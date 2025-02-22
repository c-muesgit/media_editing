#looks through directory and sub-directories for music files and creates a dictionary
#prompts if you want to remove leading numbers with periods, underscores,or hyphens (e.g. 02. music.mp3)
#prompts if you want to remove artist names/album names from the file name (matches with file metadata)
#generates a few text files of changes made to files + a list of all files after renaming

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

file_types = ['m4a','mp3','flac','aac','wav','opus']

def get_music(input_folder): #makes dictionary of music files in folders and subfolders (gets path, artist, title)

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

                    music_info[ID] = {'file_path':file_path,\
                                          'title': title, 'artist':artist, \
                                            'album':album}

    return music_info

def change_file_names(music_info):

    #text patterns
    ext_pattern = r"|".join([re.escape(ext) for ext in file_types])
    left_pat = r"^" #only matches beginning of file name
    n_pat = r"[0-9]+" #beginning of leading numbers match
    n_pat1 = left_pat + n_pat + r"\s-\s" #matches numbers with hyphens and spaces
    n_pat2 = left_pat + n_pat + r"\.\s?"r"(?!(" + ext_pattern + r")$)" #negative lookahead (?!...) ensures period is not followed by extension
    n_pat3 = left_pat + n_pat + r"\s?_\s?" #matches numbers with underscores
    n_pat4 = r"\s-\s" + n_pat + r"\s-\s"
    n_pat5 = r"_" + n_pat + r"_"
    n_pat6 = left_pat + n_pat + r"\s+"
    txt_pat = r"\s?-?_?\s?" #matches with hypen or underscore

    if input("Remove artist names from files (Y/N): ") == "Y" or "y":
        music_info = remove_artist_names(music_info,txt_pat)
    else:
        None

    if input("Remove album names from files (Y/N): ") == "Y" or "y":
        music_info = remove_album_names(music_info,txt_pat)
    else:
        None

    if input("Remove leading numbers from files (Y/N): ") == "Y" or "y":
        music_info = remove_leading_numbers(music_info,n_pat1,n_pat2,n_pat3,n_pat4,n_pat5,n_pat6)
    else:
        None
    
    all_files_txt(music_info)

def all_files_txt(music_info):

    all_files = []

    for ID, info in music_info.items():
        file_name = os.path.basename(info['file_path'])
        title = info['title']
        artist = info['artist']
        album = info['album']
        all_files.append(f'{ID}: {title} - {album} - {artist} ({file_name})')
    
    try:
        all_files_txt = open('all_files.txt', 'x')
    except:
        all_files_txt = open('all_files.txt', 'w')

    all_files_txt.write("ALL FILES\nFormat:ID: Title - Album - Artist (File Name)\n\n")
    for file in all_files:
        all_files_txt.write(f'{file}\n')
    all_files_txt.close()

def remove_leading_numbers(music_info,n_pat1,n_pat2,n_pat3,n_pat4,n_pat5,n_pat6): #removes leading numbers from file name if it exists

    for ID, info in music_info.items():
        full_path = info['file_path']
        path_to_file = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        title = info['title']

        if re.search(n_pat1, file_name):
            preview_name = re.sub(n_pat1, '', file_name)  # Simulate the rename
        elif re.search(n_pat2, file_name):
            preview_name = re.sub(n_pat2, '', file_name)  # Simulate the rename
        elif re.search(n_pat3, file_name):
            preview_name = re.sub(n_pat3, '', file_name)  # Simulate the rename
        elif re.search(n_pat4, file_name):
            preview_name = re.sub(n_pat4, ' - ', file_name)  # Simulate the rename
        elif re.search(n_pat5, file_name):
            preview_name = re.sub(n_pat5, ' - ', file_name)  # Simulate the rename
        elif re.search(n_pat6, file_name):
            preview_name = re.sub(n_pat6, '', file_name)
        else:
            preview_name = file_name  # No changes required
  
        try:
            new_path = os.path.join(path_to_file, preview_name)
            os.rename(full_path, new_path)  # Rename the file
            info['file_path'] = new_path  # Update the file path in the dictionary
        except:
            None

    return music_info

def remove_artist_names(music_info,txt_pat): #removes artists names from file name if it exists 

    changed_artist_files = []
    txt_name = "artists"

    for ID, info in music_info.items():
        full_path = info['file_path']
        path_to_file,file_name = os.path.dirname(full_path),os.path.basename(full_path)
        re_artist = info['artist']
        try:
            re_artist = re_artist + txt_pat
        except:
            re_artist = "zzzzzzzzzzzzzz"
        match = re.match(re_artist, file_name)

        if match:
            new_file_name = re.sub(re_artist, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            #print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            changed_artist_files.append(f'{file_name} -->\n{new_file_name}\n')
            info['file_path'] = new_path
    
    try:
        removed_artists_txt = open(f'removed_{txt_name}.txt', 'x')
    except:
        removed_artists_txt = open(f'removed_{txt_name}.txt', 'w')

    for l in changed_artist_files:
        removed_artists_txt.write(f'{l}\n')
    
    removed_artists_txt.close()

    return music_info

def remove_album_names(music_info,txt_pat): #removes album names from file name if it exists

    changed_album_files = []
    txt_name = "albums"

    for ID, info in music_info.items():

        full_path = info['file_path']
        path_to_file, file_name = os.path.dirname(full_path),os.path.basename(full_path)
        re_album = info['album']
        try:
            re_album = re_album + txt_pat
        except:
            re_album = "zzzzzzzzzzzzzzzzzzzzzz"

        try: 
            if info['album'] in info['title']:
                re_album = "zzzzzzzzzzzzzzzzzzzzzz"
                #print(f"{full_path} --> File name is the same as the album, skipping...")
        except:
            re_album = "zzzzzzzzzzzzzzzzzzzzzz"

        match = re.match(re_album, file_name)

        if match:
            new_file_name = re.sub(re_album, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            #print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            changed_album_files.append(f'{file_name} -->\n{new_file_name}\n')
            info['file_path'] = new_path
        else:
            None
    try:
        removed_albums_txt = open(f'removed_{txt_name}.txt', 'x')
    except:
        removed_albums_txt = open(f'removed_{txt_name}.txt', 'w')

    for l in changed_album_files:
        removed_albums_txt.write(f'{l}\n')
    
    removed_albums_txt.close()

    return music_info

def main():
    path = "/Users/calebmueller/Library/CloudStorage/OneDrive-UNBC/Music/Rachel_Music"
    music_info = get_music(path)
    change_file_names(music_info)

if __name__ == "__main__":
    main()

