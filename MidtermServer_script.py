import socket

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_socket.bind(("127.0.0.1", 8080))

# Listen for incoming connections
server_socket.listen(1)

print("Server started. Listening for connections...")

while True:
    # Accept an incoming connection
    client_socket, address = server_socket.accept()
    print(f"Connected by {address}")

    # Send a response back to the client
    response = "HTTP/1.1 200 OK\r\n\r\nHello, client!".encode()
    client_socket.sendall(response)

    # Close the client socket
    client_socket.close()