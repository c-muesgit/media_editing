import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from tkinter import Tk
from tkinter.filedialog import askdirectory

def get_artist(file_path):
    """
    Extract artist metadata from an audio file.
    Supports .mp3 and .flac formats.
    """
    try:
        if file_path.lower().endswith('.mp3'):
            audio = EasyID3(file_path)
            return audio.get('artist', [None])[0]
        elif file_path.lower().endswith('.flac'):
            audio = FLAC(file_path)
            return audio.get('artist', [None])[0]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def copy_and_organize_music(input_folder, output_folder):
    """
    Copy and organize music files into folders by artist.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    playlist_items = []

    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac')):
                file_path = os.path.join(root, file)
                artist = get_artist(file_path)
                if artist:
                    artist_folder = os.path.join(output_folder, artist)
                    if not os.path.exists(artist_folder):
                        os.makedirs(artist_folder)
                    dest_path = os.path.join(artist_folder, file)
                    shutil.copy(file_path, dest_path)
                    print(f"Copied {file} to {artist_folder}")

                    # Add relative path to playlist
                    relative_path = f"{artist}/{file}"
                    playlist_items.append(relative_path)
                else:
                    print(f"Artist metadata not found for {file_path}")

    return playlist_items

def generate_xml_playlist(playlist_items, input_folder_name, output_folder):
    """
    Generate an XML playlist with the given items.
    """
    playlist = ET.Element("Item")
    
    # Add metadata elements
    ET.SubElement(playlist, "Added").text = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    ET.SubElement(playlist, "LockData").text = "false"
    ET.SubElement(playlist, "LocalTitle").text = input_folder_name
    ET.SubElement(playlist, "RunningTime").text = "366"
    
    genres = ET.SubElement(playlist, "Genres")
    ET.SubElement(genres, "Genre").text = "Alternative"
    ET.SubElement(genres, "Genre").text = "Indie"
    # Add additional genres as needed

    ET.SubElement(playlist, "OwnerUserId").text = "9af58ec9f8c04f008565bd49fead9193"

    # Add playlist items
    playlist_items_element = ET.SubElement(playlist, "PlaylistItems")
    for item in playlist_items:
        playlist_item = ET.SubElement(playlist_items_element, "PlaylistItem")
        ET.SubElement(playlist_item, "Path").text = f"/data/music/{item}"

    ET.SubElement(playlist, "Shares")
    ET.SubElement(playlist, "PlaylistMediaType").text = "Audio"

    # Write XML to file
    tree = ET.ElementTree(playlist)
    xml_output_path = os.path.join(output_folder, f'{input_folder_name}.xml')
    tree.write(xml_output_path, encoding="utf-8", xml_declaration=True)
    print(f"XML playlist generated at {xml_output_path}")

def generate_m3u_playlist(playlist_items, input_folder_name, output_folder):
    """
    Generate an M3U playlist with the given items.
    """
    m3u_output_path = os.path.join(output_folder, f'{input_folder_name}.m3u')
    with open(m3u_output_path, "w", encoding="utf-8") as m3u_file:
        for item in playlist_items:
            m3u_file.write(f"{item}\n")
    print(f"M3U playlist generated at {m3u_output_path}")

def folder_process():
    Tk().withdraw()  # Hide the main Tkinter window
    print("Select the folder containing the music files:")
    input_folder = askdirectory(title="Select Input Folder")
    if not input_folder:
        print("No input folder selected. Exiting.")
        exit()
    input_name = os.path.basename(input_folder)
    print(f'Playlist will be named {input_name}')

    output_path = os.path.dirname(input_folder)
    output_folder = os.path.join(output_path, f'{input_name}_Sorted')
    os.makedirs(output_folder, exist_ok=True)

    return input_folder, input_name, output_folder

def main():
    input_folder, input_name, output_folder = folder_process()
    print(f"Organizing music from {input_folder} to {output_folder}...")
    playlist_items = copy_and_organize_music(input_folder, output_folder)
    print("Generating XML playlist...")
    generate_xml_playlist(playlist_items, input_name, output_folder)

    print("Generating M3U playlist...")
    generate_m3u_playlist(playlist_items, input_name, output_folder)

    print("Music organization and playlist generation complete.")

if __name__ == "__main__":
    main()