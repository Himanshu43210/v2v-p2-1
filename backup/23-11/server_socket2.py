# import asyncio
# import aiohttp
# import websockets
# from deepgram import Deepgram

# # DEEPGRAM_API_KEY = 'f81ff09854f9bb1535aa5909dd52ee7bff5c4e79'
# DEEPGRAM_API_KEY='967c5ce3f89d5cbb8c74107737ba36b9e1a5ba20'

# async def handle_audio(websocket, path, deepgram):
#     # deepgramLive = await deepgram.transcription.live({
#     #     'smart_format': True,
#     #     'interim_results': True,
#     #     'language': 'en-US',
#     #     'model': 'nova',
#     # })
#     # async def handle_audio(websocket, path, deepgram):
#     # try:
#     #     deepgramLive = await deepgram.transcription.live({
#     #         'smart_format': True,
#     #         'interim_results': False,
#     #         'language': 'en-US',
#     #         'model': 'nova',
#     #     })
#     # except Exception as e:
#     #     print(f"Error initializing Deepgram live transcription: {e}")
#     #     return

#     # def handle_transcript(transcript):
#     #     print(transcript)

#     # deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, handle_transcript)

#     # try:
#     #     async for message in websocket:
#     #         await deepgramLive.send(message)
#     # except websockets.exceptions.ConnectionClosed:
#     #     pass
#     # finally:
#     #     await deepgramLive.finish()
#     try:
#         deepgramLive = await deepgram.transcription.live({
#             'smart_format': True,
#             'interim_results': False,
#             'language': 'en-US',
#             'model': 'nova',
#         })
#         print("Deepgram live transcription initialized successfully.")
#     except Exception as e:
#         print(f"Error initializing Deepgram live transcription: {e}")
#         return

#     try:
#         async for message in websocket:
#             if deepgramLive:
#                 await deepgramLive.send(message)
#             else:
#                 print("Deepgram live object is None.")
#     except Exception as e:
#         print(f"Error during WebSocket communication: {e}")
#     finally:
#         if deepgramLive:
#             await deepgramLive.finish()

# async def main():
#     deepgram = Deepgram(DEEPGRAM_API_KEY)
#     start_server = websockets.serve(lambda ws, path: handle_audio(ws, path, deepgram), "localhost", 8765)
#     await start_server
#     await asyncio.Future()  # Run forever

# asyncio.run(main())

import asyncio
import websockets
from deepgram import Deepgram

# DEEPGRAM_API_KEY = 'YOUR_DEEPGRAM_API_KEY'
DEEPGRAM_API_KEY='967c5ce3f89d5cbb8c74107737ba36b9e1a5ba20'

class DeepgramLiveSession:
    def __init__(self, deepgram):
        self.deepgram = deepgram
        self.deepgramLive = None

    async def initialize(self):
        try:
            self.deepgramLive = await self.deepgram.transcription.live({
                'smart_format': True,
                'interim_results': False,
                'language': 'en-US',
                'model': 'nova',
            })
            print("Deepgram live transcription initialized successfully.")
        except Exception as e:
            print(f"Error initializing Deepgram live transcription: {e}")

    async def send_audio(self, message):
        if self.deepgramLive:
            try:
                await self.deepgramLive.send(message)
            except Exception as e:
                print(f"Error sending audio to Deepgram: {e}")
        else:
            print("Deepgram live object is None.")

    async def close(self):
        if self.deepgramLive:
            await self.deepgramLive.finish()

async def handle_audio(websocket, path, deepgram_session):
    await deepgram_session.initialize()

    try:
        async for message in websocket:
            await deepgram_session.send_audio(message)
    except Exception as e:
        print(f"Error during WebSocket communication: {e}")
    finally:
        await deepgram_session.close()

async def main():
    deepgram = Deepgram(DEEPGRAM_API_KEY)
    deepgram_session = DeepgramLiveSession(deepgram)
    start_server = websockets.serve(lambda ws, path: handle_audio(ws, path, deepgram_session), "localhost", 8765)
    await start_server
    await asyncio.Future()  # Run forever

asyncio.run(main())
