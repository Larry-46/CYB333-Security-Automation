import socket
import threading

#Define the port number for the server
PORT = 12345

#Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Bind the socket to the port
server_socket.bind(('', PORT))

#Listen for incoming connections
server_socket.listen(5)

print("Server started. Listening for connections ...")

while True:
    #Accept an incoming connection
    client_socket, addr = server_socket.accept()
    print(f"Connected by {addr}")

    #Handle the client connection in a separate thread
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()

def handle_client(client_socket):

    try:
        #Receive data from the client
        data = client_socket.recv(1024).decode('utf-8')
        print(f"Received data: {data}")

        #Send a response back to the client
        client_soc.sendall(b"Hello, client!")

        #Close the client socket
        client_socket.close()
    
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

#Close the server socket
server_socket.close()

