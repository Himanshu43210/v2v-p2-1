
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
