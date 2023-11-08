import socket
import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024

HOST = "127.0.0.1"
PORT = 65432

audio = pyaudio.PyAudio()

# UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
print("Recording and streaming...")

try:
    while True:  # You can set a condition to end this loop
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        if not data:
            break
        # Send data through UDP
        client_socket.sendto(data, (HOST, PORT))
except KeyboardInterrupt:
    # Handle any exception or break condition
    print("Finished recording.")
finally:
    # Stop and close the audio stream
    stream.stop_stream()
    stream.close()
    audio.terminate()
    # Close the socket connection
    client_socket.close()
