from socket import *
import threading
import time
import random
import ssl

class ThreadedSSLServer:
    # Class variables to manage game state and client information
    client_ips = []  # List to store client IP addresses
    client_sockets = []  # List to store client socket objects
    falseGuesses = 0  # Count of false guesses
    playerCount = 0  # Total number of players
    usernames = []  # List to store usernames
    registeredUsers = {}  # Dictionary to store registered usernames and passwords
    IpUsernamePairs = {}  # Dictionary to map IP addresses to usernames
    wordList = []  # List to store words for the game
    game_state = []  # List to represent the current state of the game
    gameWaiting = True  # Flag indicating if the game is waiting for players
    gameRunning = False  # Flag indicating if the game is currently running
    gameEnded = False  # Flag indicating if the game has ended
    allRunsEnded = False  # Flag indicating if all game runs have ended
    addedUsers = 0  # Counter to track the number of added users
    running = True  # Flag to control the main loop of the server

    # Method to receive guesses from clients
    def getGuessFromClient(self, client, word, wordGuesses, letterGuesses):
        stateChanged = False  # Flag to track if the game state has changed
        guess = client.recv(1024)  # Receive guess from client
        guess = guess.decode('utf-8')  # Decode guess from bytes to string
        guess = guess.lower()  # Convert guess to lowercase

        # Check if the guess matches the word
        if word == guess:
            self.gameEnded = True  # Set gameEnded flag to True
        else:
            # Process the guess (whether a word or a letter)
            if len(guess) > 1:  # If guess is a word
                self.falseGuesses += 1  # Increment false guess count
                wordGuesses.append(guess)  # Add guess to wordGuesses list
            else:  # If guess is a letter
                letterGuesses.append(guess)  # Add guess to letterGuesses list
                # Update game state based on the guess
                for i in range(len(word)):
                    if guess == word[i]:
                        stateChanged = True
                        self.game_state[i] = guess
                if not stateChanged:
                    self.falseGuesses += 1  # Increment false guess count

        # Check game ending conditions
        if "".join(self.game_state) == word:  # If word is guessed correctly
            self.gameEnded = True
        if self.falseGuesses == 7:  # If maximum false guesses reached
            self.gameEnded = True

        return guess  # Return the guess

    # Method to run the game logic
    def run_game(self, server_socket, client_socket):
        word = random.choice(self.wordList)  # Choose a random word from wordList
        for i in word:
            self.game_state.append('_')  # Initialize game state with underscores for each letter

        # Prepare initial game state message
        printStr = ""
        for i in self.game_state:
            printStr += i
            printStr += " "
        wordGuesses = []  # List to store word guesses
        letterGuesses = []  # List to store letter guesses
        welcome_message = "Hangman game is starting\n"

        print(welcome_message)
        client_socket.send((welcome_message + "Word is\n" + printStr + "\n").encode("utf-8"))

        # Main game loop
        while not self.gameEnded:
            ip = self.client_ips[self.client_sockets.index(client_socket)]
            printStr = self.IpUsernamePairs[ip] + " will be playing next\n"
            for turn_info in self.client_sockets:
                turn_info.send(printStr.encode('utf-8'))
            time.sleep(1)

            client_socket.send('Your turn\n'.encode('utf-8'))

            last_guess = self.getGuessFromClient(client_socket, word, wordGuesses, letterGuesses)  # Get guess from client
            game_state_update = "Letter guesses: " + ' ,'.join(letterGuesses) + "\n"
            game_state_update += "Word Guesses: " + " ,".join(wordGuesses) + "\n"
            print_string = ""
            for c in self.game_state:
                print_string += c + " "
            # Update game state and send updates to all clients
            for all_clients in self.client_sockets:
                all_clients.send(game_state_update.encode("utf-8"))
                all_clients.send(("Last guessed: " + last_guess + "\n").encode("utf-8"))
                print_string = " ".join(self.game_state)
                all_clients.send(("Word\n" + print_string + "\n").encode("utf-8"))
        client_socket.send("Game ended\n".encode("utf-8"))
        self.gameRunning = False
        # Inform players about game outcome
        if self.falseGuesses < 7:
            for all_clients in self.client_sockets:
                all_clients.send(("Game is won\n").encode('utf-8'))
                time.sleep(0.5)
        else:
            for all_clients in self.client_sockets:
                all_clients.send(("Game lost\n").encode('utf-8'))
                time.sleep(0.5)

    # Method to listen for new client connections
    def listenToNewClient(self, client, addr):
        allowed = True
        # Receive username from client
        username = client.recv(1024)
        username = username.decode('utf-8')
        print(username)
        time.sleep(1)
        # Receive password from client
        password = client.recv(1024)
        password = password.decode('utf-8')
        print(password)
        # Check if the username is already registered
        if username in self.usernames:
            if password == self.registeredUsers[username]:
                self.client_ips.append(addr)
                self.client_sockets.append(client)
                self.IpUsernamePairs[addr] = username
            else:
                allowed = False
        else:
            # Register new user
            self.usernames.append(username)
            self.registeredUsers[username] = password
            self.client_ips.append(addr)
            self.client_sockets.append(client)
            self.IpUsernamePairs[addr] = username
            with open("savedUsers.txt", "a+") as myFile:
                myFile.write(username + ' ' + password + '\n')
        # Inform client whether they are allowed to join
        if allowed:
            client.send("You joined the game\n".encode("utf-8"))
            self.addedUsers = self.addedUsers + 1

        if not allowed:
            client.close()
            exit(0)

        if self.addedUsers == self.playerCount:
            self.gameWaiting = False
            self.gameRunning = True
            self.run_game(client, client)  # Start the game

    # Method to handle waiting for players to join
    def game_waiting(self, server_socket):
        while self.gameWaiting and self.running:
            if self.playerCount == self.addedUsers:
                self.gameWaiting = False
                self.gameRunning = True
                self.run_game(server_socket, self.client_sockets[0])  # Start the game. Do not ever change this line
                break
            connection_socket, addr = server_socket.accept()
            if addr in self.client_ips:
                index = self.client_ips.index(addr)
                self.client_sockets[index].send("Wait for the game to start\n".encode('utf-8'))
            elif self.addedUsers < self.playerCount:
                self.listenToNewClient(connection_socket, addr)
            else:
                print("Access to ", addr, "is unallowed, max num reached")
                connection_socket.send("Max number of players reached. You are not allowed to join\n".encode('utf-8'))
                connection_socket.close()

            # Check for "start_game" message from client
            for client_socket in self.client_sockets:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if message == "start_game":
                        print("Starting the game...")
                        self.run_game(server_socket, client_socket)
                except:
                    pass

    # Method to start the server
    def start_server(self, server_socket):
        server_socket.listen(45)  # Listen for incoming connections
        while self.running:
            connection_socket, addr = server_socket.accept()

            # Start a new thread to handle the game waiting logic
            threading.Thread(target=self.game_waiting, args=(server_socket,)).start()

        server_socket.close()  # Close the server socket

    # Constructor
    def __init__(self, server_port, player_count):
        # Load words from file
        with open("words.txt") as myFile:
            line = myFile.readline()
            wordlist = line.split()
            print(" ", len(wordlist), "words loaded")
            self.wordList = wordlist  # Load words from a txt file

        self.playerCount = player_count
        self.running = True
        self.falseGuesses = 0
        self.game_state = []

        # Create an SSL context and load certificates
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_cert_chain(certfile="server_cert.pem", keyfile="server_key.pem")

        # Create a server socket
        server_socket = ssl_context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=True)
        print("SSL Socket is created...")

        # Bind the server socket to the specified address and port
        server_socket.bind(('localhost', server_port))
        print("Binding is done...")
        print("The server is ready to receive")

        # Start the server
        self.start_server(server_socket)


if __name__ == "__main__":
    serverPort = 12000
    playerCount = int(input("How many players will be playing Hangman?\n"))

    ThreadedSSLServer(serverPort, playerCount)
