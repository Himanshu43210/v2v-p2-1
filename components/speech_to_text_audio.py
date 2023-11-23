
# # # # Speech to text DEEPGRAM
### Transcription should not be empty
# getting audio rather than opening stream

import os
import asyncio
import json
import pyaudio
import websockets
from dotenv import load_dotenv

# Load environment variables from .env file for secure access
load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000

class Transcriber:
    def __init__(self):
        self.audio_queue = asyncio.Queue()
        self.stream = None  # Placeholder for the PyAudio stream
        self.stop_pushing = False  # Flag to stop pushing data to the queue

    def mic_callback(self, input_data, frame_count, time_info, status_flag):
        if not self.stop_pushing:
            # print("Pushing data to the queue")
            self.audio_queue.put_nowait(input_data)
        return (input_data, pyaudio.paContinue)

    async def sender(self, ws, timeout=0.1):
        """Send audio data from the microphone to Deepgram."""
        try:
            while not self.stop_pushing:  # Check the flag
                mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
                await ws.send(mic_data)
        except asyncio.TimeoutError:
            # print("Sender coroutine timed out. Closing...")
            self.stop_pushing = True  # Set the flag
            await ws.close()
            return
        except websockets.exceptions.ConnectionClosedOK:
            await ws.send(json.dumps({"type": "CloseStream"}))

    async def receiver(self, ws):
        """Receive transcription results from Deepgram."""
        try:
            async for msg in ws:
                # print("Received message from WebSocket")
                res = json.loads(msg)
                if res.get("is_final"):
                    transcript = (
                        res.get("channel", {})
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                    # Check if the transcript is empty or not
                    if transcript.strip():  
                        print("Transcript:", transcript)
                        self.stop_pushing = True  # Set the flag to stop pushing data to the queue
                        return transcript
        except asyncio.TimeoutError:
            # print("Receiver coroutine timed out. Stopping...")
            await ws.close()
            return None


    async def run(self, key):
        deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        
        # Open the microphone stream
        p = pyaudio.PyAudio()
        # self.stream = p.open(format=FORMAT, channels=1, rate=16000, input=True, input_device_index=11, stream_callback=self.mic_callback)
        self.stream = p.open(format=FORMAT, channels=1, rate=16000, input=True, stream_callback=self.mic_callback)
        self.stream.start_stream()
        
        async with websockets.connect(
            deepgram_url, 
            extra_headers={"Authorization": "Token {}".format(key)}, 
            timeout=0.3  # added timeout here
        ) as ws:
            
            # Launch sender and receiver coroutines
            sender_coroutine = self.sender(ws)
            receiver_coroutine = self.receiver(ws)

            # Collect results (assuming you return the transcript from the receiver)
            _, transcript = await asyncio.gather(sender_coroutine, receiver_coroutine)
            
            # Stop the microphone stream
            self.stream.stop_stream()
            self.stream.close()
            p.terminate()
            print(transcript)
            return transcript

def transcribe_stream():
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    if DEEPGRAM_API_KEY is None:
        print("Please set the DEEPGRAM_API_KEY environment variable.")
        return

    print("Start speaking...")
    transcriber = Transcriber()
    
    loop = asyncio.get_event_loop()  # Use an existing loop if available, otherwise create a new one
    transcript = loop.run_until_complete(transcriber.run(DEEPGRAM_API_KEY))
    return transcript

