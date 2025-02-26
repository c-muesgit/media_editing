import os
import subprocess
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import signal
import time
import platform

# Define the download folder to be in the current directory
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloaded_videos")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Global variable to track current download process
current_process = None
download_cancelled = False

def run_command(command):
    """Runs a shell command and captures the output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout, stderr

def normalize_resolution(resolution):
    """Convert different resolution formats into a standard format (e.g., 1920x1080 → 1080p)."""
    # First try to extract resolution from formats like "1920x1080"
    match = re.search(r'(\d+)x(\d+)', resolution)
    if match:
        height = match.group(2)
        return f"{height}p"
    
    # If that fails, try to extract numeric values that might be resolutions
    match = re.search(r'(\d+)p', resolution)
    if match:
        return f"{match.group(1)}p"
    
    # Return original if no pattern matches
    return resolution

def get_video_formats(url):
    """Fetch available video formats with both video and audio streams."""
    stdout, stderr = run_command(f'yt-dlp -F "{url}"')
    
    if "ERROR:" in stderr:
        print(f"Error from yt-dlp: {stderr}")
        return {}
    
    # Debug: Print the entire output for inspection
    print("yt-dlp output:")
    print(stdout)
    
    format_dict = {}
    
    # Universal format detection approach
    # First pass: Look for formats with clear resolutions (like 720p, 1080p)
    for line in stdout.split("\n"):
        # Skip header lines
        if "ID " in line or "----" in line or not line.strip():
            continue
            
        parts = re.split(r'\s+', line.strip())
        if len(parts) < 2:  # Need at least format ID and some info
            continue
            
        format_id = parts[0]
        
        # Try to find resolution in standard format (e.g., 720p, 1080p)
        resolution_found = False
        for part in parts:
            # Match patterns like "720p" or "1080p"
            if part.endswith("p") and part[:-1].isdigit():
                resolution = part
                format_dict[resolution] = format_id
                print(f"Added format with resolution: {resolution} -> {format_id}")
                resolution_found = True
                break
        
        # If we didn't find a standard resolution, look for dimension notation
        if not resolution_found:
            for part in parts:
                # Match patterns like "1280x720"
                if "x" in part and all(segment.isdigit() for segment in part.split("x")):
                    resolution = normalize_resolution(part)
                    format_dict[resolution] = format_id
                    print(f"Added format with dimensions: {resolution} -> {format_id}")
                    resolution_found = True
                    break
    
    # If we found formats with clear resolutions, return them
    if format_dict:
        return format_dict
    
    # Second pass: Try to find audio formats for YouTube-style combined formats
    audio_format = None
    for line in stdout.split("\n"):
        if "audio only" in line.lower():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 2:
                audio_format = parts[0]
                print(f"Found audio format: {audio_format}")
                break
    
    # If we found an audio format, look for video-only formats to combine with
    if audio_format:
        for line in stdout.split("\n"):
            if "video only" in line.lower():
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 3:
                    format_id = parts[0]
                    
                    # Try to find something that looks like a resolution
                    resolution_found = False
                    for part in parts:
                        if "x" in part or "p" in part.lower():
                            resolution = normalize_resolution(part)
                            format_dict[resolution] = f"{format_id}+{audio_format}"
                            print(f"Added combined format: {resolution} -> {format_id}+{audio_format}")
                            resolution_found = True
                            break
                    
                    # If we couldn't find a clear resolution, use format description
                    if not resolution_found and len(parts) > 2:
                        resolution_desc = ' '.join(parts[1:3])
                        format_dict[resolution_desc] = f"{format_id}+{audio_format}"
                        print(f"Added format with desc: {resolution_desc} -> {format_id}+{audio_format}")
    
    # If we still haven't found any formats, try a more generic approach
    if not format_dict:
        for line in stdout.split("\n"):
            # Look for any line that has mp4, webm or other common formats
            if any(fmt in line.lower() for fmt in ["mp4", "webm", "mkv", "m3u8"]):
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 2:
                    format_id = parts[0]
                    
                    # Try to construct a meaningful description
                    desc_parts = []
                    for part in parts[1:]:
                        # Look for parts that might describe quality
                        if any(q in part.lower() for q in ["p", "x", "small", "medium", "large", "hd", "sd"]):
                            desc_parts.append(part)
                    
                    if desc_parts:
                        desc = " ".join(desc_parts)
                    else:
                        # If we can't find quality descriptors, use format info
                        desc = f"Format {format_id}"
                    
                    format_dict[desc] = format_id
                    print(f"Added generic format: {desc} -> {format_id}")
    
    return format_dict

def fetch_formats():
    """Fetch formats with a progress bar."""
    global format_dict

    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return
    
    format_listbox.delete(0, tk.END)
    progress_bar.start(10)  # Start loading animation
    progress_label.config(text="Fetching formats...")
    search_entry.delete(0, tk.END)  # Clear search

    def fetch():
        global format_dict
        format_dict = get_video_formats(url)
        progress_bar.stop()  # Stop loading animation
        progress_label.config(text="")

        if not format_dict:
            messagebox.showerror("Error", "No suitable formats found! Check console for debug info.")
            return

        for resolution in sorted(format_dict.keys(), 
                                 key=lambda x: int(x.replace('p', '')) if x.endswith('p') and x[:-1].isdigit() else 0,
                                 reverse=True):
            format_listbox.insert(tk.END, resolution)

    threading.Thread(target=fetch, daemon=True).start()

def cancel_download():
    """Cancel the current download process."""
    global current_process, download_cancelled
    
    if current_process:
        download_cancelled = True
        if platform.system() == "Windows":
            # Windows version: terminate process tree
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(current_process.pid)])
        else:
            # Unix version
            os.killpg(os.getpgid(current_process.pid), signal.SIGTERM)
        
        progress_label.config(text="Download cancelled")
        progress_bar.stop()
        progress_bar["value"] = 0
        cancel_button.config(state=tk.DISABLED)

def download_video(is_audio):
    """Downloads the selected video format with a progress bar."""
    global current_process, download_cancelled
    
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

    # Reset progress
    progress_bar.stop()
    progress_bar["value"] = 0
    download_cancelled = False
    cancel_button.config(state=tk.NORMAL)

    def download():
        global current_process, download_cancelled
        progress_label.config(text="Starting download...")
        
        # Prepare the command with progress hooks
        if is_audio:
            command = f'yt-dlp -f {format_code} -x --audio-format mp3 --newline --progress -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'
        else:
            command = f'yt-dlp -f {format_code} --merge-output-format mp4 --newline --progress -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'

        # Start the process with a different process group
        if platform.system() == "Windows":
            current_process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            current_process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                preexec_fn=os.setsid
            )
        
        # Process the output to update progress
        for line in iter(current_process.stdout.readline, ''):
            if download_cancelled:
                break
            
            # Parse progress information
            if "[download]" in line:
                if "%" in line:
                    try:
                        # Extract percentage
                        percent_match = re.search(r'(\d+\.\d+)%', line)
                        if percent_match:
                            percent = float(percent_match.group(1))
                            root.after(10, lambda p=percent: update_progress(p))
                        
                        # Extract download speed and ETA
                        speed_match = re.search(r'at\s+([^\s]+)', line)
                        eta_match = re.search(r'ETA\s+([^\s]+)', line)
                        
                        if speed_match and eta_match:
                            speed = speed_match.group(1)
                            eta = eta_match.group(1)
                            status_text = f"Downloading: {percent:.1f}% (Speed: {speed}, ETA: {eta})"
                            root.after(10, lambda st=status_text: update_status(st))
                    except Exception as e:
                        print(f"Error parsing progress: {e}")
            
            # Check for specific messages
            elif "Destination" in line:
                root.after(10, lambda: update_status(f"Preparing: {line.strip()}"))
            elif "Merging" in line:
                root.after(10, lambda: update_status("Merging video and audio..."))
                
            print(line.strip())  # Print for debugging
        
        # Wait for the process to complete
        return_code = current_process.wait()
        
        # Check if the download was cancelled or completed successfully
        if download_cancelled:
            root.after(10, lambda: update_status("Download cancelled"))
        elif return_code == 0:
            root.after(10, lambda: update_status("Download completed successfully!"))
            root.after(10, lambda: update_progress(100))
            root.after(100, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
        else:
            root.after(10, lambda: update_status("Download failed!"))
            root.after(100, lambda: messagebox.showerror("Error", "Download failed!"))
        
        # Disable cancel button
        root.after(10, lambda: cancel_button.config(state=tk.DISABLED))
        current_process = None

    def update_progress(value):
        progress_bar["value"] = value
    
    def update_status(text):
        progress_label.config(text=text)

    threading.Thread(target=download, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Video Downloader")
root.geometry("550x500")

# URL Entry
url_frame = tk.Frame(root)
url_frame.pack(pady=10, fill=tk.X, padx=10)
tk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
url_entry = tk.Entry(url_frame, width=50)
url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
fetch_button = tk.Button(url_frame, text="Fetch Formats", command=fetch_formats)
fetch_button.pack(side=tk.RIGHT, padx=(5, 0))

# Listbox for formats with scrollbar and search
format_frame = tk.Frame(root)
format_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=10)

# Format header with search
format_header = tk.Frame(format_frame)
format_header.pack(fill=tk.X)
tk.Label(format_header, text="Available formats:").pack(side=tk.LEFT, anchor=tk.W)

# Search box
search_frame = tk.Frame(format_header)
search_frame.pack(side=tk.RIGHT)
tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
search_entry = tk.Entry(search_frame, width=15)
search_entry.pack(side=tk.LEFT, padx=(5, 0))

# List with scrollbar
list_frame = tk.Frame(format_frame)
list_frame.pack(fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
format_listbox = tk.Listbox(list_frame, height=10, yscrollcommand=scrollbar.set)
format_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=format_listbox.yview)

# Search function
def search_formats(event=None):
    search_text = search_entry.get().lower()
    format_listbox.delete(0, tk.END)
    
    if not format_dict:
        return
        
    for resolution in sorted(format_dict.keys(), 
                           key=lambda x: int(x.replace('p', '')) if x.endswith('p') and x[:-1].isdigit() else 0,
                           reverse=True):
        if search_text in resolution.lower():
            format_listbox.insert(tk.END, resolution)

search_entry.bind("<KeyRelease>", search_formats)

# Progress frame
progress_frame = tk.Frame(root)
progress_frame.pack(pady=10, fill=tk.X, padx=10)
progress_label = tk.Label(progress_frame, text="", anchor=tk.W)
progress_label.pack(fill=tk.X)
progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=200)
progress_bar.pack(fill=tk.X, pady=5)

# Buttons frame
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

mp4_button = tk.Button(btn_frame, text="Download MP4", command=lambda: download_video(False), bg="lightblue", width=15)
mp4_button.pack(side=tk.LEFT, padx=5)

mp3_button = tk.Button(btn_frame, text="Download MP3", command=lambda: download_video(True), bg="lightgreen", width=15)
mp3_button.pack(side=tk.LEFT, padx=5)

cancel_button = tk.Button(btn_frame, text="Cancel", command=cancel_download, bg="lightcoral", width=15, state=tk.DISABLED)
cancel_button.pack(side=tk.LEFT, padx=5)

# Folder selection
folder_frame = tk.Frame(root)
folder_frame.pack(pady=5, fill=tk.X, padx=10)
tk.Label(folder_frame, text="Save to:").pack(side=tk.LEFT)
folder_var = tk.StringVar(value=DOWNLOAD_FOLDER)
folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=40)
folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

def browse_folder():
    from tkinter import filedialog
    folder = filedialog.askdirectory(initialdir=folder_var.get())
    if folder:
        folder_var.set(folder)

browse_button = tk.Button(folder_frame, text="Browse", command=browse_folder)
browse_button.pack(side=tk.RIGHT)

# Status bar
status_frame = tk.Frame(root)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)
status_label = tk.Label(status_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(fill=tk.X)

# Run GUI
root.mainloop()