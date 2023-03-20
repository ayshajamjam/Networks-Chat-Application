import socket
from socket import *
import threading
import sys
import ipaddress
import json

global server_table
server_table = {}

group_list = {}

# Server response when there is a new registering client (ACK + updated table)
def serverRegister(server_socket, target_addr, target_port):
    # Tell each client to update their local client tables
    update = "Header:\nupdate\nPayload:\n" + json.dumps(server_table)  # Convert dataframe to JSON
    for indx in server_table.keys():
        server_socket.sendto(update.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))  # Send updated table
    print(">>>Broadcasted the updated table\n\n")

    # Send ack to current client that their registration req was received
    ack = "Header:\nack\nMessage:\n[Welcome, You are registered.]"
    server_socket.sendto(ack.encode(), (target_addr, target_port))  # Send ack
    print(">>>Sent the ack")

def serverDeregister(server_socket, target_addr, target_port):
    # Update the deregistering client's status to no
    for indx in server_table.keys():
        if (str(server_table[indx]['ip'] == target_addr) and int(server_table[indx]['port'] == target_port)):
            server_table[indx]['status'] = 'no'

    # Tell each client to update their local client tables
    update = "Header:\nupdate\nPayload:\n" + json.dumps(server_table)  # Convert dataframe to JSON
    for indx in server_table.keys():
        server_socket.sendto(update.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))  # Send updated table
    print(">>>Broadcasted the updated table\n\n")

    ack = "Header:\nack\nMessage:\n[You are Offline. Bye.]"
    server_socket.sendto(ack.encode(), (target_addr, target_port))  # Send ack
    print(">>>Sent the ack")

# Server response (ACK only)
def serverCheckGroup(server_socket, target_addr, target_port, group_name, client_name):
    if(group_name not in group_list.keys()):
        group_list[group_name] = []
        print(">>> [Client {} created group {} successfully]".format(client_name, group_name))
        ack = "Header:\nack\nMessage:\n[Group {} created by Server.]".format(group_name)
    else:
        print(">>> [Client {} creating group {} failed, group already exists]".format(client_name, group_name))
        ack = "Header:\nack\nMessage:\n[Group {} already exists.]".format(group_name)
    server_socket.sendto(ack.encode(), (target_addr, int(target_port)))
    print(">>>Sent the ack\n\n")

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
    # server_table = {}

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
            server_send = threading.Thread(target=serverRegister, args=(server_socket, client_address[0], client_port))
            server_send.start()
            print(">>> [Server table updated via new registration.]")
        elif header == 'dereg':
            client_port = int(lines[3])
            # Multithreading
            server_send = threading.Thread(target=serverDeregister, args=(server_socket, client_address[0], client_port))
            server_send.start()
            print(">>> [Server table updated via deregistration.]")
        elif header == 'create_group':
            client_port = lines[3]
            group_name = lines[5]
            user_name = lines[7]
            # Multithreading
            server_send = threading.Thread(target=serverCheckGroup, args=(server_socket, client_address[0], client_port, group_name, user_name))
            server_send.start()
        else:
            print("Please input a valid request to the server")