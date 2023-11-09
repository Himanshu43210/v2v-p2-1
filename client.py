import socket
import pyaudio
import queue
import threading

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
CHUNK_SIZE = 1024
HOST = "127.0.0.1"
PORT = 65432

# Initialize PyAudio
audio = pyaudio.PyAudio()

def send_audio_chunks(stream, client_socket, host, port):
    print("Sending audio chunks...")
    while True:
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        client_socket.sendto(data, (host, port))
        try:
            server_response, _ = client_socket.recvfrom(4096)
            if server_response.decode('utf-8') == 'transcription done':
                print("Transcription done, stop sending and start receiving.")
                return  # Exit the function when server signals transcription is done
        except socket.timeout:
            # If no response received, continue sending audio chunks
            continue

def play_audio(audio, playback_stream, audio_queue):
    while True:
        data = audio_queue.get()
        if data == b'END_OF_FILE':
            print("Received END_OF_FILE signal. Ready for next round.")
            audio_queue.task_done()
            break
        playback_stream.write(data)
        audio_queue.task_done()

def receive_audio(client_socket, audio_queue):
    print("Receiving audio...")
    while True:
        try:
            data, _ = client_socket.recvfrom(4096)
            if data == b'END_OF_FILE':
                audio_queue.put(data)  # Signal to end playback
                break
            audio_queue.put(data)
        except socket.timeout:
            continue

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(0.5)
    
    try:
        while True:
            # Start a new round of sending and receiving audio
            with audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE) as stream:
                send_audio_chunks(stream, client_socket, HOST, PORT)

            # Create a new stream for playback
            with audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK_SIZE) as playback_stream:
                audio_queue = queue.Queue()
                playback_thread = threading.Thread(target=play_audio, args=(audio, playback_stream, audio_queue))
                playback_thread.start()

                receive_audio(client_socket, audio_queue)

                # Wait until the playback thread has finished
                playback_thread.join()

    except KeyboardInterrupt:
        print("Finished recording.")
    finally:
        client_socket.close()
        audio.terminate()

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(0.5)
    
    try:
        while True:
            # Open the stream for recording
            stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
            
            # Send audio chunks
            send_audio_chunks(stream, client_socket, HOST, PORT)
            
            # Close the recording stream
            stream.stop_stream()
            stream.close()
            
            # Open a new stream for playback
            playback_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK_SIZE)
            
            # Create a queue to hold audio chunks
            audio_queue = queue.Queue()
            
            # Start the playback thread
            playback_thread = threading.Thread(target=play_audio, args=(audio, playback_stream, audio_queue))
            playback_thread.start()
            
            # Receive audio chunks
            receive_audio(client_socket, audio_queue)
            
            # Wait until all audio chunks have been played
            playback_thread.join()
            
            # Close the playback stream
            playback_stream.stop_stream()
            playback_stream.close()

    except KeyboardInterrupt:
        print("Finished recording.")
    finally:
        # Cleanup
        client_socket.close()
        audio.terminate()

if __name__ == '__main__':
    main()
