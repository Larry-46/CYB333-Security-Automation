import socket

# Define the target host and port
TARGET_HOST = "127.0.0.1"
PORT = 8080

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((TARGET_HOST, PORT))

# Send data to the server
data = "Hello, server!".encode()
client_socket.sendall(data)

# Receive data from the server
response = client_socket.recv(1024)
print(f"Received response from server: {response.decode()}")

# Close the client socket
client_socket.close()