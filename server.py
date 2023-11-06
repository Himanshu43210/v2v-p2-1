
import socket
import asyncio
import websockets
import json
import socket
import pyaudio
import os
import json
import uuid
import datetime
import numpy as np
import faiss
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import sounddevice as sd
import soundfile as sf
import wavio
import re
from dotenv import load_dotenv
import asyncio
import time
import openai

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY

model_name="llama-2-70b-chat"

sys.path.append("./components")
sys.path.append("./constants")
# import speech_to_text
from speech_to_text import transcribe_socket
from dictionary import phrases_dict

def generate_unique_id():
    return str(uuid.uuid4())

conversation_id = generate_unique_id()
# 1. FAISS Indexing
# Convert phrases to embeddings for searching
vectorizer = TfidfVectorizer().fit(phrases_dict.keys())
phrases_embeddings = vectorizer.transform(phrases_dict.keys())
index = faiss.IndexIDMap(faiss.IndexFlatIP(phrases_embeddings.shape[1]))
index.add_with_ids(np.array(phrases_embeddings.toarray(), dtype=np.float32), np.array(list(range(len(phrases_dict)))))

def find_matching_audio(sentence):
    start_time_f = datetime.datetime.now()
    print(f'Phrase given to faiss {start_time_f}')
    # Convert the sentence to embedding and search in the index
    sentence_embedding = vectorizer.transform([sentence]).toarray().astype(np.float32)
    D, I = index.search(sentence_embedding, 1)
    match_index = I[0][0]
    matching_sentence = list(phrases_dict.keys())[match_index]

    end_time_f = datetime.datetime.now()
    print('Faiss answer fetched: ', end_time_f)
    elapsed_time_f = (end_time_f - start_time_f).total_seconds()

    # # Print the elapsed time
    print(f"Time taken by Faiss to fetch similar answer: {elapsed_time_f:.6f} seconds")
    
    if D[0][0] > 0.1:  # You can adjust this threshold based on desired accuracy
        return phrases_dict[matching_sentence]
    return None

processed_sentences = set()

def handle_gpt_response(full_content):
    # Split content into sentences
    sentences = re.split(r'[.!?]', full_content)
    # print(f'Sentence split: {datetime.datetime.now()}')
    sentences = [s.strip() for s in sentences if s]

    for sentence in sentences:
        # Check if sentence was already processed
        if sentence not in processed_sentences:
            audio_code = find_matching_audio(sentence)
            if audio_code:
                audio_path = f"./assets/audio_files_pixel/{audio_code}.wav"
                print('Before Audio: ', datetime.datetime.now())
                wav_obj = wavio.read(audio_path)
                sd.play(wav_obj.data, samplerate=wav_obj.rate)
                print('Audio playing started: ', datetime.datetime.now())
                sd.wait()
            # Mark sentence as processed
            processed_sentences.add(sentence)


# Define PyAudio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024
p = pyaudio.PyAudio()

# Deepgram API credentials
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

# Ensure the API key is available
if not DEEPGRAM_API_KEY:
    raise ValueError("The Deepgram API key is not set in the environment variables.")

# Define the Deepgram WebSocket URL with query parameters for transcription options
DEEPGRAM_URL = f"wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=44100"

async def transcribe_socket(conn):
    async with websockets.connect(
        DEEPGRAM_URL,
        extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        ping_timeout=None,
    ) as dg_websocket:

        async def send_audio_from_socket():
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                await dg_websocket.send(data)
            await dg_websocket.send(b'')

        async def receive_transcriptions():
            full_transcript = ''
            try:
                async for message in dg_websocket:
                    data = json.loads(message)
                    if 'channel' in data:
                        transcript = data['channel']['alternatives'][0]['transcript']
                        if transcript:
                            full_transcript += transcript
                            print("Transcript:", transcript)
                        else:
                            print("Received an empty transcript - the audio might not be recognized.")
            except websockets.exceptions.ConnectionClosedOK:
                pass  # Connection was closed cleanly
            return full_transcript

        sender_task = asyncio.create_task(send_audio_from_socket())
        receiver_task = asyncio.create_task(receive_transcriptions())

        await sender_task
        return await receiver_task

# Modify the chat_with_user function to work asynchronously
async def chat_with_user(conn, addr):
    print(f"Connected by {addr}")
    messages = [
        {
            "role": "system",
            "content": (
                "Agent: Jacob. Company: Gadget Hub. Task: Demo. Product: Google Pixel. Features: Night Sight, Portrait Mode, Astrophotography, Super Res Zoom, video stabilization. Battery: All-day. Objective: Google Pixel over iPhone. Discuss features. Interest? Shop visit. Agree? Name, contact. Address inquiries. Details given? End: great day.you are Jacob. Only respond to the last query in short."
            ),
        }
    ]
    audio_path = "./assets/audio_files_pixel/Intro.wav"
    data, samplerate = sf.read(audio_path)
    sd.play(data, samplerate)    
    sd.wait()
    processed_content = ""
    sentence_end_pattern = re.compile(r'(?<=[.?!])\s')
    
    try:

        while True:
        # Start the transcription coroutine
            transcript = await transcribe_socket(conn)
            print(transcript)
            query=transcript

            if query.lower() == "exit":
                break

            messages.append({"role": "user", "content": query})
            
            start_time = datetime.datetime.now()
            print('Before gpt: ', start_time)
            
            # Chat completion with streaming
            response_stream = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                api_base="https://api.perplexity.ai",
                api_key=PPLX_API_KEY,
                stream=True,
            )

            for response in response_stream:
                if 'choices' in response:
                    content = response['choices'][0]['message']['content']
                    new_content = content.replace(processed_content, "", 1).strip()  # Remove already processed content
                    elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
                    print('gpt answer received: ', datetime.datetime.now())
                    print(new_content)

                    # Split the content by sentence-ending punctuations
                    parts = sentence_end_pattern.split(new_content)

                    # Process each part that ends with a sentence-ending punctuation
                    for part in parts[:-1]:  # Exclude the last part for now
                        part = part.strip()
                        if part:
                            handle_gpt_response(part + '.')  # Re-add the punctuation for processing
                            processed_content += part + ' '  # Add the processed part to processed_content

                    # Now handle the last part separately
                    last_part = parts[-1].strip()
                    if last_part:
                        # If the last part ends with a punctuation, process it directly
                        if sentence_end_pattern.search(last_part):
                            handle_gpt_response(last_part)
                            processed_content += last_part + ' '
                        else:
                            # Otherwise, add it to the sentence buffer to process it later
                            processed_content += last_part + ' '

            # Append only the complete assistant's response to messages
            if content.strip():
                messages.append({"role": "assistant", "content": content.strip()})


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print(f"Disconnected {addr}")

# Modify the server_program function to handle async calls
async def server_program():
    host = '127.0.0.1'
    port = 65432

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Server listening on {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        await chat_with_user(conn, addr)

# Modify the entry point to run the async server program
if __name__ == '__main__':
    asyncio.run(server_program())
