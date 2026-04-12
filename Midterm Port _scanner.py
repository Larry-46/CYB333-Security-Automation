import socket
import time
import threading

#Define the target host and port range
TARGET_HOST = "127.0.0.1" # localhost
PORT_RANGE = range(1, 1024) # 1-1023

#Define the delay between scan attempts (in seconds)
SCAN_DELAY = 0.1

#Define the maximum number of concurrent connections
MAX_CONCURRENT_CONNECTIONS = 5

#Create a socket object
socket_object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Function to scan a single port
def scan_port(port):
    try:

        #Create a socket object for the port
        port_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Set a timeout for the connection
        port_socket.settimeout(1)

        #Attempt to connect to the port
        port_socket.connect((TARGET_HOST, port))

        #If the connection is successful, print the port is open
        print(f"Port {port} is open.")

        #Close the port socket
        port_socket.close()
    
    except Exception as e:
        #If the connection fails, the port is closed
        print(f"Port {port} is closed: {e}")

    #Function to scan the port range
    def scan_port_range():
        threads = []
        for port in PORT_RANGE:
            #Create a thread for each port scan
            port_thread = threading.Thread(target=scan_port, args=(port,))
            port_thread.start()

            #Wait for the thread to finish
            port_thread.join()

            #Add a delay between scan attempts
            time.sleep(SCAN_DELAY)
        
        #Scan the port range
        scan_port_range()

        #Close the socket object
        socket_object.close()
    