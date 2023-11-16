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
sync_values: Dict[Tuple[str, int], int] = {} # dict to hold current sync value for each client
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

def handle_client(client_socket: socket.socket, address: Tuple[str, int]) -> None:
    global clients, sync_values
    clients_lock = threading.Lock()
    sync_values_lock = threading.Lock()

    # Thread Lock
    with clients_lock:
        #add client to clients dict
        clients[address] = client_socket

        #initial data send in JSON format
        if len(clients) == 1:
            initial_data = {
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT,
                "paddle": "left"
            }
        else:
            initial_data = {
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT,
                "paddle": "right"
            }

        #NOW SEND IT!
        try:
            ini_send = json.dumps(initial_data)
            client_socket.send(ini_send.encode('utf-8'))
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        # print(f"WE MADE IT TO INITIALIZE HANDLE CLIENT FOR {address} \n") #TESTING
    while len(clients) != 2:
        continue
    #########################Main While Loop#############################################################################
    while True:
        #print(f"WE MADE IT TO HANDLE CLIENT LOOP FOR {address} \n") #TESTING
        try:
            data = client_socket.recv(1024).decode('utf-8')
            data_json = json.loads(data)
            # print(f"we made it to receive data for {address} \n") #TESTING
        except ConnectionResetError:
            # print(f"Connection reset \n") # TESTING!
            break
        except json.JSONDecodeError as e:
            #print(f"Invalid JSON received: {data} - Error: {e}")
            continue
        
        # Extract data from JSON
        ball_x = data_json['ball']['x']
        ball_y = data_json['ball']['y']
        leftPaddle_y = data_json['leftPaddle_y']
        rightPaddle_y = data_json['rightPaddle_y']
        lScore = data_json['lScore']
        rScore = data_json['rScore']
        sync = data_json['sync']
        # print(f"{ball_x} @ {ball_y} @ {leftPaddle_y} @ {rightPaddle_y} @ {lScore} @ {rScore} @ {sync}") # TESTING!

        # Store sync value
        with sync_values_lock:
            sync_values[address] = data_json['sync']
            # print(f"sync value for {address} is {sync_values[address]} \n") # TESTING!
            # Check if we have sync values from both clients
            if len(sync_values) == 2:
                # Find the client with the highest sync value
                highest_sync_client = max(sync_values, key=sync_values.get)

                # If the highest sync is from the current client, broadcast its message
                if highest_sync_client == address:
                    new_message = {
                        "ball": {
                            "x": ball_x,
                            "y": ball_y
                        },
                        "leftPaddle_y": leftPaddle_y,
                        "rightPaddle_y": rightPaddle_y,
                        "lScore": lScore,
                        "rScore": rScore,
                        "sync": sync
                    }
                    json_message = json.dumps(new_message)
                    with clients_lock:
                        for client in clients.values():
                            # print(f"clients contains: {client}\n") # TESTING!
                            client.send(json_message.encode('utf-8'))
        # End loop if client disconnects
        if len(clients) < 2:
            break

    # Remove client if they disconnect
    with clients_lock:
        del clients[address]
    with sync_values_lock:
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

