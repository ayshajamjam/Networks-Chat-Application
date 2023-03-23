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

acked = {}

def create_table(user_name, target_addr, target_port):
    local_table[len(local_table)] = {'name': user_name, 'ip': target_addr, 'port': target_port, 'status': 'yes'}

def clientListen(port):

    global current_group
    global private_messages
    global acked

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
            print(acked)
            print(sender_address[1])
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
                print(acked)
            message = lines[3]
            print("ack recieved " + ">>> " + message)
        elif(header == 'nack'):
            print(acked)
            print(sender_address[1])
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
                print(acked)
            message = lines[3]
            print("ack recieved")
            print(">>> " + message)
            # Previously set current_group to be value of a group that does not exist
            current_group = ""
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
            print(">>> Sent the ack\n\n")
        elif(header == 'dereg'):
            print(acked)
            print(sender_address[1])
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
                print(acked)

            message = lines[3]
            print("ack recieved " + ">>> " + message)
            print("Closing listening socket")
            print(listen_socket.fileno())
            listen_socket.close()
            print(listen_socket.fileno())
            break
        elif(header == 'list_groups'):
            group_name = lines[3]
            print(">>> " + group_name)
        elif(header == 'send_group'):
            message = lines[3]
            server_ip = lines[5]
            server_port = int(lines[7])
            print(message)
            ack = "Header:\nack\nMessage:\n{}".format(message)
            listen_socket.sendto(ack.encode(), (server_ip, server_port))
            print(">>>Sent the ack\n\n")
        elif(header == 'list_members'):
            member = lines[3]
            print(">>> " + member)
        elif(header == 'leave'):
            print(acked)
            print(sender_address[1])
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
                print(acked)
            message = lines[3]
            print("ack recieved " + ">>> " + message)

            # Reset current_group
            current_group = ""

            # Print all private messages received while in gc
            for msg in private_messages:
                print(msg)

            # Reset all private messages
            private_messages = []

def five_time_send_server_req(client_socket, listen, server_ip, server_port):
    acked = {int(server_port): 0}

    # Try 5 times to ask the server to leave group
    for i in range(5):
        print("\nTry {})".format(i+1))
        client_socket.sendto(to_send.encode(), (server_ip, server_port))
        print(">>> request to join leave sent")
        time.sleep(.5)
        print("WOKE UP")
        print(acked)
        if(i <= 3 and acked[int(server_port)] != 1):
            print("THE SERVER DID NOT RECEIVE LEAVE GROUP REQ. SENDING AGAIN")
            continue
        if(i == 4):
            # Forced exit
            print(">>> [Server not responding]")
            print(">>> [Exiting]")
            print("Closing client socket")
            print(client_socket.fileno())
            client_socket.close()
            print(client_socket.fileno())
            listen.join()  # TODO: How to close client listening socket?
        break

def clientMode(user_name, server_ip, server_port, client_port):

    # Create UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)

    # Register the client
    register_msg = "header:\n" + "register\n" + "username:\n" + user_name + "\nip:\n" + '127.0.0.1\n' + "port:\n" + str(client_port)
    create_table(user_name, '127.0.0.1', client_port) # Create local table
    client_socket.sendto(register_msg.encode(), (server_ip, server_port)) # Send registration request to server

    # TODO (optional?): only continue if ack from registering is received

    # Multithreading
    listen = threading.Thread(target=clientListen, args=(client_port,))
    listen.start()

    while True:
        global acked
        print("LOCAL TABLE")
        print(local_table)   # Show updated local table
        global current_group
        print("CURRENT_GROUP: " + current_group)
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
            print(client_socket.fileno())
            client_socket.close()
            # sys.exit(0) # Client can no longer type inputs
            print(client_socket.fileno())
            break
        
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

            # Set acked variable to contain recipient port
            acked = {int(target_port): 0}

            # Send message to target client
            client_socket.sendto(to_send.encode(), (target_ip, int(target_port)))
            time.sleep(.5)
            print("WOKE UP")
            print(acked)
            if(acked[int(target_port)] != 1):
                print(">>> [No ACK from {}, message not delivered]".format(target_user_name))
                print("THE CLIENT DID NOT RECEIVE THE MESSAGE. IT IS OFFLINE")
                # Tell server to update tables
                to_send = "header:\n" + "dereg" + "\nport:\n" + str(target_port)
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
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

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to dereg
            for i in range(6):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> deregistration request sent: notified leave")
                time.sleep(.5)
                print("WOKE UP")
                print(acked)
                if(acked[int(server_port)] == 1):
                    break
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE DEREG REQUEST. SENDING AGAIN")
                    continue
                if(i == 4):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # TODO: How to close client listening socket?
                    listen.join()  # TODO: How to close client listening socket?
                break
            
            print("Closing client socket")
            print(client_socket.fileno())
            client_socket.close()
            print(client_socket.fileno())
            
            break

        elif header == "create_group" and current_group == "":
            try:
                group_name = input_list[1]
            except:
                print("\n>>> Invalid input: need to include group name to be created")
                continue
            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ngroup_name:\n" + group_name + "\ncurrent_user:\n" + user_name

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to create group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to create group sent")
                time.sleep(.5)
                print("WOKE UP")
                print(acked)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE CREATE GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    print("Closing client socket")
                    print(client_socket.fileno())
                    client_socket.close()
                    print(client_socket.fileno())
                    listen.join()  # TODO: How to close client listening socket?
                break

        elif header == "list_groups" and current_group == "":
            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name
            
            acked = {int(server_port): 0}

            # Try 5 times to ask the server to list groups
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to list all groups sent")
                time.sleep(.5)
                print("WOKE UP")
                print(acked)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE LIST GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    print("Closing client socket")
                    print(client_socket.fileno())
                    client_socket.close()
                    print(client_socket.fileno())
                    listen.join()  # TODO: How to close client listening socket?
                break


        elif header == 'join_group' and current_group == "":
            try:
                group_name = input_list[1]
            except:
                print("\n>>> Invalid input: need to include group name to join")
                continue
            
            current_group = group_name

            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ngroup_name:\n" + group_name + "\ncurrent_user:\n" + user_name
            
            acked = {int(server_port): 0}

            # Try 5 times to ask the server to join group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to join group sent")
                time.sleep(.5)
                print("WOKE UP")
                print(acked)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE JOIN GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    print("Closing client socket")
                    print(client_socket.fileno())
                    client_socket.close()
                    print(client_socket.fileno())
                    listen.join()  # TODO: How to close client listening socket?
                break

        elif header == 'send_group' and current_group != "":
            message = ""
            for i in range(1, len(input_list)):
                message = message + input_list[i] + " "
            to_send = "header:\n" + header + "\nsender:\n" + user_name + "\nport:\n" + str(client_port) + "\nmessage:\n" + message + "\nserver_ip\n" + server_ip + "\nserver_port\n" + str(server_port) + "\ngroup_name\n" + current_group
            client_socket.sendto(to_send.encode(), (server_ip, server_port))        
        elif header == 'list_members' and current_group != "":
            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name + '\ngroup_name:\n' + current_group

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to list members of the group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to list members in group sent")
                time.sleep(.5)
                print("WOKE UP")
                print(acked)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE LIST MEMBERS IN GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    print("Closing client socket")
                    print(client_socket.fileno())
                    client_socket.close()
                    print(client_socket.fileno())
                    listen.join()  # TODO: How to close client listening socket?
                break

        elif header == "leave_group" and current_group != "":
            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name + '\ngroup_name:\n' + current_group
            five_time_send_server_req(client_socket, listen, server_ip, server_port)

        else:
            print("Please input a valid request")