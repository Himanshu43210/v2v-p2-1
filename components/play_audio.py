from playsound import playsound

def play_audio_from_id(matched_object_id):
    filename = f"components/audio_files/{matched_object_id}.mp3"
    try:
        playsound(filename)
    except Exception as e:
        print(f"Error playing audio: {e}")

import random
import os
import threading
import pygame

def play_random_filler(folder_path='./components/fillers'):
    # Given list of fillers
    fillers = ["alright.mp3", "gotcha.mp3", "hm_hm.mp3", "okay!.mp3", "okay.mp3", "right.mp3", "yeah.mp3", "yes.mp3"]

    # Select a random filler
    chosen_filler = random.choice(fillers)

    # Play the chosen filler using pygame in a separate thread
    def play_sound(file_path):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue

    threading.Thread(target=play_sound, args=(os.path.join(folder_path, chosen_filler),)).start()
