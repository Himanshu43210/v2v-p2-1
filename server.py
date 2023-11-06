import socket
import wave
import pyaudio
import threading
import os
import json
import uuid
import datetime
import numpy as np
import faiss
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import sounddevice as sd
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

# FAISS Indexing
# Convert phrases to embeddings for searching
vectorizer = TfidfVectorizer().fit(phrases_dict.keys())
phrases_embeddings = vectorizer.transform(phrases_dict.keys())
index = faiss.IndexIDMap(faiss.IndexFlatIP(phrases_embeddings.shape[1]))
index.add_with_ids(
    np.array(phrases_embeddings.toarray(), dtype=np.float32), 
    np.array(list(range(len(phrases_dict))))
)

# Define the function to find matching audio
def find_matching_audio(sentence):
    sentence_embedding = vectorizer.transform([sentence]).toarray().astype(np.float32)
    D, I = index.search(sentence_embedding, 1)
    match_index = I[0][0]
    matching_sentence = list(phrases_dict.keys())[match_index]
    
    if D[0][0] > 0.1:
        return phrases_dict[matching_sentence]
    return None

# Define PyAudio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024
p = pyaudio.PyAudio()
        
def chat_with_user(conn, addr):
    print(f"Connected by {addr}")

    messages = [
        {
            "role": "system",
            "content": (
                "Agent: Jacob. Company: Gadget Hub. Task: Demo. Product: Google Pixel. Features: Night Sight, Portrait Mode, Astrophotography, Super Res Zoom, video stabilization. Battery: All-day. Objective: Google Pixel over iPhone. Discuss features. Interest? Shop visit. Agree? Name, contact. Address inquiries. Details given? End: great day.you are Jacob. Only respond to the last query in short."
            ),
        }
    ]
    processed_content = ""
    sentence_end_pattern = re.compile(r'(?<=[.?!])\s')
    reception_window = 5  
    try:
        frames = []
        start_time = time.time()
        while True:
            # Check if the time window has elapsed
            if time.time() - start_time > reception_window:
                print('Done receiving -- time window elapsed')
                break
            
            conn.settimeout(reception_window - (time.time() - start_time))  # Update the socket timeout
            
            try:
                data = conn.recv(CHUNK_SIZE)
                if not data:
                    print('Done receiving -- no more data')
                    break
                frames.append(data)
                print(f"Received a chunk of data from {addr}")
            except socket.timeout:
                # If no data is received and the timeout occurs
                print('Done receiving -- socket timeout')
                break

            
            print('Done receiving')
            # Process the received text
            query = transcribe_socket(conn) 
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

            # Optionally, you can send back a confirmation or response
            response = "Text received and processed."
            conn.sendall(response.encode('utf-8'))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print(f"Disconnected {addr}")

# Define server program
# Modify the server_program function to handle async calls
def server_program():
    host = '127.0.0.1'
    port = 65432

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Server listening on {host}:{port}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            conn, addr = server_socket.accept()
            loop.run_until_complete(chat_with_user(conn, addr))
    except KeyboardInterrupt:
        print("Server is closing...")
    finally:
        server_socket.close()
        loop.close()

if __name__ == '__main__':
    server_program()
