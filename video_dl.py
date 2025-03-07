import os
import subprocess
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import signal
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
    match = re.search(r'(\d+)x(\d+)', resolution)
    if match:
        height = match.group(2)
        return f"{height}p"
    
    match = re.search(r'(\d+)p', resolution)
    if match:
        return f"{match.group(1)}p"
    
    return resolution

def get_video_formats(url):
    """Fetch available video formats with both video and audio streams."""
    stdout, stderr = run_command(f'yt-dlp -F "{url}"')
    
    if "ERROR:" in stderr:
        print(f"Error from yt-dlp: {stderr}")
        return {}
    
    print("yt-dlp output:")
    print(stdout)
    
    format_dict = {}
    
    for line in stdout.split("\n"):
        if "ID " in line or "----" in line or not line.strip():
            continue
            
        parts = re.split(r'\s+', line.strip())
        if len(parts) < 2:
            continue
            
        format_id = parts[0]
        
        resolution_found = False
        for part in parts:
            if part.endswith("p") and part[:-1].isdigit():
                resolution = part
                format_dict[resolution] = format_id
                print(f"Added format with resolution: {resolution} -> {format_id}")
                resolution_found = True
                break
        
        if not resolution_found:
            for part in parts:
                if "x" in part and all(segment.isdigit() for segment in part.split("x")):
                    resolution = normalize_resolution(part)
                    format_dict[resolution] = format_id
                    print(f"Added format with dimensions: {resolution} -> {format_id}")
                    resolution_found = True
                    break
    
    if format_dict:
        return format_dict
    
    audio_format = None
    for line in stdout.split("\n"):
        if "audio only" in line.lower():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 2:
                audio_format = parts[0]
                print(f"Found audio format: {audio_format}")
                break
    
    if audio_format:
        for line in stdout.split("\n"):
            if "video only" in line.lower():
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 3:
                    format_id = parts[0]
                    
                    resolution_found = False
                    for part in parts:
                        if "x" in part or "p" in part.lower():
                            resolution = normalize_resolution(part)
                            format_dict[resolution] = f"{format_id}+{audio_format}"
                            print(f"Added combined format: {resolution} -> {format_id}+{audio_format}")
                            resolution_found = True
                            break
                    
                    if not resolution_found and len(parts) > 2:
                        resolution_desc = ' '.join(parts[1:3])
                        format_dict[resolution_desc] = f"{format_id}+{audio_format}"
                        print(f"Added format with desc: {resolution_desc} -> {format_id}+{audio_format}")
    
    if not format_dict:
        for line in stdout.split("\n"):
            if any(fmt in line.lower() for fmt in ["mp4", "webm", "mkv", "m3u8"]):
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 2:
                    format_id = parts[0]
                    
                    desc_parts = []
                    for part in parts[1:]:
                        if any(q in part.lower() for q in ["p", "x", "small", "medium", "large", "hd", "sd"]):
                            desc_parts.append(part)
                    
                    if desc_parts:
                        desc = " ".join(desc_parts)
                    else:
                        desc = f"Format {format_id}"
                    
                    format_dict[desc] = format_id
                    print(f"Added generic format: {desc} -> {format_id}")
    
    return format_dict

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("550x500")
        
        self.format_dict = {}
        
        self.create_widgets()
    
    def create_widgets(self):
        # URL Entry
        url_frame = tk.Frame(self.root)
        url_frame.pack(pady=10, fill=tk.X, padx=10)
        tk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_entry = tk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        fetch_button = tk.Button(url_frame, text="Fetch Formats", command=self.fetch_formats)
        fetch_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Listbox for formats with scrollbar
        format_frame = tk.Frame(self.root)
        format_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=10)

        # Format header
        format_header = tk.Frame(format_frame)
        format_header.pack(fill=tk.X)
        tk.Label(format_header, text="Available formats:").pack(side=tk.LEFT, anchor=tk.W)

        # List with scrollbar
        list_frame = tk.Frame(format_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.format_listbox = tk.Listbox(list_frame, height=10, yscrollcommand=scrollbar.set)
        self.format_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.format_listbox.yview)

        # Progress frame
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(pady=10, fill=tk.X, padx=10)
        self.progress_label = tk.Label(progress_frame, text="", anchor=tk.W)
        self.progress_label.pack(fill=tk.X)
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=200)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        mp4_button = tk.Button(btn_frame, text="Download MP4", command=lambda: self.download_video(False), bg="lightblue", width=15)
        mp4_button.pack(side=tk.LEFT, padx=5)

        mp3_button = tk.Button(btn_frame, text="Download MP3", command=lambda: self.download_video(True), bg="lightgreen", width=15)
        mp3_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(btn_frame, text="Cancel", command=self.cancel_download, bg="lightcoral", width=15, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Folder selection
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(folder_frame, text="Save to:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar(value=DOWNLOAD_FOLDER)
        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=40)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        browse_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT)

        # Status bar
        status_frame = tk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(status_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)

    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        
        self.format_listbox.delete(0, tk.END)
        self.progress_bar.start(10)
        self.progress_label.config(text="Fetching formats...")

        def fetch():
            self.format_dict = get_video_formats(url)
            self.progress_bar.stop()
            self.progress_label.config(text="")

            if not self.format_dict:
                messagebox.showerror("Error", "No suitable formats found! Check console for debug info.")
                return

            for resolution in sorted(self.format_dict.keys(), 
                                     key=lambda x: int(x.replace('p', '')) if x.endswith('p') and x[:-1].isdigit() else 0,
                                     reverse=True):
                self.format_listbox.insert(tk.END, resolution)

        threading.Thread(target=fetch, daemon=True).start()

    def cancel_download(self):
        global current_process, download_cancelled
        
        if current_process:
            download_cancelled = True
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(current_process.pid)])
            else:
                os.killpg(os.getpgid(current_process.pid), signal.SIGTERM)
            
            self.progress_label.config(text="Download cancelled")
            self.progress_bar.stop()
            self.progress_bar["value"] = 0
            self.cancel_button.config(state=tk.DISABLED)

    def download_video(self, is_audio):
        global current_process, download_cancelled
        
        url = self.url_entry.get().strip()
        selected_idx = self.format_listbox.curselection()
        
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        if not selected_idx and not is_audio:
            messagebox.showerror("Error", "Please select a format.")
            return

        if is_audio:
            format_code = "bestaudio"
        else:
            selected_resolution = self.format_listbox.get(selected_idx[0])
            format_code = self.format_dict[selected_resolution]

        self.progress_bar.stop()
        self.progress_bar["value"] = 0
        download_cancelled = False
        self.cancel_button.config(state=tk.NORMAL)

        def download():
            global current_process, download_cancelled
            self.progress_label.config(text="Starting download...")
            
            download_folder = self.folder_var.get()

            if is_audio:
                command = f'yt-dlp -f {format_code} -x --audio-format mp3 --newline --progress -o "{download_folder}/%(title)s.%(ext)s" "{url}"'
            else:
                command = f'yt-dlp -f {format_code}+bestaudio --merge-output-format mp4 --newline --progress -o "{download_folder}/%(title)s.%(ext)s" "{url}"'

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
            
            for line in iter(current_process.stdout.readline, ''):
                if download_cancelled:
                    break
                
                if "[download]" in line:
                    if "%" in line:
                        try:
                            percent_match = re.search(r'(\d+\.\d+)%', line)
                            if percent_match:
                                percent = float(percent_match.group(1))
                                self.root.after(10, lambda p=percent: self.update_progress(p))
                            
                            speed_match = re.search(r'at\s+([^\s]+)', line)
                            eta_match = re.search(r'ETA\s+([^\s]+)', line)
                            
                            if speed_match and eta_match:
                                speed = speed_match.group(1)
                                eta = eta_match.group(1)
                                status_text = f"Downloading: {percent:.1f}% (Speed: {speed}, ETA: {eta})"
                                self.root.after(10, lambda st=status_text: self.update_status(st))
                        except Exception as e:
                            print(f"Error parsing progress: {e}")
                
                elif "Destination" in line:
                    self.root.after(10, lambda: self.update_status(f"Preparing: {line.strip()}"))
                elif "Merging" in line:
                    self.root.after(10, lambda: self.update_status("Merging video and audio..."))
                    
                print(line.strip())
            
            return_code = current_process.wait()
            
            if download_cancelled:
                self.root.after(10, lambda: self.update_status("Download cancelled"))
            elif return_code == 0:
                self.root.after(10, lambda: self.update_status("Download completed successfully!"))
                self.root.after(10, lambda: self.update_progress(100))
                self.root.after(100, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
            else:
                self.root.after(10, lambda: self.update_status("Download failed!"))
                self.root.after(100, lambda: messagebox.showerror("Error", "Download failed!"))
            
            self.root.after(10, lambda: self.cancel_button.config(state=tk.DISABLED))
            current_process = None

        threading.Thread(target=download, daemon=True).start()

    def update_progress(self, value):
        self.progress_bar["value"] = value
    
    def update_status(self, text):
        self.progress_label.config(text=text)

    def browse_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()