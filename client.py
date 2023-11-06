import socket
import pyaudio
import wave

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024
RECORD_SECONDS = 5

HOST = "127.0.0.1"
PORT = 65432

audio = pyaudio.PyAudio()

# stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)

# print("Recording...")

# frames = []
# for i in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
#     data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
#     frames.append(data)

# print("Finished recording.")

# stream.stop_stream()
# stream.close()

# Continuously record and send the audio in chunks
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
print("Recording and streaming...")

try:
    while True:  # You can set a condition to end this loop
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        if not data:
            break
        client_socket.sendall(data)
except KeyboardInterrupt:
    # Handle any exception or break condition
    print("Finished recording.")
finally:
    # Stop and close the audio stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Inform the server that the transmission is done
    client_socket.shutdown(socket.SHUT_WR)

    # Handle the server's response if needed
    response = client_socket.recv(4096)  # Adjust buffer size if needed
    print("Received:", response.decode())

    # Close the socket connection
    client_socket.close()
