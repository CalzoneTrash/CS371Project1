# =================================================================================================
# Contributing Authors:	    Jacob Alteri, Knox Garland
# Email Addresses:          jcal240@uky.edu, 
# Date:                     11/01/2023
# Purpose:                  Server Code
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================
import json
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
sync_values: Dict[Tuple[str, int], int] = {}

def handle_client(client_socket: socket.socket, address: Tuple[str, int]) -> None:
    global client_data, sync_values
    clients[address] = client_socket

    while True:
        try:
            data = client_socket.recv(1024).decode()
            data_json = json.loads(data)
        except ConnectionResetError:
            break
        except json.JSONDecodeError:
            print("Invalid JSON received")
            continue
        
        # Extract data from JSON
        ball_x = data_json['ball']['x']
        ball_y = data_json['ball']['y']
        leftPaddle_y = data_json['leftPaddle']
        rightPaddle_y = data_json['rightPaddle']
        lScore = data_json['lScore']
        rScore = data_json['rScore']
        sync = data_json['sync']

        # Store sync value
        client_data[address] = data_json
        sync_values[address] = data_json['sync']

        # Check if we have sync values from both clients
        if len(sync_values) == 2:
            # Find the client with the highest sync value
            highest_sync_client = max(sync_values, key=sync_values.get)

            # If the highest sync is from the current client, broadcast its message
            if highest_sync_client == address:
                message = json.dumps(client_data[address])
                for client in clients.values():
                    client.send(message.encode('utf-8'))
                
                # Clear the sync value for this client
                sync_values.pop(address, None)

        # Broadcast the message to all clients
        message = json.dumps({
            "ball": {"x": ball_x, "y": ball_y},
            "leftPaddle": leftPaddle_y,
            "rightPaddle": rightPaddle_y,
            "lScore": lScore,
            "rScore": rScore
        })

        for client in clients.values():
            client.send(message.encode('utf-8'))

        if len(clients) < 2:
            break

    # Remove client if they disconnect
    del clients[address]
    del client_data[address]
    sync_values.pop(address, None)
    client_socket.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 49153))  # Bind to all available IP addresses on port 5555
    server.listen(2)  # Wait for 2 players to connect

    print("[*] Server started, waiting for players...")
    
    client_socket1, addr1 = server.accept()
    print(f"[*] Accepted connection from: {addr1}")

    client_socket2, addr2 = server.accept()
    print(f"[*] Accepted connection from: {addr2}")
    try:
        client_handler1 = threading.Thread(target=handle_client, args=(client_socket1, addr1))
        client_handler2 = threading.Thread(target=handle_client, args=(client_socket2, addr2))
        client_handler1.start()
        client_handler2.start()
        print("[*] Both players connected. Game started!")
    except Exception as e:
        print(f"An error has occured {e}")

if __name__ == "__main__":
    main()

