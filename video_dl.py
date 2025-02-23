import os
import subprocess
import re

# Define the download folder
DOWNLOAD_FOLDER = "/Users/caleb/downloaded_videos"

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

def get_mp4_video_formats(url):
    """Fetches and displays only MP4 video formats with ID and resolution."""
    print("\nFetching available MP4 video formats...\n")
    command = f'yt-dlp -F "{url}"'
    output = run_command(command)

    format_dict = {}
    counter = 1  # Start numbering formats from 1

    print("Available MP4 formats:")
    print("ID | Resolution")
    print("-" * 20)

    for line in output.split("\n"):
        if "mp4" in line.lower():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 3:
                format_id = parts[0]  # Extract format ID from the first column
                resolution = parts[2]  # Extract resolution from the third column
                print(f"{counter}  | {resolution}")
                format_dict[str(counter)] = format_id
                counter += 1

    if not format_dict:
        print("No MP4 formats found! Try another video.")
        return None

    return format_dict

def download_video(url, selected_id, format_dict):
    """Downloads the selected MP4 video format."""
    if selected_id not in format_dict:
        print("Invalid ID selection. Exiting...")
        return

    format_code = format_dict[selected_id]

    print(f"\nDownloading video(s) in format {format_code} (MP4)...")
    command = f'yt-dlp -f {format_code} -o "{DOWNLOAD_FOLDER}/%(title)s.%(ext)s" "{url}"'
    os.system(command)

def main():
    print("=== Universal Video Downloader (yt-dlp) ===\n")
    url = input("Enter the video or playlist URL: ").strip()

    if not url:
        print("Invalid URL. Exiting...")
        return

    format_dict = get_mp4_video_formats(url)
    if not format_dict:
        return  # No valid MP4 formats

    selected_id = input("\nEnter the ID of the format you want to download (MP4 only): ").strip()
    
    if not selected_id.isdigit() or selected_id not in format_dict:
        print("Invalid selection. Exiting...")
        return

    download_video(url, selected_id, format_dict)

if __name__ == "__main__":
    main()