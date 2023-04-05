# Networks-Chat-Application

## Demo

Visit our demo video [here](https://youtu.be/76dJnJJhY5c) <br />

## Instructions to Run

**Server**: python3 chatapp.py -s <server_port>
**Client**: python3 chatapp.py -c <user_name> <server_ip> <server_port> <client_port>

- python3 chatapp.py -s 4000
- python3 chatapp.py -c aysha localhost 4000 2000
- python3 chatapp.py -c sana localhost 4000 3000
- python3 chatapp.py -c sarah localhost 4000 5000
- python3 chatapp.py -c haider localhost 4000 7000

## Libraries

- **threading**: multithreading (sending and recieving simultaneously)
- **sys**: usedful for command-line

## Description of Project:

This chat app can host any number of clients that wish to communicate with each other. The clients can register with the server, create groups, see which groups already exist, join_groups, see which members are in the group, chat with other members in the group, and leave the group as well. If the client is in a group, it can only chat with those in the group and cannot send or receive messages to clients outside the group. If a client in a group receives a message from someone outside the group, it is notified but can only see those messages after leaving the group.

Clients are also able to communicate directly with each other without involving the server. If clients are unresponsive, the server deregisters them. Clients can leave silently (by closing the window or pressing ctrlC), or by notifying the server via a deregistration request.

### Checks.py

This file contains a few helper functions that check the validity of the IP address and port number provided by the client as input.

### Client-side Implementation:

For the client, I maintain global variables of local_table, which keeps track of all registered members, current_group, which maintains what group a client is in, private_messages, which store all the private messages a client receives while it is in a group, and acked, which is a dictionary that maintains the port number and binary digit for a client to which a message was sent. 

In clientMode, when a new client attempts to join, we create a socket and register the client with the server. We then use multithreading to create a listening thread for the client.

We then create a loop which runs until the client deregisters or quietly exits. From here, the client is able to input requests such as send, dereg, create_group, etc. Using a series of if else statements, we perform different actions depending on the type of request.

Since the client is only permitted to do certain actions while it is in a group and different ones when it is not, we perform checks on each request by checking if the value of the current_group string.

When attempting to send a message, we use the target user name to isolate its ip address and port number from the local_table. A user is able to send any length of message. When a message is sent, the user stores the target’s port number and assigns it to 0 in the dictionary ‘acked’ and goes to sleep for 500ms. If an ack is received from the target, this digit is changed to 1. If it is not equal to 1 when the sending client wakes up, then the sending client tells the server to deregister the recipient client because it is offline. This usually occurs when the client does a silent leave.

For all the other commands (dereg, create_group, list_groups, join_group, send_group, list_members, leave_group), the client maintains the same acked dictionary in which it only places the server’s port number and assigns it 0. The client attempts to contact the server 5 times after which it forces an exit by closing its client_socket and listening_socket (I was unable to close the listening socket for this case in my implementation).

The format of what a sending client sends depends on the type of request but is essentially a string with the name of the field on one line and the value on the next. These ‘to_send’ strings typically include fields such as: header, user_name, target_port, message, etc.

In clientListen, the client declares a listening socket which it uses to receive information from other clients and the server. The client responds to send request from other clients or other requests from the server. The client typically receives an ack from the server, and simply prints out the message sent by the server. For some cases such as ‘leave’, the client updates the value of current_group to an empty string and prints all the private messages it received.

### Server-side Information:

In serverMode, we create a socket after which we enter a while loop that runs until the server is forced to close. The server receives requests from various clients and the server isolates the header of the request to determine which if statement to execute. In each case, the server extracts variables such as sender_name, sender_port, message, etc. It then creates a separate thread with the appropriate target function and arguments.

The server maintains three global variables: server_table, group_list, and acked. Server_table maintains the state of each client and is printed each time a request is made to the server. Group_list is a dictionary that keeps track of all existing groups (keys), with values that are lists of members within those groups. Acked is a dictionary used when broadcasting messages to all members of a group and ensuring that each member received the message. This is the same functionality as the one in the client part.

## Important Notes:

### Silent Leave

Note that closing the SSH window will not trigger a silent leave. Please use ctrl + C for this.

### Maintaining Group Modes

The server maintains an accurate list of groups and individuals in the groups via the global dictionary group_list. Since it was not mentioned in the requirements, I did not make it so that the mode is updated to ‘normal’ if an individual deregistered while in a group.

Thus, deregistering does not cause an update to group_list or the server_table.

Since group_list is not updated, this results in a bit of inaccuracy because list_members still includes that individual.

However, once a member currently in the group tries to send the deregistered member a message via send_group, the group_list and server_table are updated and so list_members will no longer show the deregistered member. At this point the server will say, for example, “[Client aysha not responsive, removed from group skii]”.
