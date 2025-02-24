import os
import subprocess
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Define the download folder
DOWNLOAD_FOLDER = os.path.expanduser("~/downloaded_videos")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def run_command(command):
    """Runs a shell command and captures the output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout

def normalize_resolution(resolution):
    """Convert different resolution formats into a standard format (e.g., 1920x1080 → 1080p)."""
    resolution_map = {
        "1920x1080": "1080p",
        "1280x720": "720p",
        "854x480": "480p",
        "640x480": "480p",
        "426x240": "240p",
        "2560x1440": "1440p",
        "3840x2160": "2160p"
    }
    return resolution_map.get(resolution, resolution)  # Defaults to itself if not found

def get_video_formats(url):
    """Fetch available video formats with both video and audio streams."""
    output = run_command(f'yt-dlp -F "{url}"')
    
    format_dict = {}
    resolutions_seen = set()

    # First, find the best audio format
    audio_format = None
    for line in output.split("\n"):
        if "audio only" in line.lower():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 2:
                audio_format = parts[0]
                break

    # Then find video formats
    for line in output.split("\n"):
        if "mp4" in line.lower() and "video only" in line.lower():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 3:
                format_id = parts[0]
                resolution = normalize_resolution(parts[2])

                if resolution not in resolutions_seen:
                    resolutions_seen.add(resolution)
                    # Store both video and audio format IDs
                    format_dict[resolution] = f"{format_id}+{audio_format}"

    return format_dict

def fetch_formats():
    """Fetch formats with a progress bar."""
    global format_dict

    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a valid YouTube URL.")
        return
    
    format_listbox.delete(0, tk.END)
    progress_bar.start(10)  # Start loading animation

    def fetch():
        global format_dict
        format_dict = get_video_formats(url)
        progress_bar.stop()  # Stop loading animation

        if not format_dict:
            messagebox.showerror("Error", "No suitable formats found!")
            return

        for resolution in format_dict.keys():
            format_listbox.insert(tk.END, resolution)

    threading.Thread(target=fetch, daemon=True).start()

def download_video(is_audio):
    """Downloads the selected video format with a loading bar."""
    url = url_entry.get().strip()
    selected_idx = format_listbox.curselection()
    
    if not url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return
    if not selected_idx:
        messagebox.showerror("Error", "Please select a format.")
        return

    selected_resolution = format_listbox.get(selected_idx[0])
    format_code = format_dict[selected_resolution]

    progress_bar.start(10)  # Start loading animation

    def download():
        progress_label.config(text="Downloading... Please wait")
        if is_audio:
            command = f'yt-dlp -f {format_code} -x --audio-format mp3 -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'
        else:
            # Use format-sort to prefer MP4 container and better codecs
            command = f'yt-dlp -f {format_code} --merge-output-format mp4 -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'

        os.system(command)
        progress_bar.stop()  # Stop loading animation
        progress_label.config(text="Download Complete!")
        messagebox.showinfo("Success", "Download completed successfully!")

    threading.Thread(target=download, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("450x400")

# URL Entry
tk.Label(root, text="YouTube URL:").pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack()

# Fetch Formats Button
fetch_button = tk.Button(root, text="Fetch Formats", command=fetch_formats)
fetch_button.pack(pady=5)

# Listbox for formats
tk.Label(root, text="Select a format:").pack(pady=5)
format_listbox = tk.Listbox(root, height=10)
format_listbox.pack()

# Progress Bar
progress_label = tk.Label(root, text="")
progress_label.pack()
progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
progress_bar.pack(pady=5)

# Buttons for MP4 & MP3
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

mp4_button = tk.Button(btn_frame, text="Download MP4", command=lambda: download_video(False), bg="lightblue")
mp4_button.pack(side=tk.LEFT, padx=10)

mp3_button = tk.Button(btn_frame, text="Download MP3", command=lambda: download_video(True), bg="lightgreen")
mp3_button.pack(side=tk.RIGHT, padx=10)

# Run GUI
root.mainloop()