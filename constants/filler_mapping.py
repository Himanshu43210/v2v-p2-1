import pyaudio
import wave
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# Assume data is in this format: a list of (sentence, intent) tuples
data = [
    ("What products do you offer?", "well.wav"),
    ("Tell me more about Product X.", "okay.wav"),
    ("How much does Product Y cost?", "uh.wav"),
    ("Do you have any discounts?", "actually.wav"),
    ("How can I purchase Product Z?", "um.wav"),
    ("Where are you located?", "uh.wav"),
    ("When will my order be delivered?", "hm_hm.wav"),
    ("What is your return policy?", "well.wav"),
    ("Can I get a refund?", "um.wav"),
    ("Do you offer customer support?", "yes.wav"),
    ("How do I contact customer service?", "yeah.wav"),
    ("Do you have any reviews or testimonials?", "gotcha.wav"),
    ("How do I create an account?", "alright.wav"),
    ("I forgot my password, what do I do?", "um.wav"),
    ("Can I change my delivery address?", "actually.wav"),
    ("What payment methods do you accept?", "well.wav"),
    ("Is my personal information secure?", "yes.wav"),
    ("What are the benefits of Product A over Product B?", "uh_alright.wav"),
    ("How do I cancel my order?", "um.wav"),
    ("Can I speak with a sales representative?", "yes.wav"),
]

# Split data into sentences and labels, then into training and test sets
sentences, labels = zip(*data)
X_train, X_test, y_train, y_test = train_test_split(
    sentences, labels, test_size=0.2, random_state=42
)

# Create a pipeline with a TF-IDF vectorizer and a logistic regression classifier
pipeline = Pipeline([("tfidf", TfidfVectorizer()), ("clf", LogisticRegression())])


def refresh_learning_data():
    # Train the model
    pipeline.fit(X_train, y_train)
    # Save the model to a file
    joblib.dump(pipeline, "intent_classifier.pkl")


def play_audio(filename):
    # Set up PyAudio
    p = pyaudio.PyAudio()
    # Open the wave file
    wf = wave.open(filename, "rb")
    # Open a PyAudio stream
    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
    )
    # Play the audio file
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
    # Stop the PyAudio stream
    stream.stop_stream()
    stream.close()
    p.terminate()


def classify_and_play_audio(sentence):
    # Load the model from the file
    loaded_model = joblib.load("intent_classifier.pkl")
    # Classify a new sentence
    audio_file = loaded_model.predict([sentence])[0]
    # Path to the audio file
    # 

    audio_path = f"./assets/audio_fillers/{audio_file}"
    # Play the audio file
    play_audio(audio_path)


if __name__ == "__main__":
    refresh_learning_data()
    classify_and_play_audio("yeah I'm just")
