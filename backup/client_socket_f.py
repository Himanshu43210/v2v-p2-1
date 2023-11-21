import asyncio
import websockets
import pyaudio
import threading
import queue
import json

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
CHUNK_SIZE = 1024
WEBSOCKET_URL = "ws://127.0.0.1:65432"
# WEBSOCKET_URL = "ws://socket.itsolutionshub.com/"
# WEBSOCKET_URL = "wss://socket.itsolutionshub.com/"  # If the server supports SSL/TLS
# WEBSOCKET_URL = "https://socket.itsolutionshub.com/"

audio = pyaudio.PyAudio()


def send_audio_chunks(stream, websocket, loop):
    print("Sending audio chunks...")
    while True:
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        audio_chunk = {
            "audio": data.hex()
        }  # Convert binary data to hex string for JSON

        # Use the provided event loop to schedule the coroutine
        future = asyncio.run_coroutine_threadsafe(
            websocket.send(json.dumps(audio_chunk)), loop
        )

        try:
            # Wait for the future to be completed
            future.result()
        except Exception as e:
            print(f"Error sending audio chunk: {e}")
            break


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
            # Handle the error as needed, maybe restart the stream or log the error
        except OSError as e:
            print(f"Stream error: {e}, possibly the stream is not open.")
            break

        audio_queue.task_done()

async def receive_audio(websocket, audio_queue):
    print("Receiving audio...")
    async for message in websocket:
        print(f"Received message type: {type(message)}")  # Debugging line
        if isinstance(message, bytes):
            print("Received binary message (presumed audio data)")
            audio_queue.put(message)
        else:
            print(f"Received non-binary message: {message}")

import asyncio
import websockets

async def send_ping_periodically(websocket, interval=5):
    """
    Send a ping to the server every 'interval' seconds.
    """
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(interval)
        except websockets.exceptions.ConnectionClosed:
            break


async def main():
    loop = asyncio.get_event_loop()

    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                # Open the stream for recording
                stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                )

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

                audio_thread = threading.Thread(
                    target=send_audio_chunks, args=(stream, websocket, loop)
                )
                audio_thread.start()

                audio_queue = queue.Queue()
                playback_thread = threading.Thread(
                    target=play_audio, args=(audio, playback_stream, audio_queue)
                )
                playback_thread.start()

                # Start the ping task
                ping_task = asyncio.create_task(send_ping_periodically(websocket))

                await receive_audio(websocket, audio_queue)

                playback_thread.join()

                if not playback_stream.is_stopped():
                    playback_stream.stop_stream()
                playback_stream.close()

                audio_thread.join()

                # Wait for the ping task to finish (in case of disconnection)
                await ping_task

                stream.stop_stream()
                stream.close()

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}, attempting to reconnect...")
            # await asyncio.sleep(5)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main())