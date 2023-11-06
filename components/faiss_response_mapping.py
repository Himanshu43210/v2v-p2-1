from datetime import datetime
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv
import os
import sys

load_dotenv()

sys.path.append('./utils')
from mongo_db import MongoDB

# Access environment variables
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
CSV_FILE_PATH = os.environ.get('CSV_FILE_PATH')
MONGO_DB_URI = os.environ.get('MONGO_DB_URI')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')
MONGO_DB_COLLECTION = os.environ.get('MONGO_DB_COLLECTION')
MONGO_DB_COLLECTION_ENTRY = os.environ.get('MONGO_DB_COLLECTION_ENTRY')

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

mongo = MongoDB(MONGO_DB_URI, MONGO_DB_NAME) 

# Fetch the possible responses from MongoDB
collection = mongo.db[MONGO_DB_COLLECTION]
cursor = collection.find({})

given_responses = []
object_ids = []
for doc in cursor:
    given_responses.append(doc['response'])
    object_ids.append(str(doc['_id']))

vectorizer = TfidfVectorizer()
response_matrix = vectorizer.fit_transform(given_responses).toarray()

d = response_matrix.shape[1]

index = faiss.IndexFlatL2(d)
index.add(response_matrix.astype("float32"))

def find_most_similar(input_sentence):
    vectorized_sentence = vectorizer.transform([input_sentence]).toarray().astype("float32")
    distances, indices = index.search(vectorized_sentence, k=1)

    similarity_score = 1 / (1 + distances[0][0])

    return object_ids[indices[0][0]], similarity_score

def get_similar_response(input_sentence, conversation_id, query):
    start_time = datetime.now()

    matched_object_id, similarity_score = find_most_similar(input_sentence)

    matched_index = object_ids.index(matched_object_id)
    matched_response = given_responses[matched_index]

    end_time = datetime.now()
    time_taken = (end_time - start_time).total_seconds()  # Time taken in seconds

    # Construct the data to be added to MongoDB
    data_to_insert = {
        "conversation_id": conversation_id,
        "user": query,
        "input_text": input_sentence,
        "output_text": matched_response,
        "matched_object_id": matched_object_id,
        "similarity_score": similarity_score,
        "time_taken": time_taken,
        "time_stamp": str(end_time)
    }

    # Insert the data into the MONGO_DB_COLLECTION_ENTRY collection
    mongo.db[MONGO_DB_COLLECTION_ENTRY].insert_one(data_to_insert)

    return matched_object_id, matched_response
