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

def print_brackets(current_group):
    if (current_group == ""):
        print("\n>>> ", end="")
    else:
        print("\n>>> ({}) ".format(current_group), end="")

def clientListen(port):

    global current_group
    global private_messages
    global acked
    global local_table

    print(">>> Client now listening\n")

    # Need to declare a new socket bc socket is already being used to send
    listen_socket = socket(AF_INET, SOCK_DGRAM)
    listen_socket.bind(('', port))

    while True:

        buffer, sender_address = listen_socket.recvfrom(4096)
        buffer = buffer.decode()
        lines = buffer.splitlines()
        header = lines[1]
        if(header == 'ack'):
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
            message = lines[3]
            print("\n>>> " + message + '\n')

        elif(header == 'nack'):
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
            message = lines[3]
            print("\n>>> " + message + '\n')
            # Previously set current_group to be value of a group that does not exist
            current_group = ""

        elif(header == 'update'):
            # update current client's table to match the server
            payload = lines[3]
            dict = json.loads(payload)
            local_table = dict
            print("\n>>> [Client table updated.]")

        elif(header == 'send'):
            original_sender_name = lines[3]
            recipient_name = lines[5]
            original_sender_ip = lines[7]
            original_sender_port = int(lines[9])
            message = lines[11]

            if(current_group != ""):    # Case: sending user is in a group chat
                # Store private messages in a list
                private_messages.append(str(original_sender_name + ": " + message))
            else:                       # Case: sending user is NOT in a group chat
                print('\n>>> ' + original_sender_name + ": " + message)

            ack = "Header:\nack\nMessage:\n[Message received by {}.]".format(recipient_name)
            listen_socket.sendto(ack.encode(), (original_sender_ip, original_sender_port))
            # print(">>> Sent the ack\n")
            

        elif(header == 'dereg'):
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1

            message = lines[3]
            print("\n>>> " + message)
            # print(">>> Closing listening socket\n")
            listen_socket.close()
            break
        elif(header == 'list_groups'):
            group_name = lines[3]
            print(">>> " + group_name)
            continue
        elif(header == 'send_group'):
            message = lines[3]
            server_ip = lines[5]
            server_port = int(lines[7])
            print(message)
            ack = "Header:\nack\nMessage:\n{}\nPort:\n{}".format(message, port)
            listen_socket.sendto(ack.encode(), (server_ip, server_port))
            # print("Sent the ack\n\n")
        elif(header == 'list_members'):
            member = lines[3]
            print(">>> " + member)
            continue
        elif(header == 'leave'):
            if(sender_address[1] in acked.keys() and acked[sender_address[1]] == 0):
                acked[sender_address[1]] = 1
            message = lines[3]
            print("\n>>> " + message + '\n')
            # Reset current_group
            current_group = ""

            # Print all private messages received while in gc
            for msg in private_messages:
                print('>>> ' + msg)

            # Reset all private messages
            private_messages = []

        print_brackets(current_group)

def clientMode(user_name, server_ip, server_port, client_port):

    # Create UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM)

    # Multithreading
    listen = threading.Thread(target=clientListen, args=(client_port,))
    listen.start()

    # Register the client
    register_msg = "header:\n" + "register\n" + "username:\n" + user_name + "\nip:\n" + '127.0.0.1\n' + "port:\n" + str(client_port)
    create_table(user_name, '127.0.0.1', client_port) # Create local table
    client_socket.sendto(register_msg.encode(), (server_ip, server_port)) # Send registration request to server

    while True:
        global acked
        global current_group

        # take in the input
        try:
            temp = input()
        except KeyboardInterrupt: # Silent leave
            to_send = "header:\n" + "dereg" + "\nport:\n" + str(client_port)
            client_socket.sendto(to_send.encode(), (server_ip, server_port))
            print(">>> deregistration request sent: silent leave\n")
            client_socket.close()
            break
        
        input_list = temp.split()

        # retrieve the header
        try:
            header = input_list[0]
        except:
            print("\n>>> Invalid input\n")
            print(local_table)
            print_brackets(current_group)
            continue
    
        if header == "send":
            if(current_group != ""):
                print(">>> Cannot send a private message while you are in a group")
                print_brackets(current_group)
                continue

            client_ip = '127.0.0.1'
            try:
                target_user_name = input_list[1]
            except:
                print("\n>>> Need to include username\n")
                print_brackets(current_group)
                continue

            target_ip = ""
            target_port = ""
            for indx in local_table:
                if local_table[indx]['name'] == target_user_name:
                    target_ip = local_table[indx]['ip']
                    target_port = str(local_table[indx]['port'])

            # Verify target user name exists
            if (target_ip == "" and target_port == ""):
                print(">>> Incorrect username provided\n")
                continue

            # Construct message
            message = ""
            for i in range(2, len(input_list)):
                message = message + input_list[i] + " "
            to_send = "header:\n" + header + "\ncurrent_user:\n" + user_name + "\nname\n" + target_user_name + "\nip\n" + str(client_ip) + "\nport:\n" + str(client_port) + "\nmessage:\n" + message

            # Set acked variable to contain recipient port
            acked = {int(target_port): 0}

            # Try once to send message to the target client
            client_socket.sendto(to_send.encode(), (target_ip, int(target_port)))
            time.sleep(.5)
            if(acked[int(target_port)] != 1):
                print(">>> [No ACK from {}, message not delivered]".format(target_user_name))
                # Tell server to update tables
                to_send = "header:\n" + "dereg" + "\nport:\n" + str(target_port)
                client_socket.sendto(to_send.encode(), (server_ip, server_port))

            continue

        elif header == "dereg":   # notified leave
            # Verify target user name exists

            user_name = ""

            try:
                target_user_name = input_list[1]
            except:
                print("\n>>> Invalid input: need to include username to dereg\n")
                print_brackets(current_group)
                continue

            target_ip = ""
            target_port = ""
            for indx in local_table:
                if int(local_table[indx]['port']) == int(client_port):
                    user_name = local_table[indx]['name']
                if local_table[indx]['name'] == target_user_name:
                    target_ip = local_table[indx]['ip']
                    target_port = str(local_table[indx]['port'])

            if (target_ip == "" and target_port == ""):
                print(">>> Incorrect username provided\n")
                print_brackets(current_group)
                continue

            # Deregestering a different user
            if(user_name != target_user_name):
                to_send = "header:\n" + header + "\nport:\n" + str(target_port)
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                continue

            acked = {int(server_port): 0}
            to_send = "header:\n" + header + "\nport:\n" + str(target_port)

            # Try 5 times to ask the server to dereg
            for i in range(6):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> deregistration request sent: notified leave")
                time.sleep(.5)
                if(acked[int(server_port)] == 1):
                    break
                if(i <= 3 and acked[int(server_port)] != 1):
                    print(">>> THE SERVER DID NOT RECEIVE DEREG REQUEST. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    exit()
                    listen.join()
                break
            
            # print("Closing client socket\n")
            client_socket.close()

            break

        elif header == "create_group":
            if(current_group != ""):
                print(">>> Cannot create a new group while you are in a group\n")
                print_brackets(current_group)
                continue

            try:
                group_name = input_list[1]
            except:
                print(">> Invalid input: need to include group name to be created\n")
                print_brackets(current_group)
                continue
            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ngroup_name:\n" + group_name + "\ncurrent_user:\n" + user_name

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to create group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to create group sent")
                time.sleep(.5)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print(">>> THE SERVER DID NOT RECEIVE CREATE GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break

            continue

        elif header == "list_groups":
            
            if(current_group != ""):
                print("Cannot list groups while you are in a group")
                print_brackets(current_group)
                continue

            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name
            
            acked = {int(server_port): 0}

            # Try 5 times to ask the server to list groups
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to list all groups sent")
                time.sleep(.5)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print(">>> THE SERVER DID NOT RECEIVE LIST GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break


        elif header == 'join_group':
            if(current_group != ""):
                print(">>> Cannot join another group while you are in a group\n")
                print_brackets(current_group)
                continue

            try:
                group_name = input_list[1]
            except:
                print(">>> Invalid input: need to include group name to join\n")
                print_brackets(current_group)
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
                if(i <= 3 and acked[int(server_port)] != 1):
                    print(">>> THE SERVER DID NOT RECEIVE JOIN GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break

            continue

        elif header == 'send_group':
            if(current_group == ""):
                print(">>> You are not in a group chat\n")
                print_brackets(current_group)
                continue

            message = ""
            for i in range(1, len(input_list)):
                message = message + input_list[i] + " "
            to_send = "header:\n" + header + "\nsender:\n" + user_name + "\nport:\n" + str(client_port) + "\nmessage:\n" + message + "\nserver_ip\n" + server_ip + "\nserver_port\n" + str(server_port) + "\ngroup_name\n" + current_group
            
            # Set acked variable to contain serveer port
            acked = {int(server_port): 0}

            # Try 5 times to ask the server to send message to the group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, int(server_port)))
                time.sleep(.5)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print(">>> [Message not delivered to server]")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break
            continue
 
        elif header == 'list_members':
            if(current_group == ""):
                print(">>> You are not in a group chat so you cannot see its members\n")
                print_brackets(current_group)
                continue

            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name + '\ngroup_name:\n' + current_group

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to list members of the group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to list members in group sent")
                time.sleep(.5)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE LIST MEMBERS IN GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break

        elif header == "leave_group":
            if(current_group == ""):
                print("You are not in a group chat so you cannot leave one\n")
                print_brackets(current_group)
                continue

            to_send = "header:\n" + header + "\nport:\n" + str(client_port) + "\ncurrent_user:\n" + user_name + '\ngroup_name:\n' + current_group

            acked = {int(server_port): 0}

            # Try 5 times to ask the server to leave group
            for i in range(5):
                print("\nTry {})".format(i+1))
                client_socket.sendto(to_send.encode(), (server_ip, server_port))
                print(">>> request to leave group sent")
                time.sleep(.5)
                if(i <= 3 and acked[int(server_port)] != 1):
                    print("THE SERVER DID NOT RECEIVE LEAVE GROUP REQ. SENDING AGAIN")
                    continue
                if(i == 4 and acked[int(server_port)] != 1):
                    # Forced exit
                    print(">>> [Server not responding]")
                    print(">>> [Exiting]")
                    # print(">>> Closing client socket\n")
                    client_socket.close()
                    listen.join()
                break
            continue

        else:
            print(">>> Please input a valid request\n")

        print_brackets(current_group)
