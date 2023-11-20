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
index.add_with_ids(
    np.array(phrases_embeddings.toarray(), dtype=np.float32),
    np.array(list(range(len(phrases_dict)))),
)


def find_matching_audio(sentence):
    start_time_f = datetime.datetime.now()
    print(f"Phrase given to faiss {start_time_f}")
    # Convert the sentence to embedding and search in the index
    sentence_embedding = vectorizer.transform([sentence]).toarray().astype(np.float32)
    D, I = index.search(sentence_embedding, 1)
    match_index = I[0][0]
    matching_sentence = list(phrases_dict.keys())[match_index]

    end_time_f = datetime.datetime.now()
    print("Faiss answer fetched: ", end_time_f)
    elapsed_time_f = (end_time_f - start_time_f).total_seconds()

    # # Print the elapsed time
    print(f"Time taken by Faiss to fetch similar answer: {elapsed_time_f:.6f} seconds")

    if D[0][0] > 0.1:  # You can adjust this threshold based on desired accuracy
        return phrases_dict[matching_sentence]
    return None


async def handle_gpt_response(full_content, websocket):
    sentences = re.split(r"[.!?]", full_content)
    sentences = [s.strip() for s in sentences if s]

    for sentence in sentences:
        if sentence not in processed_sentences:
            audio_code = find_matching_audio(sentence)
            if audio_code:
                audio_path = f"./assets/audio_files_pixel/{audio_code}.wav"
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_data = audio_file.read()
                        await websocket.send(audio_data)
                except FileNotFoundError:
                    print(f"Audio file not found: {audio_path}")
                except Exception as e:
                    print(f"Error sending audio file: {e}")
            processed_sentences.add(sentence)


async def chat_with_user_websocket(websocket, path):
    print(f"Connected with a client")
    messages = [
        {
            "role": "system",
            "content": ("Name: Jacob... (rest of the system message)"),
        }
    ]

    processed_content = ""
    sentence_end_pattern = re.compile(r"(?<=[.?!])\s")

    try:
        async for message in websocket:
            # Assuming the message is a JSON with 'text' and 'audio' fields
            data = json.loads(message)

            if "audio" in data:
                # Handle audio data
                audio_chunk = data["audio"]
                transcriber = Transcriber()
                transcription_task = asyncio.create_task(
                    transcriber.run(DEEPGRAM_API_KEY)
                )
                await transcriber.audio_queue.put(audio_chunk)

                transcript = await transcription_task
                if transcript.lower() == "exit":
                    print("Exiting as requested by the client")
                    break
                query = transcript
                await websocket.send(json.dumps({"status": "transcription done"}))
                messages.append({"role": "user", "content": query})

                # Chat completion with GPT-3
                start_time = datetime.datetime.now()
                print("Before GPT-3: ", start_time)

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
                        elapsed_time = (
                            datetime.datetime.now() - start_time
                        ).total_seconds()
                        print("GPT-3 answer received: ", datetime.datetime.now())
                        print(new_content)

                        # Process and send back the response
                        await websocket.send(json.dumps({"response": new_content}))

                        # Update processed content
                        processed_content += new_content + " "

                # Append only the complete assistant's response to messages
                if content.strip():
                    messages.append({"role": "assistant", "content": content.strip()})

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


async def server_program_websocket():
    host = "0.0.0.0"
    port = 65432

    async with websockets.serve(chat_with_user_websocket, host, port):
        print(f"Server listening on {host}:{port} (WebSocket)")
        await asyncio.Future()  # This will keep the server running indefinitely


if __name__ == "__main__":
    asyncio.run(server_program_websocket())
