#### UDP
import socket
import asyncio
import socket
import os
import uuid
import datetime
import numpy as np
import faiss
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from dotenv import load_dotenv
import asyncio
import openai

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

model_name="llama-2-70b-chat"

sys.path.append("./components")
sys.path.append("./constants")
# import speech_to_text
from dictionary import phrases_dict
from speech_to_text import Transcriber

def generate_unique_id():
    return str(uuid.uuid4())

conversation_id = generate_unique_id()

processed_sentences = set()

# 1. FAISS Indexing
# Convert phrases to embeddings for searching
vectorizer = TfidfVectorizer().fit(phrases_dict.keys())
phrases_embeddings = vectorizer.transform(phrases_dict.keys())
index = faiss.IndexIDMap(faiss.IndexFlatIP(phrases_embeddings.shape[1]))
index.add_with_ids(np.array(phrases_embeddings.toarray(), dtype=np.float32), np.array(list(range(len(phrases_dict)))))

def send_audio_file_udp(file_path, client_address, server_socket):
    # Read the audio file in chunks
    with open(file_path, "rb") as f:
        while True:
            audio_data = f.read(1024)  # Read 1024 bytes of the file
            if not audio_data:
                break  # If file has ended, stop sending
            server_socket.sendto(audio_data, client_address)  # Send the audio chunk to the client

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

def handle_gpt_response(full_content, addr, server_socket):
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
                print('Sending Audio to client: ', datetime.datetime.now())
                send_audio_file_udp(audio_path, addr, server_socket)
            # Mark sentence as processed
            processed_sentences.add(sentence)
 

async def chat_with_user_udp(addr, server_socket):
    print(f"Connected by {addr}")
    messages = [
        {
            "role": "system",
            "content": (
                "Name: Jacob. Hospital Name: Health Care Hospital. Task: Appointment Booking. Appointment Type: Check-up, Consultation, Follow-up. Objective: First ask for name and contact number and then book the appointment for the patient as per his convenience. Discuss Medical Concern/Health issues and any other issues. Hospital/Clinic visit. Agree?  Preferred Date and Time. Details given? Confirm detail: Appointment Details and availability. End: Great day. You are Jacob. Only respond to the last query in short."
            ),
        }
    ]

    processed_content = ""
    sentence_end_pattern = re.compile(r'(?<=[.?!])\s')
   
    while True:
        server_socket.sendto(b'END_OF_FILE', addr)
        audio_chunk, addr = server_socket.recvfrom(4096)  # buffer size is 4096 bytes
        print(f"Received message from {addr}")

        transcriber = Transcriber()  # Create a new Transcriber instance for each transcription cycle
        transcription_task = asyncio.create_task(transcriber.run(DEEPGRAM_API_KEY))
        await transcriber.audio_queue.put(audio_chunk)  # Put the received audio chunk into the transcriber's queue

        # Now wait for the transcription to complete
        transcript = await transcription_task
        if transcript.lower() == "exit":
            print(f"Exiting as requested by the client {addr}")
            break
        query = transcript
        server_socket.sendto(b'transcription done', addr)
        print(f"Sent 'transcription done' message to {addr}")

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
                        handle_gpt_response(part + '.', addr, server_socket)  # Re-add the punctuation for processing
                        processed_content += part + ' '  # Add the processed part to processed_content

                # Now handle the last part separately
                last_part = parts[-1].strip()
                if last_part:
                    # If the last part ends with a punctuation, process it directly
                    if sentence_end_pattern.search(last_part):
                        handle_gpt_response(last_part, addr, server_socket)
                        processed_content += last_part + ' '
                    else:
                        # Otherwise, add it to the sentence buffer to process it later
                        processed_content += last_part + ' '
    
        # Append only the complete assistant's response to messages
        if content.strip():
            messages.append({"role": "assistant", "content": content.strip()})
        
async def server_program_udp():
    host = '0.0.0.0'  # Use your host
    port = 65432  # Use your port

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Notice SOCK_DGRAM for UDP
    server_socket.bind((host, port))

    print(f"Server listening on {host}:{port} (UDP)")

    while True:
        try:
            # Since UDP is connectionless, we don't accept connections. We directly receive data from any address
            data, addr = server_socket.recvfrom(4096)  # buffer size is 4096 bytes
            print(f"Received message from {addr}")
            await chat_with_user_udp(addr, server_socket)
        except Exception as e:
            print(f"An error occurred: {e}")

# Modify the entry point to run the async server program
if __name__ == '__main__':
    asyncio.run(server_program_udp())
