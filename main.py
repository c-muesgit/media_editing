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

re_pattern1 = r"^[0-9]+\s?-\s?" #file needs to have "-" after number (spaces don't matter)
re_pattern2 = r"^[0-9]+\.\s+" #file needs to have "." after number and any number of spaces
#pattern 2 won't delete songs like "1998.flac" or "7 Years.flac"

file_types = ['.m4a','.mp3','.flac','.aac','.wav','.opus']

def get_music_files(input_folder): #makes dictionary of music files in folders and subfolders (gets path, artist, title)

    music_files = {}
    ID = 0

    if os.path.isfile('skipped.txt'):
        skipped_txt = open('skipped.txt','w')
    else:
        skipped_txt = open('skipped.txt','x')

    for (path, directories, files) in os.walk(input_folder): #get music info and create dictionary
        for file in files:
            for type in file_types: # checks extensions in types (iterate as .endswith only accepts one at a time)
                if file.endswith(type):
                    ID = ID + 1
                    file_path = os.path.join(path,file)
                    try:
                        file_info = mutagen.File(file_path, easy=True)
                    except: # tip: you can get error as variable if you put "Exception as variable" after ""except"
                        print(f'Skipping file {os.path.basename(file)}')
                        skipped_txt.write(f'{file_path}\n')

                    title = file_info.get('title', [None])[0]
                    artist = file_info.get('artist', [None])[0]

                    #artist_name = get_artist(file_path)
                    if artist:
                        music_files[ID] = {'file_path':file_path,'title': title, 'artist': artist}
                    else:
                        print(f"no artist found for {file_path}")
                        music_files[ID] = {'file_path':file_path}
    
    return music_files

def remove_artist_names(music_files): #removes artists names from beginning of file if it exists 

    removed_artists = []

    for ID, info in music_files.items():
        full_path = info['file_path']
        path_to_file = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)

        re_artist = info['artist']
        re_artist = r"^" + re_artist + r"\s?-?_?\s?"
        match = re.search(re_artist, file_name)
        if match:
            new_file_name = re.sub(re_artist, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            removed_artists.append(new_file_name)
    try:
        removed_artists_txt = open('removed_artists.txt', 'x')
    except:
        removed_artists_txt = open('removed_artists.txt', 'w')

    for l in removed_artists:
        removed_artists_txt.write(f'{l}\n')
    
    removed_artists_txt.close()

def remove_leading_numbers(music_files): #removes leading numbers from songs like "04 - song.flac" if it exists

    all_files = []

    for ID, info in music_files.items():
        full_path = info['file_path']
        path_to_file = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        match1 = re.search(re_pattern1, file_name)
        match2 = re.search(re_pattern2, file_name)
        if match1:
            new_file_name = re.sub(re_pattern1, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            all_files.append(new_file_name)
        elif match2:
            new_file_name = re.sub(re_pattern2, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            all_files.append(new_file_name)
        else:
            all_files.append(file_name)
    try:
        all_files_txt = open('all_files.txt', 'x')
    except:
        all_files_txt = open('all_files.txt', 'w')

    for l in all_files:
        all_files_txt.write(f'{l}\n')
    
    all_files_txt.close()

    return None

#unused functions
def convert_m3u_to_xml(input_folder): #unused

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
                ET.SubElement(playlist, "RunningTime").text = "366"

                genres = ET.SubElement(playlist, "Genres")
                ET.SubElement(genres, "Genre").text = "Alternative"
                ET.SubElement(genres, "Genre").text = "Indie"

                ET.SubElement(playlist, "OwnerUserId").text = "9af58ec9f8c04f008565bd49fead9193"

                playlist_items_element = ET.SubElement(playlist, "PlaylistItems")

                with open(m3u, 'r') as file:
                    for line in file:
                        folder = line.split('/')[0]
                        m3u_title = line.split('/')[1]
                        pattern = re_pattern1
                        match = re.search(pattern, m3u_title)
                        if match:
                            new_m3u_title = re.sub(pattern, '', m3u_title)
                        else:
                            new_m3u_title = m3u_title

                        relative_path = f"{folder}/{new_m3u_title}"
                        playlist_item = ET.SubElement(playlist_items_element, "PlaylistItem")
                        ET.SubElement(playlist_item, "Path").text = f"/data/music/{relative_path}"

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

def main():
    #Tk().withdraw()  # Hide the main Tkinter window
    #print("Select the folder containing the music files and/or folders:")
    #path = askdirectory(title="Select Folder: ")
    path = "/Users/calebmueller/Desktop/test"
    music_files = get_music_files(path)
    if input("Remove leading numbers from files (Y/N): ") == "Y" or "y":
        remove_leading_numbers(music_files)
    else:
        None
    if input("Remove artist names from files (Y/N): ") == "Y" or "y":
        remove_artist_names(music_files)
    else:
        None

    #for (path, directories, files) in os.walk(path):
        #for file in files:
            #if file.endswith(".m3u"):
                #if input("Convert M3U to XML? (Y/N): ") == "Y" or "y":
                    #convert_m3u_to_xml(path)

if __name__ == "__main__":
    main()

