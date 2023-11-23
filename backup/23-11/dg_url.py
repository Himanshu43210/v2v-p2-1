
# # # # import asyncio
# # # # import aiohttp
# # # # from deepgram import Deepgram

# # # # # Initialize the Deepgram SDK
# # # # DEEPGRAM_API_KEY = 'your_deepgram_api_key'
# # # # deepgram = Deepgram(DEEPGRAM_API_KEY)

# # # # # URL of the local audio stream
# # # # URL = 'http://localhost:8000/path_to_your_audio_stream'

# # # # async def transcribe():
# # # #     # Create a live transcription object
# # # #     try:
# # # #         deepgramLive = await deepgram.transcription.live({'punctuate': True, 'interim_results': True, 'language': 'en-US'})
# # # #     except Exception as e:
# # # #         print(f'Could not open socket: {e}')
# # # #         return

# # # #     # Register handler for receiving transcripts
# # # #     deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print)
# # # #     deepgramLive.send(await audio.content.readany())

# # # #     async with aiohttp.ClientSession() as session:
# # # #         async with session.get(URL) as audio:
# # # #             while True:
# # # #                 deepgramLive.send(await audio.content.readany())

            
# # # import asyncio
# # # import aiohttp
# # # from deepgram import Deepgram

# # # # Initialize the Deepgram SDK
# # # # DEEPGRAM_API_KEY = 'your_deepgram_api_key'

# # # import os
# # # from dotenv import load_dotenv
# # # import openai

# # # # Load environment variables from .env file
# # # load_dotenv()

# # # # Access environment variables
# # # PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
# # # os.environ["PPLX_API_KEY"] = PPLX_API_KEY
# # # DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# # # deepgram = Deepgram(DEEPGRAM_API_KEY)

# # # # URL of your local audio stream
# # # # URL = 'http://localhost:your_port/your_audio_stream'
# # # # file:///E:/v2v-p2-1-20-11/index.html
# # # # URL = 'http://localhost:8000/file:///E:/v2v-p2-1-20-11/index.html'
# # # # URL = "http://127.0.0.1:5500"
# # # URL = "https://www.ndtv.com/video/live/channel/ndtv24x7"

# # # async def transcribe():
# # #     try:
# # #         # Create a live transcription object
# # #         deepgramLive = await deepgram.transcription.live({'punctuate': True, 'interim_results': True, 'language': 'en-US'})

# # #         # Register handler for receiving transcripts
# # #         deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print)

# # #         # Register handler for connection close
# # #         deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))

# # #         # Fetch and stream the audio
# # #         async with aiohttp.ClientSession() as session:
# # #             async with session.get(URL) as audio:
# # #                 while True:
# # #                     data = await audio.content.readany()
# # #                     if not data:
# # #                         break
# # #                     await deepgramLive.send(data)

# # #         # Finish the transcription session
# # #         await deepgramLive.finish()

# # #     except Exception as e:
# # #         print(f'An error occurred: {e}')

# # # # Run the transcription
# # # asyncio.run(transcribe())

# # import aiohttp
# # import asyncio
# # from deepgram import Deepgram


# # import os
# # from dotenv import load_dotenv
# # import openai

# # # Load environment variables from .env file
# # load_dotenv()

# # DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# # if not DEEPGRAM_API_KEY:
# #     raise ValueError("Deepgram API key is missing.")
# # deepgram = Deepgram(DEEPGRAM_API_KEY)
# # # DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# # # deepgram = Deepgram(DEEPGRAM_API_KEY)
# # # # Initialize Deepgram SDK
# # # DEEPGRAM_API_KEY = 'your_deepgram_api_key'
# # # deepgram = Deepgram(DEEPGRAM_API_KEY)

# # # URL of your audio stream
# # URL = "https://www.ndtv.com/video/live/channel/ndtv24x7"

# # async def transcribe():
# #     try:
# #         # Create a live transcription object
# #         deepgramLive = await deepgram.transcription.live({'punctuate': True, 'interim_results': True, 'language': 'en-GB'})

# #         # Register event handlers
# #         deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
# #         deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print)

# #         # Connect to the audio source and send audio to Deepgram
# #         async with aiohttp.ClientSession() as session:
# #             async with session.get(URL) as audio:
# #                 while True:
# #                     data = await audio.content.readany()
# #                     if not data:
# #                         break
# #                     await deepgramLive.send(data)

# #         # Close the connection
# #         await deepgramLive.finish()

# #     except Exception as e:
# #         print(f'Could not open socket: {e}')

# # # Run the transcription
# # asyncio.run(transcribe())


# import asyncio
# import websockets
# import aiohttp
# import os
# import os
# from dotenv import load_dotenv


# # Load environment variables from .env file
# load_dotenv()

# async def stream_audio_to_deepgram(url, deepgram_url, key):
#     async with websockets.connect(
#         deepgram_url, 
#         extra_headers={"Authorization": "Token {}".format(key)}
#     ) as ws:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 while True:
#                     data = await response.content.read(8000)  # Read chunks of audio
#                     if not data:
#                         break
#                     await ws.send(data)
#                     # Here you would also handle incoming transcription results

# def transcribe_stream_from_url():
#     DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
#     if DEEPGRAM_API_KEY is None:
#         print("Please set the DEEPGRAM_API_KEY environment variable.")
#         return

#     URL = "https://www.ndtv.com/video/live/channel/ndtv24x7"
#     deepgram_url = "wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000"

#     loop = asyncio.get_event_loop()
#     transcript = loop.run_until_complete(stream_audio_to_deepgram(URL, deepgram_url, DEEPGRAM_API_KEY))
#     return transcript

# transcribe_stream_from_url()


from deepgram import Deepgram
import asyncio
import aiohttp
import time

import os
from dotenv import load_dotenv
# import openai

# # Load environment variables from .env file
load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise ValueError("Deepgram API key is missing.")

# Your personal API key
# DEEPGRAM_API_KEY = '🔑🔑🔑 Your API Key here! 🔑🔑🔑'

# URL for the real-time streaming audio you would like to transcribe
URL = 'https://www.ndtv.com/video/live/channel/ndtv24x7'

# Fill in these parameters to adjust the output as you wish!
# See our docs for more info: https://developers.deepgram.com/documentation/ 
PARAMS = {"punctuate": True, 
          "numerals": True,
          "model": "general", 
          "language": "en-US",
          "tier": "enhanced" }

# The number of *seconds* you wish to transcribe the livestream.
# Set this equal to `float(inf)` if you wish to stream forever.
# (Or at least until you wish to cut off the function manually.)
TIME_LIMIT = 10

# Set this variable to `True` if you wish only to 
# see the transcribed words, like closed captions. 
# Set it to `False` if you wish to see the raw JSON responses.
TRANSCRIPT_ONLY = True

'''
Function object.

Input: JSON data sent by a live transcription instance, which is named 
`deepgramLive` in main().

Output: The printed transcript obtained from the JSON object
'''
# def print_transcript(json_data):
#     try:
#       print(json_data['channel']['alternatives'][0]['transcript'])
#     except KeyError:
#       print()

def print_transcript(json_data):
    try:
        print(json_data['channel']['alternatives'][0]['transcript'])
    except KeyError as e:
        print("Error in JSON response:", e)
        print("Full JSON response:", json_data)

async def main():
    start = time.time()
    # Initializes the Deepgram SDK
    deepgram = Deepgram(DEEPGRAM_API_KEY)
    # Create a websocket connection to Deepgram
    try:
        deepgramLive = await deepgram.transcription.live(PARAMS)
    except Exception as e:
        print(f'Could not open socket: {e}')
        return

    # Listen for the connection to close
    deepgramLive.registerHandler(deepgramLive.event.CLOSE, 
                                 lambda _: print('✅ Transcription complete! Connection closed. ✅'))

    # Listen for any transcripts received from Deepgram & write them to the console
    if TRANSCRIPT_ONLY:
        deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, 
                                  print_transcript)
    else:
        deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, print)

    # Listen for the connection to open and send streaming audio from the URL to Deepgram
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as audio:
            while time.time() - start < TIME_LIMIT:
                data = await audio.content.readany()
                if data:
                    deepgramLive.send(data)
                else:
                    break

    # Indicate that we've finished sending data by sending the customary 
    # zero-byte message to the Deepgram streaming endpoint, and wait 
    # until we get back the final summary metadata object
    await deepgramLive.finish()

# trans = await main()
if __name__ == "__main__":
    asyncio.run(main())