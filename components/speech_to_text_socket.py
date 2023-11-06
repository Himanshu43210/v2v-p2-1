# speech_to_text.py

import os
import asyncio
import websockets
import json

# Load environment variables from .env file for secure access
from dotenv import load_dotenv
load_dotenv()

# Deepgram API credentials
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

# Ensure the API key is available
if not DEEPGRAM_API_KEY:
    raise ValueError("The Deepgram API key is not set in the environment variables.")

# Define the Deepgram WebSocket URL with query parameters for transcription options
DEEPGRAM_URL = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"

# async def transcribe_socket(conn):
#     # Set up the connection to Deepgram
#     async with websockets.connect(
#         DEEPGRAM_URL,
#         extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
#         ping_timeout=None,
#     ) as dg_websocket:

#         # Function to send data from the socket connection to Deepgram
#         async def send_audio_from_socket():
#             try:
#                 while True:
#                     data = conn.recv(1024)  # This buffer size can be changed depending on your use case
#                     if not data:
#                         break
#                     await dg_websocket.send(data)
#             except websockets.exceptions.ConnectionClosedOK:
#                 pass  # Connection was closed cleanly
#             finally:
#                 # Tell Deepgram to process the last chunk of audio by sending an empty message
#                 await dg_websocket.send(b'')

#         # Function to receive transcriptions from Deepgram
#         async def receive_transcriptions():
#             transcript = ''
#             try:
#                 async for message in dg_websocket:
#                     data = json.loads(message)
#                     if data.get('is_final'):
#                         # Extract the transcript from the received data
#                         transcript = data['channel']['alternatives'][0]['transcript']
#                         print("Transcript:", transcript)
#                         break
#             except websockets.exceptions.ConnectionClosedOK:
#                 pass  # Connection was closed cleanly
#             return transcript

#         # Start sender and receiver coroutines
#         sender_task = asyncio.create_task(send_audio_from_socket())
#         receiver_task = asyncio.create_task(receive_transcriptions())

#         # Wait for both tasks to complete
#         await sender_task
#         return await receiver_task

async def transcribe_socket(conn):
    async with websockets.connect(
        DEEPGRAM_URL,
        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        ping_timeout=None,
    ) as dg_websocket:

        # Define a queue to hold received audio data
        queue = asyncio.Queue()

        # Function to send data from the socket connection to Deepgram
        async def send_audio_from_socket():
            while True:
                # Get data from the queue
                data = await queue.get()
                if data is None:
                    # Stop if None is received, signaling the end of input
                    break
                await dg_websocket.send(data)

            # Tell Deepgram to process the last chunk of audio by sending an empty message
            await dg_websocket.send(b'')

        # Function to receive transcriptions from Deepgram
        async def receive_transcriptions():
            transcript = ''
            try:
                async for message in dg_websocket:
                    data = json.loads(message)
                    if data.get('is_final'):
                        transcript = data['channel']['alternatives'][0]['transcript']
                        break
            except websockets.exceptions.ConnectionClosedOK:
                pass
            return transcript

        # Start sender and receiver coroutines
        sender_task = asyncio.create_task(send_audio_from_socket())
        receiver_task = asyncio.create_task(receive_transcriptions())

        # Begin receiving audio from the client and putting it in the queue
        while True:
            data = conn.recv(1024)
            if not data:
                break
            await queue.put(data)

        # Signal the end of audio input
        await queue.put(None)

        # Wait for both tasks to complete
        await sender_task
        return await receiver_task
