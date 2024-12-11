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
    n_pat1 = left_pat + n_pat + r"\s?-\s?" #matches numbers with hyphens
    n_pat2 = left_pat + n_pat + r"\."r"(?!(" + ext_pattern + r")$)" #negative lookahead (?!...) ensures period is not followed by extension
    n_pat3 = left_pat + n_pat + r"\s?_\s?" #matches numbers with underscores
    txt_pat = r"\s?-?_?\s?" #matches with hypen or underscore

    if input("Remove leading numbers from files (Y/N): ") == "Y" or "y":
        remove_leading_numbers(music_info,n_pat1,n_pat2,n_pat3)
    else:
        None
    if input("Remove artist names from files (Y/N): ") == "Y" or "y":
        remove_artist_names(music_info,txt_pat)
    else:
        None
    if input("Remove album names from files (Y/N): ") == "Y" or "y":
        remove_album_names(music_info,txt_pat)
    else:
        None

def remove_artist_names(music_info,txt_pat): #removes artists names from beginning of file if it exists 

    changed_artist_files = []
    txt_name = "artists"

    for ID, info in music_info.items():
        full_path = info['file_path']
        path_to_file,file_name = os.path.dirname(full_path),os.path.basename(full_path)
        re_artist = info['artist']
        re_artist = re_artist + txt_pat
        match = re.search(re_artist, file_name)

        if match:
            new_file_name = re.sub(re_artist, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            changed_artist_files.append(f'{file_name} -->\n{new_file_name}\n')
    
    try:
        removed_artists_txt = open(f'removed_{txt_name}.txt', 'x')
    except:
        removed_artists_txt = open(f'removed_{txt_name}.txt', 'w')

    for l in changed_artist_files:
        removed_artists_txt.write(f'{l}\n')
    
    removed_artists_txt.close()

def remove_album_names(music_info,txt_pat):

    changed_album_files = []
    txt_name = "albums"

    for ID, info in music_info.items():

        full_path = info['file_path']
        path_to_file,file_name = os.path.dirname(full_path),os.path.basename(full_path)
        re_album = info['album']
        re_album = re_album + txt_pat
        match = re.search(re_album, file_name)
        if match:
            new_file_name = re.sub(re_album, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            changed_album_files.append(f'{file_name} -->\n{new_file_name}\n')
    try:
        removed_albums_txt = open(f'removed_{txt_name}.txt', 'x')
    except:
        removed_albums_txt = open(f'removed_{txt_name}.txt', 'w')

    for l in changed_album_files:
        removed_albums_txt.write(f'{l}\n')
    
    removed_albums_txt.close()

def remove_leading_numbers(music_info,n_pat1,n_pat2,n_pat3): #removes leading numbers from songs like "04 - song.flac" if it exists

    all_files = []

    for ID, info in music_info.items():
        full_path = info['file_path']
        path_to_file = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        match1 = re.search(n_pat1, file_name)
        match2 = re.search(n_pat2, file_name)
        match3 = re.search(n_pat3, file_name)
        if match1:
            new_file_name = re.sub(n_pat1, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            all_files.append(new_file_name)
        elif match2:
            new_file_name = re.sub(n_pat2, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            all_files.append(new_file_name)
        elif match3:
            new_file_name = re.sub(n_pat3, '', file_name) #change file_name to one without pattern
            new_path = os.path.join(path_to_file, new_file_name)
            os.rename(full_path,new_path)
            print(f'"{file_name}" CHANGED TO "{new_file_name}"')
            all_files.append(new_file_name)
        else:
            all_files.append(file_name)
            
    print(music_info)
    try:
        all_files_txt = open('all_files.txt', 'x')
    except:
        all_files_txt = open('all_files.txt', 'w')

    for l in all_files:
        all_files_txt.write(f'{l}\n')
    
    all_files_txt.close()

def main():
    #Tk().withdraw()  # Hide the main Tkinter window
    #print("Select the folder containing the music files and/or folders:")
    #path = askdirectory(title="Select Folder: ")
    path = "/Users/calebmueller/Desktop/test"
    music_info = get_music(path)
    change_file_names(music_info)

    #for (path, directories, files) in os.walk(path):
        #for file in files:
            #if file.endswith(".m3u"):
                #if input("Convert M3U to XML? (Y/N): ") == "Y" or "y":
                    #convert_m3u_to_xml(path)

if __name__ == "__main__":
    main()

