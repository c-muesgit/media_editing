import os
import subprocess
import re

# Define the download folder
DOWNLOAD_FOLDER = "downloaded_videos"

# Create the directory if it doesn’t exist
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def run_command(command):
    """Runs a shell command and captures the output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout

def is_youtube_playlist(url):
    """Checks if the given URL is a YouTube playlist."""
    return "playlist" in url.lower()

def download_audio(url):
    """Downloads the best audio format and converts it to MP3."""
    print("\nDownloading best audio (MP3)...")
    
    # If it's a playlist, store audio in a subfolder
    if is_youtube_playlist(url):
        command = f'yt-dlp -f "bestaudio" --extract-audio --audio-format mp3 -o "{DOWNLOAD_FOLDER}/%(playlist_title)s/%(title)s.%(ext)s" "{url}"'
    else:
        command = f'yt-dlp -f "bestaudio" --extract-audio --audio-format mp3 -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'
    
    os.system(command)

def get_mp4_video_formats(url):
    """Fetches and displays only MP4 video formats using yt-dlp, with numbered IDs."""
    print("\nFetching available MP4 video formats...\n")
    command = f'yt-dlp -F "{url}"'
    output = run_command(command)

    # Extract only MP4 formats and assign numbered IDs
    mp4_formats = []
    format_dict = {}
    counter = 1  # Start numbering formats from 1

    for line in output.split("\n"):
        if "mp4" in line.lower():
            mp4_formats.append(line.strip())
            format_id = line.split()[0]  # Extract format ID from the first column
            format_dict[str(counter)] = format_id
            counter += 1

    if not mp4_formats:
        print("No MP4 formats found! Try another video.")
        return None

    print("Available MP4 formats:\n")
    print("ID | Format ID | Resolution | File Size | Video Codec")
    print("-" * 60)

    for i, format_line in enumerate(mp4_formats, start=1):
        format_id = format_dict[str(i)]
        print(f"{i}  | {format_id}  | {format_line}")

    return format_dict

def download_video(url, selected_id, format_dict):
    """Downloads the selected MP4 video format."""
    if selected_id not in format_dict:
        print("Invalid ID selection. Exiting...")
        return

    format_code = format_dict[selected_id]

    print(f"\nDownloading video(s) in format {format_code} (MP4)...")

    # If it's a playlist, store videos in a subfolder
    if is_youtube_playlist(url):
        command = f'yt-dlp -f {format_code} -o "{DOWNLOAD_FOLDER}/%(playlist_title)s/%(title)s.%(ext)s" "{url}"'
    else:
        command = f'yt-dlp -f {format_code} -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'

    os.system(command)

def main():
    print("=== Universal Video Downloader (yt-dlp) ===\n")
    url = input("Enter the video or playlist URL: ").strip()

    if not url:
        print("Invalid URL. Exiting...")
        return

    # Detect if it's a playlist
    if is_youtube_playlist(url):
        print("\n🎵 This is a **YouTube playlist**! All videos will be downloaded.\n")

    choice = input("Do you want to download (A)udio or (V)ideo? [A/V]: ").strip().lower()

    if choice == 'a':
        download_audio(url)
    elif choice == 'v':
        # Fetch formats only if it's a single video (playlists don't need manual format selection)
        if not is_youtube_playlist(url):
            format_dict = get_mp4_video_formats(url)
            if not format_dict:
                return  # No valid MP4 formats

            selected_id = input("\nEnter the ID of the format you want to download (MP4 only): ").strip()
            
            if not selected_id.isdigit() or selected_id not in format_dict:
                print("Invalid selection. Exiting...")
                return
        else:
            # Auto-select best MP4 quality for playlists
            selected_id = "bv+ba"

        download_video(url, selected_id, format_dict)
    else:
        print("Invalid choice. Exiting...")

if __name__ == "__main__":
    main()
