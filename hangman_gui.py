from tkinter import *
from threading import Thread  # Import Thread for handling concurrent tasks
from socket import *  # Import socket module for networking
import time  # Import time module for handling time-related operations
import ssl  # Import SSL module for secure communication
import argparse  # Import argparse module for parsing command-line arguments

class HangmanClientGUI:
    def __init__(self, master):
        # Initialize the GUI window
        self.master = master
        master.title("Hangman Client")

        # Create and place GUI elements (labels, entry fields, buttons, text widget)
        self.server_label = Label(master, text="Server Address:")
        self.server_label.grid(row=0, column=0, sticky=W)

        self.server_entry = Entry(master)
        self.server_entry.grid(row=0, column=1)

        self.port_label = Label(master, text="Server Port:")
        self.port_label.grid(row=1, column=0, sticky=W)

        self.port_entry = Entry(master)
        self.port_entry.grid(row=1, column=1)

        self.username_label = Label(master, text="Username:")
        self.username_label.grid(row=2, column=0, sticky=W)

        self.username_entry = Entry(master)
        self.username_entry.grid(row=2, column=1)

        self.password_label = Label(master, text="Password:")
        self.password_label.grid(row=3, column=0, sticky=W)

        self.password_entry = Entry(master, show="*")
        self.password_entry.grid(row=3, column=1)

        self.connect_button = Button(master, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=4, column=0, columnspan=2)

        self.play_button = Button(master, text="Play", command=self.play_game, state=DISABLED)
        self.play_button.grid(row=5, column=0, columnspan=2)

        self.output_text = Text(master, height=10, width=40)
        self.output_text.grid(row=6, column=0, columnspan=2)

        self.guess_entry = Entry(master)
        self.guess_entry.grid(row=7, column=0, columnspan=2)

        self.guess_button = Button(master, text="Submit Guess", command=self.submit_guess)
        self.guess_button.grid(row=8, column=0, columnspan=2)

        # Initialize variables for storing socket and receiving thread
        self.client_socket = None
        self.receiving_thread = None

    # Method to connect to the server
    def connect_to_server(self):
        # Retrieve server address, port, username, and password from GUI input
        server_name = self.server_entry.get()
        server_port = int(self.port_entry.get())
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Set up SSL context and create SSL socket for secure communication
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_verify_locations("server_cert.pem")
        ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        ssl_socket = ssl_context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=server_name)

        try:
            # Connect to the server
            ssl_socket.connect((server_name, server_port))
        except error as e:
            # Handle connection error
            self.output_text.insert(END, f"Error connecting to the server: {e}\n")
            return

        # Send username and password to the server
        ssl_socket.send(username.encode('utf-8'))
        time.sleep(1)
        ssl_socket.send(password.encode('utf-8'))

        # Start a new thread for receiving messages
        self.receiving_thread = Thread(target=self.receive_messages, args=(ssl_socket,))
        self.receiving_thread.start()

        # Enable the play button after successful connection
        self.play_button.config(state=NORMAL)
        self.client_socket = ssl_socket

    # Method to start the game
    def play_game(self):
        if self.client_socket:
            # Send a message to the server to start the game
            self.client_socket.send("start_game".encode('utf-8'))

    # Method to submit a guess to the server
    def submit_guess(self):
        if self.client_socket:
            # Retrieve guess from the entry field and send it to the server
            guess = self.guess_entry.get()
            self.client_socket.send(guess.encode('utf-8'))

    # Method to receive messages from the server
    def receive_messages(self, ssl_socket):
        while True:
            try:
                # Receive messages from the server
                received = ssl_socket.recv(1024).decode('utf-8')
                if not received:
                    break
                # Display received messages in the output text widget
                self.output_text.insert(END, received + "\n")
                self.output_text.see(END)  # Scroll to the end of the text widget
            except Exception as e:
                # Handle receive error
                print(f"Error during receive_messages: {e}")
                break

# Main function
if __name__ == "__main__":
    # Create and initialize the Tkinter root window
    root = Tk()
    hangman_client_gui = HangmanClientGUI(root)
    root.mainloop()  # Enter the Tkinter event loop
