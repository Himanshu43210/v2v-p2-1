
# # # ## Speech to text DEEPGRAM
# # # ## Transcription should not be empty
# # # ## Socket connection

# # # import asyncio
# # # import json
# # # import pyaudio
# # # import websockets
# # # from dotenv import load_dotenv

# # # # Load environment variables from .env file for secure access
# # # load_dotenv()

# # # FORMAT = pyaudio.paInt16
# # # CHANNELS = 1
# # # RATE = 16000
# # # CHUNK = 8000

# # # class Transcriber:
# # #     def __init__(self, audio_source):
# # #         self.audio_queue = asyncio.Queue()
# # #         self.audio_source = audio_source  # The socket connection to receive data from
# # #         self.stop_pushing = False  # Flag to stop pushing data to the queue

# # #     async def socket_to_queue(self):
# # #         """Receive audio data from the socket and put it in the queue."""
# # #         while not self.stop_pushing:
# # #             data = await self.audio_source.recv(CHUNK)
# # #             if not data:
# # #                 self.stop_pushing = True  # Stop if no data received
# # #                 break
# # #             await self.audio_queue.put(data)

# # #     def mic_callback(self, input_data, frame_count, time_info, status_flag):
# # #         if not self.stop_pushing:
# # #             # print("Pushing data to the queue")
# # #             self.audio_queue.put_nowait(input_data)
# # #         return (input_data, pyaudio.paContinue)

# # #     async def sender(self, ws, timeout=0.1):
# # #         """Send audio data from the microphone to Deepgram."""
# # #         try:
# # #             while not self.stop_pushing:  # Check the flag
# # #                 mic_data = await asyncio.wait_for(self.audio_queue.get(), timeout)
# # #                 await ws.send(mic_data)
# # #         except asyncio.TimeoutError:
# # #             # print("Sender coroutine timed out. Closing...")
# # #             self.stop_pushing = True  # Set the flag
# # #             await ws.close()
# # #             return
# # #         except websockets.exceptions.ConnectionClosedOK:
# # #             await ws.send(json.dumps({"type": "CloseStream"}))

# # #     async def receiver(self, ws):
# # #         """Receive transcription results from Deepgram."""
# # #         try:
# # #             async for msg in ws:
# # #                 # print("Received message from WebSocket")
# # #                 res = json.loads(msg)
# # #                 if res.get("is_final"):
# # #                     transcript = (
# # #                         res.get("channel", {})
# # #                         .get("alternatives", [{}])[0]
# # #                         .get("transcript", "")
# # #                     )
# # #                     # Check if the transcript is empty or not
# # #                     if transcript.strip():  
# # #                         print("Transcript:", transcript)
# # #                         self.stop_pushing = True  # Set the flag to stop pushing data to the queue
# # #                         return transcript
# # #         except asyncio.TimeoutError:
# # #             # print("Receiver coroutine timed out. Stopping...")
# # #             await ws.close()
# # #             return None


# # #     async def run(self, key):
# # #         deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
        
# # #         async with websockets.connect(
# # #             deepgram_url, 
# # #             extra_headers={"Authorization": "Token {}".format(key)}, 
# # #             timeout=0.3  # added timeout here
# # #         ) as ws:
            
# # #             # Launch socket_to_queue and receiver coroutines
# # #             socket_to_queue_coroutine = self.socket_to_queue()
# # #             receiver_coroutine = self.receiver(ws)

# # #             # Collect results (assuming you return the transcript from the receiver)
# # #             _, transcript = await asyncio.gather(socket_to_queue_coroutine, receiver_coroutine)

# # #             print(transcript)
# # #             return transcript

# # # async def handle_client(reader, writer):
# # #     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
# # #     if DEEPGRAM_API_KEY is None:
# # #         print("Please set the DEEPGRAM_API_KEY environment variable.")
# # #         return

# # #     transcriber = Transcriber(reader)  # Pass the reader from the client connection
# # #     transcript = await transcriber.run(DEEPGRAM_API_KEY)
# # #     writer.close()

# # # async def main(host, port):
# # #     server = await asyncio.start_server(handle_client, host, port)
# # #     addr = server.sockets[0].getsockname()
# # #     print(f'Serving on {addr}')

# # #     async with server:
# # #         await server.serve_forever()

# # # if __name__ == '__main__':
# # #     host = '127.0.0.1'
# # #     port = 65432
# # #     asyncio.run(main(host, port))
    
# # # def transcribe_stream():
# # #     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
# # #     if DEEPGRAM_API_KEY is None:
# # #         print("Please set the DEEPGRAM_API_KEY environment variable.")
# # #         return

# # #     print("Start speaking...")
# # #     transcriber = Transcriber()
    
# # #     loop = asyncio.get_event_loop()  # Use an existing loop if available, otherwise create a new one
# # #     transcript = loop.run_until_complete(transcriber.run(DEEPGRAM_API_KEY))
# # #     return transcript



# # # speech_to_text.py
# # import os
# # import asyncio
# # import json
# # import pyaudio
# # import websockets
# # from dotenv import load_dotenv
# # import socket

# # # Load environment variables from .env file for secure access
# # load_dotenv()

# # FORMAT = pyaudio.paInt16
# # CHANNELS = 1
# # RATE = 16000
# # CHUNK = 8000

# # # Add socket to the Transcriber init function and setup
# # # class Transcriber:
# # #     def __init__(self, client_socket):
# # #         self.audio_queue = asyncio.Queue()
# # #         self.client_socket = client_socket  # Socket to receive audio from
# # #         self.stop_pushing = False  # Flag to stop pushing data to the queue

# # class Transcriber:
# #     def __init__(self, client_socket, loop=None):
# #         self.loop = loop or asyncio.get_event_loop()
# #         self.audio_queue = asyncio.Queue(loop=self.loop)
# #         self.client_socket = client_socket  # Socket to receive audio from
# #         self.stop_pushing = False  # Flag to stop pushing data to the queue

# #     async def socket_sender(self, ws, timeout=0.1):
# #         """Send audio data from the socket to Deepgram."""
# #         try:
# #             while not self.stop_pushing:
# #                 # Receive data from the socket
# #                 socket_data = self.client_socket.recv(CHUNK)
# #                 if socket_data:
# #                     # Push socket data to Deepgram
# #                     await ws.send(socket_data)
# #                 else:
# #                     break  # If no data, stop the loop
# #         except asyncio.TimeoutError:
# #             self.stop_pushing = True
# #             await ws.close()
# #         except websockets.exceptions.ConnectionClosedOK:
# #             await ws.send(json.dumps({"type": "CloseStream"}))

# #     async def receiver(self, ws):
# #         """Receive transcription results from Deepgram."""
# #         try:
# #             async for msg in ws:
# #                 # print("Received message from WebSocket")
# #                 res = json.loads(msg)
# #                 if res.get("is_final"):
# #                     transcript = (
# #                         res.get("channel", {})
# #                         .get("alternatives", [{}])[0]
# #                         .get("transcript", "")
# #                     )
# #                     # Check if the transcript is empty or not
# #                     if transcript.strip():  
# #                         print("Transcript:", transcript)
# #                         self.stop_pushing = True  # Set the flag to stop pushing data to the queue
# #                         return transcript
# #         except asyncio.TimeoutError:
# #             # print("Receiver coroutine timed out. Stopping...")
# #             await ws.close()
# #             return None

# #     async def run(self, key):
# #         # Deepgram setup remains the same
# #         deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
# #         async with websockets.connect(
# #             deepgram_url, 
# #             extra_headers={"Authorization": "Token {}".format(key)}, 
# #             timeout=0.3
# #         ) as ws:

# #             # Use socket_sender instead of mic_callback
# #             sender_coroutine = self.socket_sender(ws)
# #             receiver_coroutine = self.receiver(ws)

# #             _, transcript = await asyncio.gather(sender_coroutine, receiver_coroutine)

# #             return transcript

# # # Function to start the transcription process
# # # def transcribe_socket(client_socket):
# # #     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
# # #     if DEEPGRAM_API_KEY is None:
# # #         print("Please set the DEEPGRAM_API_KEY environment variable.")
# # #         return

# # #     transcriber = Transcriber(client_socket)
# # #     loop = asyncio.get_event_loop()
# # #     transcript = loop.run_until_complete(transcriber.run(DEEPGRAM_API_KEY))
# # #     return transcript


# # def transcribe_socket(client_socket, loop):
# #     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
# #     if DEEPGRAM_API_KEY is None:
# #         print("Please set the DEEPGRAM_API_KEY environment variable.")
# #         return

# #     transcriber = Transcriber(client_socket)
# #     transcript = loop.run_until_complete(transcriber.run(DEEPGRAM_API_KEY))
# #     return transcript


# # # You need to pass the client_socket to this function from your main.py
# # # For example: transcript = transcribe_socket(client_socket)

# # import threading

# # # def chat_with_user(conn, addr):
# # #     text = transcribe_socket(conn)
# # #     print(text)

# # def chat_with_user(conn, addr):
# #     loop = asyncio.new_event_loop()
# #     asyncio.set_event_loop(loop)

# #     text = loop.run_until_complete(transcribe_socket(conn, loop))
# #     print(text)

# #     loop.close()

# # def server_program():
# #     host = '127.0.0.1'
# #     port = 65432

# #     server_socket = socket.socket()
# #     server_socket.bind((host, port))
# #     server_socket.listen()

# #     print(f"Server listening on {host}:{port}")

# #     try:
# #         while True:
# #             conn, addr = server_socket.accept()
# #             threading.Thread(target=chat_with_user, args=(conn, addr)).start()
# #     except KeyboardInterrupt:
# #         print("Server is closing...")
# #     finally:
# #         server_socket.close()

# # if __name__ == '__main__':
# #     server_program()
# # ###################################333


# # I want to create a server which will take socket connection, the clients which are connected to that server will send some data via microphone.
# # and in server, I have to listen that and record that data in a wav file.
# # same client after speaking will listen what he has said when server start that recording.

# # speech_to_text.py ######## Socket
# import os
# import asyncio
# import json
# import pyaudio
# import websockets
# from dotenv import load_dotenv
# import socket

# # Load environment variables from .env file for secure access
# load_dotenv()

# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 16000
# CHUNK = 8000

# # Add socket to the Transcriber init function and setup
# class Transcriber:
#     def __init__(self, client_socket):
#         self.audio_queue = asyncio.Queue()
#         self.client_socket = client_socket  # Socket to receive audio from
#         self.stop_pushing = False  # Flag to stop pushing data to the queue

#     async def socket_sender(self, ws, timeout=0.1):
#         """Send audio data from the socket to Deepgram."""
#         try:
#             while not self.stop_pushing:
#                 # Receive data from the socket
#                 socket_data = self.client_socket.recv(CHUNK)
#                 if socket_data:
#                     # Push socket data to Deepgram
#                     await ws.send(socket_data)
#                 else:
#                     break  # If no data, stop the loop
#         except asyncio.TimeoutError:
#             self.stop_pushing = True
#             await ws.close()
#         except websockets.exceptions.ConnectionClosedOK:
#             await ws.send(json.dumps({"type": "CloseStream"}))

#     async def receiver(self, ws):
#         """Receive transcription results from Deepgram."""
#         try:
#             async for msg in ws:
#                 # print("Received message from WebSocket")
#                 res = json.loads(msg)
#                 if res.get("is_final"):
#                     transcript = (
#                         res.get("channel", {})
#                         .get("alternatives", [{}])[0]
#                         .get("transcript", "")
#                     )
#                     # Check if the transcript is empty or not
#                     if transcript.strip():  
#                         print("Transcript:", transcript)
#                         self.stop_pushing = True  # Set the flag to stop pushing data to the queue
#                         return transcript
#         except asyncio.TimeoutError:
#             # print("Receiver coroutine timed out. Stopping...")
#             await ws.close()
#             return None

#     async def run(self, key):
#         # Deepgram setup remains the same
#         deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"
#         async with websockets.connect(
#             deepgram_url, 
#             extra_headers={"Authorization": "Token {}".format(key)}, 
#             timeout=0.3
#         ) as ws:

#             # Use socket_sender instead of mic_callback
#             sender_coroutine = self.socket_sender(ws)
#             receiver_coroutine = self.receiver(ws)

#             _, transcript = await asyncio.gather(sender_coroutine, receiver_coroutine)

#             return transcript

# # Function to start the transcription process
# def transcribe_socket(client_socket):
#     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
#     if DEEPGRAM_API_KEY is None:
#         print("Please set the DEEPGRAM_API_KEY environment variable.")
#         return

#     transcriber = Transcriber(client_socket)
#     loop = asyncio.get_event_loop()
#     transcript = loop.run_until_complete(transcriber.run(DEEPGRAM_API_KEY))
#     return transcript


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

async def transcribe_socket(conn):
    # Set up the connection to Deepgram
    async with websockets.connect(
        DEEPGRAM_URL,
        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        ping_timeout=None,
    ) as dg_websocket:

        # Function to send data from the socket connection to Deepgram
        async def send_audio_from_socket():
            try:
                while True:
                    data = conn.recv(1024)  # This buffer size can be changed depending on your use case
                    if not data:
                        break
                    await dg_websocket.send(data)
            except websockets.exceptions.ConnectionClosedOK:
                pass  # Connection was closed cleanly
            finally:
                # Tell Deepgram to process the last chunk of audio by sending an empty message
                await dg_websocket.send(b'')

        # Function to receive transcriptions from Deepgram
        async def receive_transcriptions():
            transcript = ''
            try:
                async for message in dg_websocket:
                    data = json.loads(message)
                    if data.get('is_final'):
                        # Extract the transcript from the received data
                        transcript = data['channel']['alternatives'][0]['transcript']
                        print("Transcript:", transcript)
                        break
            except websockets.exceptions.ConnectionClosedOK:
                pass  # Connection was closed cleanly
            return transcript

        # Start sender and receiver coroutines
        sender_task = asyncio.create_task(send_audio_from_socket())
        receiver_task = asyncio.create_task(receive_transcriptions())

        # Wait for both tasks to complete
        await sender_task
        return await receiver_task
