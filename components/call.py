import pyautogui as pg
import time
import webbrowser
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
MONGO_URI = os.environ.get('MONGO_DB_URI')  # Your MongoDB connection string
client = MongoClient(MONGO_URI)
MONGO_DB_V2V = os.environ.get('MONGO_DB_V2V')
MONGO_DB_V2V_COLLECTION = os.environ.get('MONGO_DB_V2V_COLLECTION')

db_v2v = client[MONGO_DB_V2V]
collection_v2v = db_v2v[MONGO_DB_V2V_COLLECTION]

def get_number_to_call():
    # Fetch the document with status 'submitted'
    document = collection_v2v.find_one({'Status': 'submitted'})
    if document:
        return document['Phone no.'], document['_id']
    return None, None

def update_call_status(document_id, status):
    collection_v2v.update_one({'_id': document_id}, {'$set': {'Status': status}})

def make_call():
    number, doc_id = get_number_to_call()
    if not number:
        print("No number with status 'submitted' found!")
        return

    # Update status to 'processing'
    update_call_status(doc_id, 'processing')

    def open_website(url):
        webbrowser.open(url, new=2)  # new=2 opens in a new tab, if possible

    website = 'https://dialer.callhippo.com/dial'
    open_website(website)

    time.sleep(15)

    pg.click(977, 316) ## cick on dialer pad
    pg.press('backspace')
    pg.press('backspace')
    pg.press('backspace')
    pg.write(number)
    print("Number typed")
    time.sleep(2)
    pg.press('enter')
    print('calling', {number})

    # Assuming there's a set time for the call to be picked up
    time.sleep(2)

    return doc_id
    
