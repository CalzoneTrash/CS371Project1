# =================================================================================================
# Contributing Authors:	    Jacob Alteri, Knox Garland
# Email Addresses:          jcal240@uky.edu, 
# Date:                     11/01/2023
# Purpose:                  Server Code
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================
import socket
import threading
from assets.code.helperCode import *
from typing import Dict, Tuple

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games


# Global variables

clients: Dict[Tuple[str, int], socket.socket] = {}  # Dictionary to hold client sockets

def handle_client(client_socket: socket.socket, address: Tuple[str, int]) -> None:
    global ball, leftPaddle, rightPaddle, lScore, rScore

    # Assign paddles to the players
    if not clients:
        playerPaddle = "left"
        clientPaddleObj = leftPaddle
    else:
        playerPaddle = "right"
        clientPaddleObj = rightPaddle

    clients[address] = client_socket

    # Inform the client of their paddle assignment and the screen dimensions
    client_socket.send(f"{playerPaddle},640,480".encode())

    while True:
        try:
            data = client_socket.recv(1024).decode()
        except ConnectionResetError:
            break
        
        # Extract data from client message
        paddlePos, = data.split(",")
        clientPaddleObj.rect.y = paddlePos

        # Ball Logic NEED SERVER SIDE PROCESSING 

        # BALLS LOGIC

        # Create message with the updated positions of all game objects
        message = f"{ball.rect.x},{ball.rect.y},{leftPaddle.rect.y},{rightPaddle.rect.y},{lScore},{rScore}"
        
        # Broadcast the message to all clients
        for client in clients.values():
            client.send(message.encode())

        if len(clients) < 2:
            break

    # Remove client if they disconnect
    del clients[address]
    client_socket.close()

def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 49153))  # Bind to all available IP addresses on port 5555
    server.listen(2)  # Wait for 2 players to connect

    print("[*] Server started, waiting for players...")
    
    while len(clients) < 2:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from: {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

    print("[*] Both players connected. Game started!")

if __name__ == "__main__":
    main()

