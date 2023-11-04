import socket
import pyaudio
import wave

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024
RECORD_SECONDS = 5  # change this to record for longer

# Server information
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 12345  # The port used by the server

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Start recording
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK_SIZE,
)

print("Recording...")

frames = []

for i in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
    data = stream.read(CHUNK_SIZE)
    frames.append(data)
    print(f"Captured audio frame size: {len(data)}")  # Confirming data is captured

print("Finished recording.")

# Stop and close the stream
stream.stop_stream()
stream.close()
audio.terminate()

# Create a socket connection to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print("Sending data to server...")

# Send the recorded audio data to the server
for frame in frames:
    client_socket.sendall(frame)

print("Finished sending data.")

# Close the socket connection
client_socket.close()

print("Connection closed.")
