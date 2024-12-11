import os
import re
import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import askdirectory

def remove_leading_numbers(file_name):
    """
    Remove leading numbers and the following space from a file name.
    """
    return re.sub(r"^\d+\.\s*", "", file_name)

def update_artist_folders(main_folder):
    """
    Process all artist folders to remove leading numbers from song files.
    """
    for artist_folder in os.listdir(main_folder):
        artist_path = os.path.join(main_folder, artist_folder)
        if os.path.isdir(artist_path):
            seen_files = set()
            for file_name in os.listdir(artist_path):
                old_path = os.path.join(artist_path, file_name)
                if os.path.isfile(old_path):
                    new_name = remove_leading_numbers(file_name)
                    if new_name not in seen_files:
                        seen_files.add(new_name)
                        new_path = os.path.join(artist_path, new_name)
                        os.rename(old_path, new_path)
                    else:
                        os.remove(old_path)

def update_m3u_files(main_folder):
    """
    Update all .m3u playlist files in the main folder to reflect updated paths.
    """
    for root, _, files in os.walk(main_folder):
        for file_name in files:
            if isinstance(file_name, str) and file_name.endswith(".m3u"):
                m3u_path = os.path.join(root, file_name)
                updated_lines = []
                with open(m3u_path, 'r', encoding='utf-8') as m3u_file:
                    for line in m3u_file:
                        if line.strip() and not line.startswith("#"):
                            parts = line.strip().split(os.sep)
                            parts[-1] = remove_leading_numbers(parts[-1])
                            updated_lines.append(os.path.join(*parts) + "\n")
                        else:
                            updated_lines.append(line)
                with open(m3u_path, 'w', encoding='utf-8') as m3u_file:
                    m3u_file.writelines(updated_lines)

def update_xml_files(main_folder):
    """
    Update all .xml playlist files in the main folder to reflect updated paths.
    """
    for root, _, files in os.walk(main_folder):
        for file_name in files:
            if isinstance(file_name, str) and file_name.endswith(".xml"):
                xml_path = os.path.join(root, file_name)
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for playlist_item in root.findall(".//PlaylistItem"):
                    path = playlist_item.find("Path")
                    if path is not None and isinstance(path.text, str):
                        parts = path.text.split(os.sep)
                        parts[-1] = remove_leading_numbers(parts[-1])
                        path.text = os.path.join(*parts)
                tree.write(xml_path, encoding='utf-8', xml_declaration=True)

def main():

    Tk().withdraw()  # Hide the main Tkinter window
    print("Select the folder containing the music files:")
    main_folder = askdirectory(title="Select Input Folder")
    if not main_folder:
        print("No input folder selected. Exiting.")
        exit()
    
    if not os.path.isdir(main_folder):
        print("Invalid folder path. Please try again.")
        return
    
    # Update artist folders
    print("Processing artist folders...")
    update_artist_folders(main_folder)
    
    # Update .m3u files
    print("Updating .m3u playlist files...")
    update_m3u_files(main_folder)
    
    # Update .xml files
    print("Updating .xml playlist files...")
    update_xml_files(main_folder)
    
    print("Processing completed!")

if __name__ == "__main__":
    main()
