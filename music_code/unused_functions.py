import os
import re
from functools import reduce
from datetime import datetime

from tkinter import Tk
from tkinter.filedialog import askdirectory

import xml.etree.ElementTree as ET

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.aac import AAC

#unused functions
def convert_m3u_to_xml(input_folder,jellyfin_path): #unused

    m3u_files = []
    for (path, directories, files) in os.walk(input_folder):
        for file in files:
            if file.endswith(".m3u"):
                m3u = os.path.join(path,file)

                playlist_name = os.path.splitext(os.path.basename(m3u))[0]
                print(playlist_name)
                playlist = ET.Element("Item")
                
                ET.SubElement(playlist, "Added")
                ET.SubElement(playlist, "Added").text = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                ET.SubElement(playlist, "LockData").text = "false"
                ET.SubElement(playlist, "LocalTitle").text = playlist_name
                ET.SubElement(playlist, "RunningTime").text = ""

                genres = ET.SubElement(playlist, "Genres")
                ET.SubElement(genres, "Genre").text = "Alternative"
                ET.SubElement(genres, "Genre").text = "Indie"

                ET.SubElement(playlist, "OwnerUserId").text = "9af58ec9f8c04f008565bd49fead9193"

                playlist_items_element = ET.SubElement(playlist, "PlaylistItems")

                with open(m3u, 'r', encoding='utf-8') as file:
                    for line in file:
                        folder = line.split('/')[0]
                        m3u_title = line.split('/')[1]
                        relative_path = f"{folder}/{m3u_title}"
                        playlist_item = ET.SubElement(playlist_items_element, "PlaylistItem")
                        ET.SubElement(playlist_item, "Path").text = f"{jellyfin_path}/{relative_path}"

                ET.SubElement(playlist, "Shares")
                ET.SubElement(playlist, "PlaylistMediaType").text = "Audio"

                # Write XML to file
                tree = ET.ElementTree(playlist)

                os.makedirs(os.path.join(input_folder, 'XML Playlists', playlist_name),exist_ok=True)
                output_folder = os.path.join(input_folder, 'XML Playlists', playlist_name)
                xml_output_path = os.path.join(output_folder, 'playlist.xml')
                tree.write(xml_output_path, encoding="utf-8", xml_declaration=True)
                print(f"XML playlist generated at {xml_output_path}")
                
        return None

def get_artist(file_path): #unused
    
    try:
        if file_path.lower().endswith('.mp3'):
            audio = EasyID3(file_path)
            return audio.get('artist', [None])[0]
        elif file_path.lower().endswith('.flac'):
            audio = FLAC(file_path)
            return audio.get('artist', [None])[0]
        elif file_path.lower().endswith('.m4a'):
            audio = MP4(file_path)
            return audio.tags.get('\xa9ART', [None])[0]  # MP4 artist tag
        elif file_path.lower().endswith('.opus'):
            audio = OggOpus(file_path)
            return audio.get('artist', [None])[0]
        elif file_path.lower().endswith('.aac'):
            audio = AAC.get(file_path) #untested!
            return audio.get('artist', [None])[0]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

input_folder = "C:/Users/Caleb/Desktop/Rachel_Music"
jellyfin_path = "/data/music/rachels_music"
convert_m3u_to_xml(input_folder,jellyfin_path)