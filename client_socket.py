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
        playback_stream.write(data)
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


async def main():
    loop = asyncio.get_event_loop()  # Get the current event loop

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        # Open the stream for recording
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        try:
            audio_thread = threading.Thread(
                target=send_audio_chunks, args=(stream, websocket, loop)
            )
            audio_thread.start()

            playback_stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
            )

            try:
                audio_queue = queue.Queue()
                playback_thread = threading.Thread(
                    target=play_audio, args=(audio, playback_stream, audio_queue)
                )
                playback_thread.start()

                await receive_audio(websocket, audio_queue)

                playback_thread.join()
            finally:
                playback_stream.stop_stream()
                playback_stream.close()

            audio_thread.join()
        finally:
            stream.stop_stream()
            stream.close()


if __name__ == "__main__":
    asyncio.run(main())
