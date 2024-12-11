import os
import re
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

def music_info(input_folder): #makes dictionary of music files in folders and subfolders (gets path, artist, title)

    music_info = {}
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

                    try:
                        title = file_info.get('title', [None])[0]
                        artist = file_info.get('artist', [None])[0]
                        album = file_info.get('album', [None])[0]
                    except:
                        print(f"Missing info for {file_path}")

                    music_info[ID] = {'file_path':file_path}

                    if title:
                        music_info[ID] = {'title': title}
                    #artist_name = get_artist(file_path)
                    if artist:
                        music_info[ID] = {'artist': artist}
    
                    if album:
                        music_info[ID] = {'album': album}
                    
    return music_info

def remove_artist_names(music_info): #removes artists names from beginning of file if it exists 

    removed_artists = []

    for ID, info in music_info.items():
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

def remove_album_names(music_info):

    removed_albums = []

    for ID, info in music_info.items():
        full_path = info['file_path']
        path_to_file = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)

        re_album = info['album']
        re_album = r"^" + re_album + r"\s?-?_?\s?"
        match = re.search(re_album, file_name)
        if match:
            new_file_name = re.sub(re_album, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            removed_albums.append(new_file_name)
    try:
        removed_albums_txt = open('removed_artists.txt', 'x')
    except:
        removed_albums_txt = open('removed_artists.txt', 'w')

    for l in removed_albums:
        removed_albums_txt.write(f'{l}\n')
    
    removed_albums_txt.close()

def remove_leading_numbers(music_info): #removes leading numbers from songs like "04 - song.flac" if it exists

    all_files = []

    for ID, info in music_info.items():
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

def main():
    #Tk().withdraw()  # Hide the main Tkinter window
    #print("Select the folder containing the music files and/or folders:")
    #path = askdirectory(title="Select Folder: ")
    path = "/Users/calebmueller/Desktop/test"
    music_info = music_info(path)
    if input("Remove leading numbers from files (Y/N): ") == "Y" or "y":
        remove_leading_numbers(music_info)
    else:
        None
    if input("Remove artist names from files (Y/N): ") == "Y" or "y":
        remove_artist_names(music_info)
    else:
        None

    #for (path, directories, files) in os.walk(path):
        #for file in files:
            #if file.endswith(".m3u"):
                #if input("Convert M3U to XML? (Y/N): ") == "Y" or "y":
                    #convert_m3u_to_xml(path)

if __name__ == "__main__":
    main()

