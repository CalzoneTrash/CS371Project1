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

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Global variables
server_sync: int = 0
clients_ready: Dict[Tuple[str, int], bool] = {}
sync_values: Dict[str, int] = {} # dict to hold current sync value for each client
requests: Dict[str, int] = {} #dict to hold request types
clients_lock = threading.Lock()
sync_lock = threading.Lock()

def handle_client(client_socket: socket.socket, address: Tuple[str, int], paddle: str) -> None:
    global sync_values, clients_ready, requests, server_sync
    
    while True:
        request_json = client_socket.recv(1024).decode('utf-8')
        request = json.loads(request_json)

        # if clients request is to start the game
        if request['req'] == 'start':
            with clients_lock:
                clients_ready[paddle] = True
                if len(clients_ready) == 2:
                    if clients_ready["left"] == True and clients_ready["right"] == True:
                        ret: Dict[str, bool] = {'return': True}
                        client_socket.send(json.dumps(ret).encode('utf-8'))
                    else:
                        ret: Dict[str, bool] = {'return': False}
                        client_socket.send(json.dumps(ret).encode('utf-8'))
                else:
                    ret: Dict[str, bool] = {'return': False}
                    client_socket.send(json.dumps(ret).encode('utf-8'))
                
        # if clients request is send data to server 
        elif request['req'] == 'send':
            # get data transmitted
            data_json = request['data']

            # Extract data from JSON if client sync is greater than servers
            
            with sync_lock:
                if data_json['sync'] > server_sync:   
                    server_sync = data_json['sync']
                    server_lScore = data_json['lScore']
                    server_rScore = data_json['rScore']
                    server_currPaddle = data_json['playerPaddle_y']
                    server_ball_x = data_json['ball']['x']
                    server_ball_y = data_json['ball']['y']

        # if clients request is for server to give server data back               
        elif request['req'] == 'give':
            response = {
                        "ball": {
                            "x": server_ball_x,
                            "y": server_ball_y
                        },
                        "playerPaddle_y": server_currPaddle,
                        "lScore": server_lScore,
                        "rScore": server_rScore,
                        "sync": server_sync
                    }
            client_socket.send(json.dumps(response).encode('utf-8'))
            



def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 49153))  # Bind to all available IP addresses on port 
    server.listen(2)  # Wait for 2 players to connect

    print("[*] Server started, waiting for players...")
    
    client_socket1, addr1 = server.accept()
    print(f"[*] Accepted connection from: {addr1}")

    client_socket2, addr2 = server.accept()
    print(f"[*] Accepted connection from: {addr2}")

    
    try:
        client_handler1 = threading.Thread(target=handle_client, args=(client_socket1, addr1, "left"))
        client_handler2 = threading.Thread(target=handle_client, args=(client_socket2, addr2, "right"))
        client_handler1.start()
        client_handler2.start()
        print("[*] Both players connected. Game started!")
    except Exception as e:
        print(f"An error has occured {e}")

if __name__ == "__main__":
    main()

