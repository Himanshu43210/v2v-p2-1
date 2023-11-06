# # import socket
# # import pyaudio
# # import wave

# # # Audio recording parameters
# # FORMAT = pyaudio.paInt16
# # CHANNELS = 1
# # RATE = 44100
# # CHUNK_SIZE = 1024
# # RECORD_SECONDS = 5  # Record for 5 seconds

# # # Server information
# # HOST = "127.0.0.1"  # The server's hostname or IP address
# # PORT = 65432  # The port used by the server

# # # Initialize PyAudio
# # audio = pyaudio.PyAudio()

# # # Start recording
# # stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
# # print("Recording...")
# # frames = []

# # for _ in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
# #     data = stream.read(CHUNK_SIZE)
# #     frames.append(data)

# # print("Finished recording.")

# # # Stop and close the stream
# # stream.stop_stream()
# # stream.close()
# # audio.terminate()

# # # Create a socket connection to the server
# # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # try:
# #     client_socket.connect((HOST, PORT))
# # except socket.error as e:
# #     print(f"Socket error: {e}")
# #     exit(1)

# # print("Sending data to server...")

# # # Send the recorded audio data to the server
# # for frame in frames:
# #     client_socket.sendall(frame)

# # print("Finished sending data. Awaiting server response...")

# # # Receive data from the server, which we expect to be audio data
# # response_frames = []
# # while True:
# #     try:
# #         data = client_socket.recv(CHUNK_SIZE)
# #         if not data:
# #             break
# #         response_frames.append(data)
# #     except socket.error as e:
# #         print(f"Socket error while receiving: {e}")
# #         break

# # print("Received response from server.")

# # # Now we'll save the server's response
# # output_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
# # print("Playing server's response...")
# # for frame in response_frames:
# #     output_stream.write(frame)

# # output_stream.stop_stream()
# # output_stream.close()
# # audio.terminate()

# # # Save the conversation (optional)
# # with wave.open("conversation.wav", "wb") as wave_file:
# #     wave_file.setnchannels(CHANNELS)
# #     wave_file.setsampwidth(audio.get_sample_size(FORMAT))
# #     wave_file.setframerate(RATE)
# #     wave_file.writeframes(b''.join(frames + response_frames))

# # print("Conversation saved.")

# # # Close the socket connection
# # client_socket.close()
# # print("Connection closed.")

# import socket
# import pyaudio
# import wave

# # Audio recording parameters
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# CHUNK_SIZE = 1024
# RECORD_SECONDS = 5  # Record for 5 seconds

# # Server information
# HOST = "127.0.0.1"  # The server's hostname or IP address
# PORT = 65432  # The port used by the server

# # Initialize PyAudio
# audio = pyaudio.PyAudio()

# # Start recording
# stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
# print("Recording...")
# frames = []

# for _ in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
#     data = stream.read(CHUNK_SIZE)
#     frames.append(data)

# print("Finished recording.")

# # Stop and close the stream
# stream.stop_stream()
# stream.close()
# audio.terminate()

# # Create a socket connection to the server
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# try:
#     client_socket.connect((HOST, PORT))
# except socket.error as e:
#     print(f"Socket error: {e}")
#     exit(1)

# print("Sending data to server...")

# # Send the recorded audio data to the server
# for frame in frames:
#     client_socket.sendall(frame)

# print("Finished sending data. Awaiting server response...")

# print("Finished sending data. Awaiting server response...")

# # Receive the file size from the server
# file_size = client_socket.recv(1024).decode('utf-8')
# print(f"Received file size: {file_size}")

# # Send acknowledgment for file size
# client_socket.sendall(b'ACK')

# # Receive the file data from the server
# response_data = bytearray()
# bytes_recd = 0
# file_size = int(file_size)
# while bytes_recd < file_size:
#     packet = client_socket.recv(min(file_size - bytes_recd, CHUNK_SIZE))
#     if not packet:
#         break
#     response_data.extend(packet)
#     bytes_recd += len(packet)

# print("Received response from server.")

# # Now we'll save the server's response
# with wave.open("server_response.wav", "wb") as wave_file:
#     wave_file.setnchannels(CHANNELS)
#     wave_file.setsampwidth(audio.get_sample_size(FORMAT))
#     wave_file.setframerate(RATE)
#     wave_file.writeframes(response_data)

# print("Server response saved.")

# # Close the socket connection
# client_socket.close()
# print("Connection closed.")

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

stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)

print("Recording...")

frames = []
for i in range(0, int(RATE / CHUNK_SIZE * RECORD_SECONDS)):
    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
    frames.append(data)

print("Finished recording.")

stream.stop_stream()
stream.close()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
received_frames = []

try:
    client_socket.connect((HOST, PORT))

    print("Sending data to server...")
    for frame in frames:
        client_socket.sendall(frame)

    print("Finished sending data. Waiting for response...")
    
    data = client_socket.recv(CHUNK_SIZE)
    while data:
        received_frames.append(data)
        data = client_socket.recv(CHUNK_SIZE)

    print("Received response from server.")
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    client_socket.close()

if received_frames:
    print("Playing server's response...")
    output_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    for frame in received_frames:
        output_stream.write(frame)

    output_stream.stop_stream()
    output_stream.close()
else:
    print("No response received from server.")
    
response_audio_path = "server_response.wav"
wf = wave.open(response_audio_path, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(received_frames))
wf.close()

print(f"Received audio saved to {response_audio_path}")

# Then, play the server's response
print("Playing server's response...")
output_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True,
)

wf = wave.open(response_audio_path, 'rb')
data = wf.readframes(CHUNK_SIZE)
while data:
    output_stream.write(data)
    data = wf.readframes(CHUNK_SIZE)

output_stream.stop_stream()
output_stream.close()
wf.close()

print("Playback finished.")

audio.terminate()
