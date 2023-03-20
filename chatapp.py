import socket
from socket import *
import threading
import sys
import ipaddress
import json
from checks import *
from server import *
from client import *

if __name__ == "__main__":
    
    mode = sys.argv[1] # Extract mode from args

    if mode == '-s': # Server mode
        s_port = int(sys.argv[2])
        if (checkPort(s_port)):
            serverMode(s_port)
    elif mode == '-c': # Client mode
        user_name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        client_port = int(sys.argv[5])
        if(checkPort(server_port) and checkPort(client_port) and checkIP(server_ip)):
            clientMode(user_name, server_ip, server_port, client_port)