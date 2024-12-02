from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, TALB, APIC
import requests
import shutil
from tkinter import *
from tkinter.filedialog import askopenfilename, askdirectory
import musicbrainzngs
import os

musicbrainzngs.set_useragent("MetadataUpdater","1.0","ctwmueller@gmail.com")
supported_file_types = [".mp3", ".flac"]

def main():
    files = open_files()
    print(files)
    output_folder = "/Users/calebmueller/Github/mutagen/Processed"
    process_files(files,output_folder)

def select():
    window = Tk()
    window.title("What type of media do you want to select?")
    window.geometry("400x260")
    padding = 20
    button_h = 2
    button_w = 5
    font_s = 12
    selection = {"value":None}

    def set_selection(option):
        selection["value"]=option
        window.quit()

    folder = Button(window,text="Folder",font=("Arial",font_s),height=button_h,width=button_w,command=lambda: set_selection("folder"))
    folder.pack(pady=padding)
    file = Button(window,text="File",font=("Arial",font_s),height=button_h,width=button_w,command=lambda: set_selection("file"))
    file.pack(pady=padding)
    quit = Button(window,text="Quit",font=("Arial",font_s),height=button_h,width=button_w,command=lambda: set_selection("quit"))
    quit.pack(pady=padding)
    window.mainloop()
    window.destroy()
    print(selection["value"])
    return selection["value"]
    
def open_files():
    
    """Prompts the user to select a music file or a folder containing music files.
    Returns:
        - If a single file is selected, returns its path.
        - If a folder is selected, returns a dictionary of supported music files in the folder.
        - If no valid selection is made, returns None."""

    Tk().withdraw()
    print("Choose whether to select a file or a folder.")
    selection_type = select()
    if selection_type == 'file':
        file_path = askopenfilename(
            title="Please select a music file",
            filetypes=[("Music Files", " ".join(f"*{ext}" for ext in supported_file_types))]
        )
        if file_path and os.path.isfile(file_path):
            return file_path
    elif selection_type == 'folder':
        folder_path = askdirectory(title="Please select a folder containing music files")
        if folder_path and os.path.isdir(folder_path):
            files = {}
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in supported_file_types):
                        full_path = os.path.join(root, filename)
                        files[filename] = full_path
            return files
    print("No valid file or folder was selected.")
    return None

def extract_metadata(file_path):
    """
    Extract Title and Artist metadata from a file.
    """
    if file_path.endswith(".mp3"):
        audio = MP3(file_path, ID3=ID3)
        artist = audio.get("TPE1", None)  # TPE1 is the artist tag
        title = audio.get("TIT2", None)  # TIT2 is the title tag
        return artist.text[0] if artist else None, title.text[0] if title else None
    elif file_path.endswith(".flac"):
        audio = FLAC(file_path)
        artist = audio.get("artist", None)  # 'artist' is the artist tag in FLAC
        title = audio.get("title", None)  # 'title' is the title tag in FLAC
        return artist[0] if artist else None, title[0] if title else None
    return None, None

def search_album(artist, title):
    """
    Search for the original album name and release group ID on MusicBrainz.
    Returns:
        - Album name (str)
        - Release group ID (str)
    """
    try:
        # Search recordings on MusicBrainz
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=10)
        if not result['recording-list']:
            print(f"No results found for {artist} - {title}")
            return None, None

        # Filter results for the best match
        candidate_albums = []
        for recording in result['recording-list']:
            # Ensure the artist matches exactly
            artist_matches = any(
                credit['artist']['name'].lower() == artist.lower()
                for credit in recording.get('artist-credit', [])
            )
            if not artist_matches:
                continue

            # Check if release-list exists
            if 'release-list' not in recording:
                continue

            for release in recording['release-list']:
                # Check if the release is "Official" and part of an "Album" group
                if (
                    release.get('status') == 'Official'
                    and release.get('release-group', {}).get('primary-type') == 'Album'
                    and 'secondary-type-list' not in release.get('release-group', {})
                ):
                    # Extract the release date for prioritization
                    release_date = release.get('date', '9999-99-99')  # Default to far future if no date
                    candidate_albums.append({
                        'title': release['title'],
                        'release_date': release_date,
                        'release_group_id': release['release-group']['id'],
                    })

        # Prioritize the earliest release date
        if candidate_albums:
            sorted_albums = sorted(candidate_albums, key=lambda x: x['release_date'])
            best_match = sorted_albums[0]
            print(f"Best match for {artist} - {title}: {best_match['title']} ({best_match['release_date']})")
            return best_match['title'], best_match['release_group_id']

        # Fallback: Return the first available album title and release group ID
        print(f"No suitable match found for {artist} - {title}")
        return None, None

    except Exception as e:
        print(f"Error searching metadata: {e}")
    return None, None


def fetch_album_cover(release_group_id):
    """
    Fetch album cover art URL from the Cover Art Archive using the release group ID.
    """
    try:
        url = f"https://coverartarchive.org/release-group/{release_group_id}/front"
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            print("Album cover fetched successfully.")
            return response.content
        else:
            print(f"Album cover not found for release group ID: {release_group_id}")
    except Exception as e:
        print(f"Error fetching album cover: {e}")
    return None

def update_album_metadata(file_path, album, output_folder, release_group_id=None):
    """
    Copy the file to the output folder, update its album metadata, and save it.
    Optionally add album cover art if `release_group_id` is provided.
    """
    if not album:
        print(f"No album metadata found for {file_path}")
        return

    # Create output folder if it doesn't exist
    try:
        if not os.path.exists(output_folder):
            print(f"Creating output folder: {output_folder}")
            os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        print(f"Error creating output folder {output_folder}: {e}")
        return

    try:
        # Determine output path
        output_path = os.path.join(output_folder, os.path.basename(file_path))

        # Skip copying if file is already in the output folder
        if os.path.abspath(file_path) != os.path.abspath(output_path):
            shutil.copy2(file_path, output_path)  # Preserve original metadata during copy
            print(f"Copied file to: {output_path}")
        else:
            print(f"File is already in the output folder: {output_path}")

        # Fetch album cover art (if release_group_id is provided)
        cover_art = None
        if release_group_id:
            cover_art = fetch_album_cover(release_group_id)

        # Update metadata in the copied file
        if file_path.endswith(".mp3"):
            audio = MP3(output_path, ID3=ID3)
            audio["TALB"] = TALB(encoding=3, text=album)

            # Embed cover art for MP3
            if cover_art:
                audio.tags.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime="image/jpeg",  # MIME type for the cover art
                        type=3,  # Front cover
                        desc="Cover",
                        data=cover_art,
                    )
                )
                print("Album cover embedded successfully.")
            audio.save()
            print(f"Updated album metadata and saved to {output_path}")

        elif file_path.endswith(".flac"):
            audio = FLAC(output_path)
            audio["album"] = album

            # Embed cover art for FLAC
            if cover_art:
                picture = Picture()
                picture.data = cover_art
                picture.type = 3  # Front cover
                picture.mime = "image/jpeg"
                audio.add_picture(picture)
                print("Album cover embedded successfully.")
            audio.save()
            print(f"Updated album metadata and saved to {output_path}")

        else:
            print(f"Unsupported file type: {file_path}")
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except Exception as e:
        print(f"Error updating metadata for {file_path}: {e}")

def process_files(files, output_folder):
    """
    Process a single file or a dictionary of files to update album metadata and cover.
    """
    if isinstance(files, str):  # Single file
        artist, title = extract_metadata(files)
        if artist and title:
            album, release_group_id = search_album(artist, title)
            # Copy the original file to the output folder
            output_path = os.path.join(output_folder, os.path.basename(files))
            shutil.copy2(files, output_path)  # Ensure the copied file is used
            print(f"Copied file to: {output_path}")

            # Update metadata and album cover for the copied file
            update_album_metadata(output_path, album, output_folder, release_group_id)
        else:
            print(f"Metadata missing for file: {files}")
    elif isinstance(files, dict):  # Multiple files
        for file_path in files.values():
            artist, title = extract_metadata(file_path)
            if artist and title:
                album, release_group_id = search_album(artist, title)
                # Copy the original file to the output folder
                output_path = os.path.join(output_folder, os.path.basename(file_path))
                shutil.copy2(file_path, output_path)  # Ensure the copied file is used
                print(f"Copied file to: {output_path}")

                # Update metadata and album cover for the copied file
                update_album_metadata(output_path, album, output_folder, release_group_id)
            else:
                print(f"Metadata missing for file: {file_path}")

main()