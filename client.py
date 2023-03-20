import socket
from socket import *
import threading
import sys
import ipaddress
import json
import time

local_table = {}
current_group = ""
private_messages = []

def create_table(user_name, target_addr, target_port):
    local_table[len(local_table)] = {'name': user_name, 'ip': target_addr, 'port': target_port, 'status': 'yes'}

def clientListen(port):

    global current_group
    global private_messages

    print(">>>Client now listening")

    # Need to declare a new socket bc socket is already being used to send
    listen_socket = socket(AF_INET, SOCK_DGRAM)
    listen_socket.bind(('', port))

    while True:
        buffer, sender_address = listen_socket.recvfrom(4096)
        buffer = buffer.decode()
        lines = buffer.splitlines()
        header = lines[1]
        if(header == 'ack'):
            message = lines[3]
            print("ack recieved " + ">>> " + message)
        elif(header == 'update'):
            # update current client's table to match the server
            payload = lines[3]
            dict = json.loads(payload)
            global local_table
            local_table = dict
            print(">>> [Client table updated.]")
        elif(header == 'send'):
            original_sender_name = lines[3]
            recipient_name = lines[5]
            original_sender_ip = lines[7]
            original_sender_port = int(lines[9])
            message = lines[11]
            
            if(current_group != ""):    # Case: sending user is in a group chat
                # Store private messages in a list
                print("RECIEVED PRIVATE MESSAGE WHILE IN GC; exit to see")
                private_messages.append(str(original_sender_name + ": " + message))
            else:                       # Case: sending user is NOT in a group chat
                print(original_sender_name + ": " + message)

            ack = "Header:\nack\nMessage:\n[Message received by {}.]".format(recipient_name)
            listen_socket.sendto(ack.encode(), (original_sender_ip, original_sender_port))
            print(">>>Sent the ack\n\n")



def clientMode(user_name, server_ip, server_port, client_port):

    # Create UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)

    # Register the client
    register_msg = "header:\n" + "register\n" + "username:\n" + user_name + "\nip:\n" + '127.0.0.1\n' + "port:\n" + str(client_port)
    create_table(user_name, '127.0.0.1', client_port) # Create local table
    client_socket.sendto(register_msg.encode(), (server_ip, server_port)) # Send registration request to server

    # Multithreading
    listen = threading.Thread(target=clientListen, args=(client_port,))
    listen.start()

    while True:
        print("LOCAL TABLE")
        print(local_table)   # Show updated local table
        # global current_group
        # print("CURRENT_GROUP: " + current_group)
        if (current_group == ""):
            print(">>>", end="")
        else:
            print(">>> ({}) ".format(current_group), end="")
        
        try:
            temp = input()
        except KeyboardInterrupt: # Silent leave
            to_send = "header:\n" + "dereg" + "\nport:\n" + str(client_port)
            client_socket.sendto(to_send.encode(), (server_ip, server_port))
            print(">>> deregistration request sent: silent leave")
            sys.exit(0) # Client can no longer type inputs
        
        input_list = temp.split()

        try:
            header = input_list[0]
        except:
            print("\n>>>Invalid input")
            continue
    
        if header == "send":
            client_ip = '127.0.0.1'
            try:
                target_user_name = input_list[1]
            except:
                print("\n>>>Need to include username")
                continue

            target_ip = ""
            target_port = ""
            for indx in local_table:
                if local_table[indx]['name'] == target_user_name:
                    target_ip = local_table[indx]['ip']
                    target_port = str(local_table[indx]['port'])

            # Verify target user name exists
            if (target_ip == "" and target_port == ""):
                print(">>> Incorrect username provided")
                continue

            # Construct message
            message = ""
            for i in range(2, len(input_list)):
                message = message + input_list[i] + " "
            to_send = "header:\n" + header + "\ncurrent_user:\n" + user_name + "\nname\n" + target_user_name + "\nip\n" + str(client_ip) + "\nport:\n" + str(client_port) + "\nmessage:\n" + message

            # Send message to target client
            client_socket.sendto(to_send.encode(), (target_ip, int(target_port)))
            print(">>> Message sent")
        elif header == "dereg":   # notified leave
            # Verify target user name exists
            try:
                target_user_name = input_list[1]
            except:
                print("\n>>>Invalid input: need to include username to dereg")
                continue

            target_ip = ""
            target_port = ""
            for indx in local_table:
                if local_table[indx]['name'] == target_user_name:
                    target_ip = local_table[indx]['ip']
                    target_port = str(local_table[indx]['port'])

            if (target_ip == "" and target_port == ""):
                print(">>>Incorrect username provided")
                continue

            to_send = "header:\n" + header + "\nport:\n" + str(target_port)
            client_socket.sendto(to_send.encode(), (server_ip, server_port))
            print(">>> deregistration request sent: notified leave")
            sys.exit(0) # Client can no longer type inputs