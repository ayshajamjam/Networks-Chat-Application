import socket
from socket import *
import threading
import sys
import ipaddress
import json

global server_table
server_table = {}

global group_list
group_list = {}

# Server response when there is a new registering client (ACK + updated table)
def serverRegister(server_socket, target_addr, target_port):
    # Tell each client to update their local client tables
    update = "Header:\nupdate\nPayload:\n" + json.dumps(server_table)  # Convert dataframe to JSON
    for indx in server_table.keys():
        server_socket.sendto(update.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))  # Send updated table
    print(">>>Broadcasted the updated table\n")

    # Send ack to current client that their registration req was received
    ack = "Header:\nack\nMessage:\n[Welcome, You are registered.]"
    server_socket.sendto(ack.encode(), (target_addr, target_port))  # Send ack
    print(">>> Sent the ack\n\n")

def serverDeregister(server_socket, target_addr, target_port):
    # Update the deregistering client's status to no
    for indx in server_table.keys():
        if (server_table[indx]['ip'] == str(target_addr) and server_table[indx]['port'] == int(target_port)):
            server_table[indx]['status'] = 'no'

    # Tell each client to update their local client tables
    update = "Header:\nupdate\nPayload:\n" + json.dumps(server_table)  # Convert dataframe to JSON
    for indx in server_table.keys():
        server_socket.sendto(update.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))  # Send updated table
    print(">>>Broadcasted the updated table\n")

    ack = "Header:\ndereg\nMessage:\n[You are Offline. Bye.]"
    server_socket.sendto(ack.encode(), (target_addr, target_port))  # Send ack
    print(">>> Sent the ack\n\n")

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
    print(">>> Sent the ack\n\n")

def serverListGroups(server_socket, target_addr, target_port, client_name):
    print(">>> [Client {} requested listing groups, current groups:]".format(client_name))
    ack = "Header:\nack\nMessage:\n[Available group chats:]"
    server_socket.sendto(ack.encode(), (target_addr, int(target_port)))
    for group in group_list.keys():
        print(">>> " + group)
        li = "Header:\nlist_groups\nMessage:\n{}".format(group)
        server_socket.sendto(li.encode(), (target_addr, int(target_port)))

    print(">>> Sent the ack\n\n")

def serverJoinGroup(server_socket, target_addr, target_port, group_name, client_name):
    
    if(group_name in group_list.keys()):
        # Add to group
        group_list[group_name].append(client_name)

        # Update the client's mode to group name
        for indx in server_table.keys():
            if (server_table[indx]['ip'] == str(target_addr) and server_table[indx]['port'] == int(target_port)):
                print("HELLOOO")
                server_table[indx]['mode'] = group_name

        print(">>> [Client {} joined group {}]".format(client_name, group_name))
        ack = "Header:\nack\nMessage:\n[Entered group {} successfully.]".format(group_name)
    else:
        print(">>> [Client {} joining group {} failed, group does not exist]".format(client_name, group_name))
        ack = "Header:\nnack\nMessage:\n[Group {} does not exist.]".format(group_name)
    
    server_socket.sendto(ack.encode(), (target_addr, int(target_port)))
    print(">>> Sent the ack\n\n")

def serverBroadcast(server_socket, sender_addr, sender_port, sender_name, group_name, message, server_ip, server_port):
    print(">>> [Client {} sent group message: {}]".format(sender_name, message))

    # send ack to original sender
    ack = "Header:\nack\nMessage:\n[Message received by Server.]"
    server_socket.sendto(ack.encode(), (sender_addr, int(sender_port)))
    print(">>> Sent the ack\n\n")

    # Construct message to be sent to each user
    msg = "Group_Message <" + sender_name + ">: " + message
    full_msg = "Header:\nsend_group\nMessage:\n" + msg + "\nServer_ip:\n" + server_ip + "\nServer_port:\n" + server_port

    # Send message those in the group except the client that originally sent the message
    for indx in server_table.keys():
        print(str(server_table[indx]['ip']), int(server_table[indx]['port']), str(server_table[indx]['name']))
        if(not ((str(server_table[indx]['ip']) == str(sender_addr)) and (int(server_table[indx]['port']) == int(sender_port))) and str(server_table[indx]['name']) in clients_in_group):
            server_socket.sendto(full_msg.encode(), (str(server_table[indx]['ip']), int(server_table[indx]['port'])))


def serverListMembers(server_socket, target_addr, target_port, client_name, group_name):
    print(">>> [Client {} requested listing members of group {}:]".format(client_name, group_name))
    ack = "Header:\nack\nMessage:\n[Members in the group {}:]".format(group_name)
    server_socket.sendto(ack.encode(), (target_addr, int(target_port)))
    for client in group_list[group_name]:
        print(">>> {}".format(client))
        li = "Header:\nlist_members\nMessage:\n({}) {}".format(group_name, client)
        server_socket.sendto(li.encode(), (target_addr, int(target_port)))
    print(">>> Sent the ack\n\n")

def serverLeaveGroup(server_socket, target_addr, target_port, client_name, group_name):
    print(">>> [Client {} left group {}]".format(client_name, group_name))
    ack = "Header:\nleave\nMessage:\n[Leave group chat {}.]".format(group_name)
    server_socket.sendto(ack.encode(), (target_addr, int(target_port)))

    # Update group members in group: remove client
    group_list[group_name].remove(client_name)

    # Update the client's mode to normal
    for indx in server_table.keys():
        if (server_table[indx]['ip'] == str(target_addr) and server_table[indx]['port'] == int(target_port)):
            server_table[indx]['mode'] = 'normal'

    print(">>> Sent the ack\n\n")
    
def serverMode(port):
    # Create UDP socket
    server_socket = socket(AF_INET, SOCK_DGRAM)
    
    # Start listening
    server_socket.bind(('localhost', port))
    print(">>> Server is online\n")

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

        # Extract header to determine what to do
        buffer = buffer.decode()
        lines = buffer.splitlines()
        header = lines[1]

        if header == 'register':
            user_name = lines[3]
            client_ip = str(lines[5])
            client_port = int(lines[7])

            # Append the newly registered client to the server's table
            server_table[len(server_table)] = {'name': user_name, 'ip': client_ip, 'port': client_port, 'status': 'yes', 'mode': 'normal'}

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
        elif header == 'list_groups':
            client_port = lines[3]
            user_name = lines[5]
            # Multithreading
            server_send = threading.Thread(target=serverListGroups, args=(server_socket, client_address[0], client_port, user_name))
            server_send.start()
        elif header == 'join_group':
            client_port = lines[3]
            group_name = lines[5]
            user_name = lines[7]
            # Multithreading
            server_send = threading.Thread(target=serverJoinGroup, args=(server_socket, client_address[0], client_port, group_name, user_name))
            server_send.start()
        elif header == 'send_group':
            sender_name = lines[3]
            sender_port = lines[5]
            message = lines[7]
            server_ip = lines[9]
            server_port = lines[11]
            group_name = lines[13]
            # Multithreading
            server_send = threading.Thread(target=serverBroadcast, args=(server_socket, client_address[0], sender_port, sender_name, group_name, message, server_ip, server_port))
            server_send.start()
        elif header == 'ack':
            message = lines[3]
            print("ack recieved")
        elif header == 'list_members':
            client_port = lines[3]
            user_name = lines[5]
            group_name = lines[7]
            # Multithreading
            server_send = threading.Thread(target=serverListMembers, args=(server_socket, client_address[0], client_port, user_name, group_name))
            server_send.start()
        elif header == 'leave_group':
            client_port = lines[3]
            user_name = lines[5]
            group_name = lines[7]
            # Multithreading
            server_send = threading.Thread(target=serverLeaveGroup, args=(server_socket, client_address[0], client_port, user_name, group_name))
            server_send.start()
        else:
            print("Please input a valid request to the server")

        print(server_table)