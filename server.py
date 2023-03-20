import socket
from socket import *
import threading
import sys
import ipaddress
import json

# Server response when there is a new registering client (ACK + updated table)
def serverRegister(server_socket, target_addr, target_port, server_table):
    # Tell each client to update their local client tables
    update = "Header:\nupdate\nPayload:\n" + json.dumps(server_table)  # Convert dataframe to JSON
    for indx in server_table.keys():
        server_socket.sendto(update.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))  # Send updated table
    print(">>>Broadcasted the updated table\n\n")

    # Send ack to current client that their registration req was received
    ack = "Header:\nack\nMessage:\n[Welcome, You are registered.]"
    server_socket.sendto(ack.encode(), (target_addr, target_port))  # Send ack
    print(">>>Sent the ack")

def serverMode(port):
    # Create UDP socket
    server_socket = socket(AF_INET, SOCK_DGRAM)
    
    # Start listening
    server_socket.bind(('localhost', port))
    print(">>>Server is online\n")

    # Server Table: initially empty
    """
    {
        0: {
            name: ayshajam
            ip: x
            port: y
            status: yes
        },
    }
    """
    server_table = {}

    while True:
        # Buffer: contains datastream
        # Client_address: tuple of (ip_addr, port)
        # Buffer size: 4096
        buffer, client_address = server_socket.recvfrom(4096)
        print("the client address is: ", client_address)

        # Extract header to determine what to do
        buffer = buffer.decode()
        lines = buffer.splitlines()
        header = lines[1]

        if header == 'register':
            user_name = lines[3]
            client_ip = str(lines[5])
            client_port = int(lines[7])

            # Append the newly registered client to the server's table
            server_table[len(server_table)] = {'name': user_name, 'ip': client_ip, 'port': client_port, 'status': 'yes'}
            print(server_table)

            # Send ack to current client and update all local clients' tables
            server_send = threading.Thread(target=serverRegister, args=(server_socket, client_address[0], client_port, server_table))
            server_send.start()
            print(">>> [Server table updated via new registration.]")
        else:
            print("Please input a valid request to the server")