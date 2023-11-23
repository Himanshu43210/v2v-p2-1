from flask import Flask, render_template, request
import asyncio
import threading
import websockets
import json
import os

app = Flask(__name__)

import asyncio
import websockets
import pyaudio
import threading
import queue
import json
import sys
sys.path.append("./components")
sys.path.append("./constants")
import speech_to_text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
WEBSOCKET_URL = "ws://127.0.0.1:65432"  # Update this to your server's WebSocket URL

FORMAT = pyaudio.paInt16  # Linear16 encoding
CHANNELS = 1  # Mono audio
# RATE = 16000  # Sample rate of 16000 Hz

RATE = 24000

CHUNK_SIZE = 1024

audio = pyaudio.PyAudio()

def play_audio(audio, playback_stream, audio_queue):
    while True:
        data = audio_queue.get()
        if not data:
            print("End of audio playback.")
            audio_queue.task_done()
            break

        try:
            if playback_stream.is_stopped():
                playback_stream.start_stream()

            playback_stream.write(data)
        except IOError as e:
            print(f"IOError occurred: {e}")
        except OSError as e:
            print(f"Stream error: {e}, possibly the stream is not open.")
            break

        audio_queue.task_done()

async def receive_audio(websocket, audio_queue, transcriber):
    print("Receiving audio...")
    async for message in websocket:
        if isinstance(message, bytes):
            audio_queue.put(message)
        elif message == '{"message": "END_OF_FILE"}':
            print("End of file received, restarting transcription.")
            return True  # Indicates that transcription should restart
        else:
            print(f"Received non-binary message: {message}")

async def send_transcription(websocket, transcription):
    """Send the transcription to the server."""
    await websocket.send(json.dumps({"transcription": transcription}))

async def main():
    loop = asyncio.get_event_loop()

    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                # Initialize the transcriber
                transcriber = speech_to_text.Transcriber()

                # Open the playback stream
                playback_stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK_SIZE,
                )

                # Ensure the playback stream is started
                if playback_stream.is_stopped():
                    playback_stream.start_stream()

                audio_queue = queue.Queue()
                playback_thread = threading.Thread(
                    target=play_audio, args=(audio, playback_stream, audio_queue)
                )
                playback_thread.start()

                while True:
                    # Start transcription
                    transcription_task = asyncio.create_task(
                        transcriber.run(DEEPGRAM_API_KEY)
                    )
                    transcription = await transcription_task

                    # Send the transcription to the server
                    await send_transcription(websocket, transcription)

                    # Receive and play back audio from the server
                    should_restart = await receive_audio(websocket, audio_queue, transcriber)
                    if not should_restart:
                        break

                playback_thread.join()

                if not playback_stream.is_stopped():
                    playback_stream.stop_stream()
                playback_stream.close()

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}, attempting to reconnect...")
        except Exception as e:
            print(f"An error occurred: {e}")
            break

# if __name__ == "__main__":
#     asyncio.run(main())


@app.route('/')
def index():
    return render_template('index.html')

def start_transcription():
    asyncio.run(main())

@app.route('/start_transcription', methods=['POST'])
def handle_start_transcription():
    threading.Thread(target=start_transcription, daemon=True).start()
    return ('', 204)

if __name__ == "__main__":
    app.run(debug=True)
