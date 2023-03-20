import ipaddress

def checkPort(port):
    if (int(port) < 1024 or int(port) > 65535):
        print("Error: Port number is not in range [1024, 65535]")
        return False
    return True

def checkIP(ip):
    if (ip == 'localhost'):
        return True
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        print("Error: invalid IP address")
        return False