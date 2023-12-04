# Connection through websockets
import asyncio
import websockets
import json
import os
import uuid
import datetime
import numpy as np
import faiss
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
os.environ["PPLX_API_KEY"] = PPLX_API_KEY
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

model_name = "llama-2-70b-chat"

sys.path.append("./components")
sys.path.append("./constants")
from dictionary import phrases_dict
from speech_to_text_audio import Transcriber


def generate_unique_id():
    return str(uuid.uuid4())


conversation_id = generate_unique_id()
processed_sentences = set()


vectorizer = TfidfVectorizer().fit(phrases_dict.keys())
phrases_embeddings = vectorizer.transform(phrases_dict.keys())
index = faiss.IndexIDMap(faiss.IndexFlatIP(phrases_embeddings.shape[1]))
index.add_with_ids(
    np.array(phrases_embeddings.toarray(), dtype=np.float32),
    np.array(list(range(len(phrases_dict)))),
)

def find_matching_audio(sentence):
    start_time_f = datetime.datetime.now()
    print(f'Phrase given to faiss {start_time_f}')
    # Convert the sentence to embedding and search in the index
    sentence_embedding = vectorizer.transform([sentence]).toarray().astype(np.float32)
    D, I = index.search(sentence_embedding, 1)
    match_index = I[0][0]
    matching_sentence = list(phrases_dict.keys())[match_index]
    print(f'Matching sentence: {matching_sentence}')

    end_time_f = datetime.datetime.now()
    print('Faiss answer fetched: ', end_time_f)
    elapsed_time_f = (end_time_f - start_time_f).total_seconds()

    # # Print the elapsed time
    print(f"Time taken by Faiss to fetch similar answer: {elapsed_time_f:.6f} seconds")
    
    if D[0][0] > 0.1:  # You can adjust this threshold based on desired accuracy
        return phrases_dict[matching_sentence]
    return None


import logging
import re

async def send_audio_file_websocket(file_path, websocket):
    try:
        with open(file_path, "rb") as audio_file:
            while True:
                audio_data = audio_file.read(1024)
                if not audio_data:
                    break
                await websocket.send(audio_data)
        await websocket.send(b"END_OF_FILE")
        logging.info(f"Sent audio file: {file_path}")
    except FileNotFoundError:
        logging.error(f"Audio file not found: {file_path}")
    except Exception as e:
        logging.error(f"Error sending audio file: {e}")

async def handle_gpt_response(full_content, websocket, processed_sentences):
    sentences = re.split(r"[.!?]", full_content)
    sentences = [s.strip() for s in sentences if s]

    for sentence in sentences:
        if sentence not in processed_sentences:
            audio_code = find_matching_audio(sentence)
            if audio_code:
                audio_path = f"./assets/audio_files_pixel/{audio_code}.wav"
                await send_audio_file_websocket(audio_path, websocket)
            processed_sentences.add(sentence)

async def chat_with_user_websocket(websocket, path):
    print(f"Connected with a client")
    messages = [
        {
            "role": "system",
            "content": ("Name: Jacob. Hospital Name: Health Care Hospital. Task: Appointment Booking. Appointment Type: Check-up, Consultation, Follow-up. Objective: First ask for name and contact number and then book the appointment for the patient as per his convenience. Discuss Medical Concern/Health issues and any other issues. Hospital/Clinic visit. Agree?  Preferred Date and Time. Details given? Confirm detail: Appointment Details and availability. End: Great day. You are Jacob. Only respond to the last query in short."),
        }
    ]

    processed_content = ""
    sentence_end_pattern = re.compile(r"(?<=[.?!])\s")

   
    transcriber = Transcriber()
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    if DEEPGRAM_API_KEY is None:
        print("Please set the DEEPGRAM_API_KEY environment variable.")
        return

    # Start the transcription process
    transcription_task = asyncio.create_task(transcriber.run(DEEPGRAM_API_KEY))

    while True:
        try:
            # async for message in websocket:
            #     # if isinstance(message, bytes):
            #     #     # Directly handle binary audio data
            #     #     await transcriber.add_audio_chunk(message)
            #     # else:
            #     #     # Process text-based messages as before
            #     #     data = json.loads(message)
            #     # data = json.loads(message)
            #     if isinstance(message, bytes):
            #         # Directly handle binary audio data
            #         await transcriber.add_audio_chunk(message)
            #     else:
            #         # Process text-based messages
            #         data = json.loads(message)

            #         if "audio" in data:
            #             # Handle text-based audio data (if needed)
            #             audio_chunk = data["audio"]
            #             # Add the audio chunk to the transcriber's queue
            #             await transcriber.add_audio_chunk(audio_chunk)

            #         # Additional text-based message handling (if needed)
            #         # ...
            #     # if "audio" in data:
            #     #     # Handle audio data
            #     #     audio_chunk = data["audio"]
            #     #     # Add the audio chunk to the transcriber's queue
            #     #     await transcriber.add_audio_chunk(audio_chunk)
            #     transcript = await transcription_task
         
            message = await websocket.recv()
            if isinstance(message, bytes):
                # Directly handle binary audio data
                await transcriber.add_audio_chunk(message)
            else:
                print("Non-audio message received:", message)

            if message == b"END_OF_FILE":
                print("End of audio file received, starting transcription.")
                transcript = await transcriber.run(DEEPGRAM_API_KEY)
                print("Transcription:", transcript)
                # break
                # print("Transcription:", transcript)
                if transcript.lower() == "exit":
                    print("Exiting as requested by the client")
                    break
                query = transcript
                print(query)
                await websocket.send(json.dumps({"status": "transcription done"}))
                messages.append({"role": "user", "content": query})

                # Chat completion with GPT-3
                start_time = datetime.datetime.now()
                print("Before GPT: ", start_time)

                response_stream = openai.ChatCompletion.create(
                    model=model_name,
                    messages=messages,
                    api_base="https://api.perplexity.ai",
                    api_key=PPLX_API_KEY,
                    stream=True,
                )

                for response in response_stream:
                    if "choices" in response:
                        content = response["choices"][0]["message"]["content"]
                        new_content = content.replace(processed_content, "", 1).strip()
                        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
                        print("GPT-3 answer received: ", datetime.datetime.now())
                        # print(new_content)

                        parts = sentence_end_pattern.split(new_content)

                        # Process and send back the response
                        for part in parts[:-1]:  # Exclude the last part for now
                            part = part.strip()
                            if part:
                                await handle_gpt_response(part + '.', websocket, processed_sentences)
                                processed_content += part + ' '
                        
                        last_part = parts[-1].strip()
                        if last_part:
                            # If the last part ends with a punctuation, process it directly
                            if sentence_end_pattern.search(last_part):
                                await handle_gpt_response(last_part, websocket, processed_sentences)
                                processed_content += last_part + " "
                            else:
                                processed_content += last_part + ' '

                        if content.strip():
                            messages.append({"role": "assistant", "content": content.strip()})
                            print("After GPT: ", datetime.datetime.now())
                            print("Elapsed time: ", elapsed_time)
                            print("Total time: ", (datetime.datetime.now() - start_time).total_seconds())
                            print("Total time: ", (datetime.datetime.now() - start_time).total_seconds() - elapsed_time)
                            print("Total time: ", (datetime.datetime.now() - start_time).total_seconds() - elapsed_time)
                if last_part:
                    print(f"Processed part sent to FAISS: '{last_part}'")
                    await handle_gpt_response(last_part, websocket, processed_sentences)
                    processed_content += last_part + ' '

                if content.strip():
                    messages.append({"role": "assistant", "content": content.strip()})

        except websockets.exceptions.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e.code} - {e.reason}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if not websocket.closed:
                print("Closing the WebSocket connection properly.")
                await websocket.close()
            # print("WebSocket connection closed properly.")


async def server_program_websocket():
    host = "0.0.0.0"
    port = 65432

    async with websockets.serve(chat_with_user_websocket, host, port):
        print(f"Server listening on {host}:{port} (WebSocket)")
        await asyncio.Future()  # This will keep the server running indefinitely


if __name__ == "__main__":
    asyncio.run(server_program_websocket())
