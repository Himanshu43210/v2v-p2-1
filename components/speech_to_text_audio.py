
# # # # # Speech to text DEEPGRAM
# ### Transcription should not be empty
# # getting audio rather than opening stream

import asyncio
import json
import websockets

class Transcriber:
    def __init__(self):
        self.audio_queue = asyncio.Queue()
        self.stop_pushing = False

    async def add_audio_chunk(self, audio_chunk):
        """Add an audio chunk to the queue."""
        if not self.stop_pushing:
            await self.audio_queue.put(audio_chunk)

    async def sender(self, ws, timeout=0.1):
        """Send audio data to Deepgram."""
        try:
            while not self.stop_pushing:
                audio_chunk = await asyncio.wait_for(self.audio_queue.get(), timeout)
                print("Audio chunk (first 10 bytes):", audio_chunk[:10])
                await ws.send(audio_chunk)
        except asyncio.TimeoutError:
            self.stop_pushing = True
            await ws.close()

    async def receiver(self, ws):
        """Receive transcription results from Deepgram."""
        try:
            async for msg in ws:
                res = json.loads(msg)
                if res.get("is_final"):
                    transcript = (
                        res.get("channel", {})
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                    if transcript.strip():
                        print("Transcript:", transcript)
                        self.stop_pushing = True
                        return transcript
        except asyncio.TimeoutError:
            await ws.close()
            return None

    async def run(self, key):
        deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        
        async with websockets.connect(
            deepgram_url, 
            extra_headers={"Authorization": "Token {}".format(key)}, 
            timeout=0.3
        ) as ws:
            sender_coroutine = self.sender(ws)
            receiver_coroutine = self.receiver(ws)
            _, transcript = await asyncio.gather(sender_coroutine, receiver_coroutine)
            return transcript
