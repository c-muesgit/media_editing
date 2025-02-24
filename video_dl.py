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

# Function to run shell commands
def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout

# Normalize video resolutions
def normalize_resolution(resolution):
    resolution_map = {
        "1920x1080": "1080p", "1280x720": "720p",
        "854x480": "480p", "640x480": "480p",
        "426x240": "240p", "2560x1440": "1440p",
        "3840x2160": "2160p"
    }
    return resolution_map.get(resolution, resolution)

# Fetch available formats
def get_formats(url):
    output = run_command(f'yt-dlp -F "{url}"')
    mp4_formats = {}

    for line in output.split("\n"):
        parts = re.split(r'\s+', line.strip())
        if len(parts) >= 3:
            format_id, ext, quality = parts[0], parts[1], parts[2]

            if ext == "mp4":
                resolution = normalize_resolution(quality)
                if resolution not in mp4_formats:
                    mp4_formats[resolution] = format_id  

    return mp4_formats

# Update format list based on selection
def update_format_list():
    """Shows format options only if 'MP4' is selected."""
    selected_option = format_choice.get()
    
    if selected_option == "MP4":
        format_listbox.pack(pady=5)
        format_label.pack(pady=5)
        fetch_formats_button.pack(pady=5)
    else:
        format_listbox.pack_forget()
        format_label.pack_forget()
        fetch_formats_button.pack_forget()

# Fetch MP4 formats
def fetch_formats():
    global mp4_dict

    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Enter a Video URL.")
        return

    format_listbox.delete(0, tk.END)
    progress_bar.start(10)

    def fetch():
        global mp4_dict
        mp4_dict = get_formats(url)
        progress_bar.stop()

        if not mp4_dict:
            messagebox.showerror("Error", "No valid MP4 formats found.")
            return

        for resolution in mp4_dict.keys():
            format_listbox.insert(tk.END, resolution)

    threading.Thread(target=fetch, daemon=True).start()

# Download progress tracking
def progress_hook(d):
    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes", 1)
        speed = d.get("speed", 0) / 1024  # Convert bytes/s to KB/s
        percent = (downloaded / total) * 100
        progress_label.config(text=f"Speed: {speed:.2f} KB/s | Progress: {percent:.1f}%")
        progress_bar["value"] = percent

# Download function
def download():
    url = url_entry.get().strip()
    selected_option = format_choice.get()

    if not url:
        messagebox.showerror("Error", "Enter a valid URL.")
        return

    progress_bar["value"] = 0
    progress_label.config(text="Downloading...")

    def download_thread():
        if selected_option == "MP3":
            # Download best available MP3
            command = f'yt-dlp -x --audio-format mp3 -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'
        else:
            selected_idx = format_listbox.curselection()
            if not selected_idx:
                messagebox.showerror("Error", "Select a video format.")
                return

            selected_quality = format_listbox.get(selected_idx[0])
            format_code = mp4_dict[selected_quality]
            command = f'yt-dlp -f {format_code} -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            match = re.search(r"(\d+\.\d+)%", line)
            if match:
                percent = float(match.group(1))
                progress_bar["value"] = percent
                progress_label.config(text=f"Progress: {percent:.1f}%")

        process.communicate()
        progress_label.config(text="Download Complete!")
        messagebox.showinfo("Success", "Download completed.")

    threading.Thread(target=download_thread, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Video Downloader")
root.geometry("500x400")
root.configure(bg="#2b2b2b")

# Apply modern ttk theme
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12), padding=5)
style.configure("TLabel", font=("Arial", 12), background="#2b2b2b", foreground="white")
style.configure("TFrame", background="#2b2b2b")

# URL Entry
tk.Label(root, text="Video URL:", bg="#2b2b2b", fg="white", font=("Arial", 12)).pack(pady=5)
url_entry = ttk.Entry(root, width=50)
url_entry.pack()

# Format Selection Dropdown
format_choice = tk.StringVar(value="MP4")
format_dropdown = ttk.Combobox(root, textvariable=format_choice, values=["MP3", "MP4"], state="readonly")
format_dropdown.pack(pady=5)
format_dropdown.bind("<<ComboboxSelected>>", lambda event: update_format_list())

# MP4 Format Listbox
format_label = tk.Label(root, text="Select MP4 Format:", bg="#2b2b2b", fg="white", font=("Arial", 12))
format_listbox = tk.Listbox(root, height=5, width=20, bg="black", fg="white")

# Fetch Formats Button
fetch_formats_button = ttk.Button(root, text="Fetch MP4 Formats", command=fetch_formats)

# Progress Bar & Status Label
progress_label = ttk.Label(root, text="Progress: 0%")
progress_label.pack(pady=5)
progress_bar = ttk.Progressbar(root, mode="determinate", length=350)
progress_bar.pack(pady=5)

# Download Button
download_button = ttk.Button(root, text="Download", command=download)
download_button.pack(pady=10)

# Ensure correct UI layout on startup
update_format_list()

root.mainloop()
