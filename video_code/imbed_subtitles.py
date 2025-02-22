import os
import tkinter as tk
from tkinter import filedialog
import subprocess
import difflib

def get_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory(title="Select Folder")
    return folder_path

def find_files(folder_path):
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov')
    subtitle_extension = '.srt'
    video_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(video_extensions):
                video_files.append(os.path.join(root, file))

    return video_files

def find_subtitle(video_file):
    video_base = os.path.splitext(os.path.basename(video_file))[0]
    folder = os.path.dirname(video_file)

    best_match = None
    highest_similarity = 0

    for file in os.listdir(folder):
        if file.lower().endswith('.srt'):
            subtitle_base = os.path.splitext(file)[0]
            similarity = difflib.SequenceMatcher(None, video_base, subtitle_base).ratio()
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = os.path.join(folder, file)

    return best_match if highest_similarity > 0.5 else None

def embed_subtitles(video_files):
    for video_file in video_files:
        subtitle_file = find_subtitle(video_file)

        if subtitle_file:
            output_file = video_file.replace(os.path.splitext(video_file)[1], '_subtitled' + os.path.splitext(video_file)[1])
            command = f'ffmpeg -i "{video_file}" -vf "subtitles={subtitle_file}" "{output_file}"'
            subprocess.call(command, shell=True)
            print(f'Successfully embedded subtitles in: {output_file}')
        else:
            print(f'No matching subtitle file found for: {video_file}')

if __name__ == "__main__":
    folder_path = get_folder()
    if folder_path:
        video_files = find_files(folder_path)
        embed_subtitles(video_files)
    else:
        print("No folder selected")
