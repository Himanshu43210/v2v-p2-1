import os
from pydub import AudioSegment
from transcribe import transcribe_stream  # Assuming your transcription code is in transcribe.py

def get_audio_chunks(file_path, chunk_length=8000):
    """Read an audio file and yield chunks of specified length."""
    audio = AudioSegment.from_file(file_path, format="wav")
    for i in range(0, len(audio), chunk_length):
        yield audio[i:i + chunk_length].raw_data

def test_transcription(file_path):
    audio_chunks = list(get_audio_chunks(file_path))
    transcript = transcribe_stream(audio_chunks)
    print("Transcription:", transcript)

# Test with an audio file
test_audio_file = "./assets/audio_files_pixel/01.wav"  # Replace with your audio file path
test_transcription(test_audio_file)
