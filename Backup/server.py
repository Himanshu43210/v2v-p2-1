import socket
import wave
import pyaudio
import threading

# Server's IP address and port
SERVER_IP = "0.0.0.0"
SERVER_PORT = 12345
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Initialize PyAudio
p = pyaudio.PyAudio()

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Avoid bind() exception: OSError: [Errno 98] Address already in use
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the port
server_address = (SERVER_IP, SERVER_PORT)
print(f"Starting up on {server_address[0]} port {server_address[1]}")
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(1)


def client_thread(connection, client_address):
    try:
        print(f"Connection from {client_address} has been established.")

        # Receive the data in chunks
        frames = []
        while True:
            data = connection.recv(CHUNK_SIZE)
            if not data:
                break
            frames.append(data)

        # Save the received audio data to a file
        with wave.open("server_recording.wav", "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
        print(f"Recording from {client_address} saved.")

        # Send the recording back to the client
        with wave.open("server_recording.wav", "rb") as wf:
            data = wf.readframes(CHUNK_SIZE)
            while data:
                connection.sendall(data)
                data = wf.readframes(CHUNK_SIZE)
        print(f"Playback sent to {client_address}.")

    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"Other exception: {e}")
    finally:
        # Clean up the connection
        connection.close()
        print(f"Connection with {client_address} closed.")


while True:
    # Wait for a connection
    print("Waiting for a connection...")
    client_connection, client_address = server_socket.accept()

    # Start a new thread for the client
    threading.Thread(
        target=client_thread, args=(client_connection, client_address)
    ).start()
