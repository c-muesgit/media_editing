#update
import os
import re
import xml.etree.ElementTree as ET

def normalize_filename(filename):
    """Remove artist prefix like 'Artist - ' for normalization purposes."""
    return re.sub(r'^[^/\\]* -  ', '', filename).lower()

def parse_xml_playlist(xml_file):
    """Extract playlist items and their full paths from an XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        playlist_items = [
            item.find('Path') for item in root.find('PlaylistItems')
        ]
        return tree, root, playlist_items
    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
        return None, None, []

def update_playlist_item(path_element, new_filename):
    """Update the Path element in the XML with the new filename."""
    directory = os.path.dirname(path_element.text)
    path_element.text = os.path.join(directory, new_filename)

def process_xml_playlists(xml_folder, music_database_dir):
    # Collect all XML files
    xml_files = [
        os.path.join(subdir, file)
        for subdir, _, files in os.walk(xml_folder)
        for file in files if file.endswith(".xml")
    ]

    # Collect all music database files
    database_files = [
        os.path.join(subdir, file)
        for subdir, _, files in os.walk(music_database_dir)
        for file in files
    ]

    # Normalize database filenames for comparison
    normalized_database_files = {
        normalize_filename(os.path.basename(file)): file for file in database_files
    }

    for xml_file in xml_files:
        print(f"\nProcessing playlist: {xml_file}")
        tree, root, playlist_items = parse_xml_playlist(xml_file)
        if not tree or not playlist_items:
            continue

        changes_made = False

        for path_element in playlist_items:
            original_path = path_element.text
            original_filename = os.path.basename(original_path)
            normalized_original = normalize_filename(original_filename)

            # Check for a match in the database
            if normalized_original in normalized_database_files:
                print(f"Match found: {original_path} -> {normalized_database_files[normalized_original]}")
            else:
                # Normalize to {title}.extension while retaining original directory
                normalized_filename = re.sub(r'^[^/\\]* -  ', '', original_filename)
                update_playlist_item(path_element, normalized_filename)
                print(f"No match found. Normalized: {original_filename} -> {normalized_filename}")
                changes_made = True

        # Save changes back to the XML file
        if changes_made:
            tree.write(xml_file)
            print(f"Saved changes to {xml_file}")
        else:
            print("No changes made to this playlist.")


# Path to the folder containing XML files and the music database directory
xml_folder_path = 'C:/Users/Caleb/Desktop/m3u/XML Playlists'
music_database_path = 'C:/Users/Caleb/Desktop/Rachel_Music'
process_xml_playlists(xml_folder_path, music_database_path)
