import os
import xml.etree.ElementTree as ET
from datetime import datetime

# Updated function

def convert_m3u_to_xml(input_folder, jellyfin_path, owner):
    m3u_files = []
    for (path, directories, files) in os.walk(input_folder):
        for file in files:
            if file.endswith(".m3u"):
                m3u = os.path.join(path, file)
                playlist_name = os.path.splitext(os.path.basename(m3u))[0]
                
                # Create the root Item element
                playlist = ET.Element("Item")
                
                # Add sub-elements with proper formatting
                ET.SubElement(playlist, "Added").text = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                ET.SubElement(playlist, "LockData").text = "false"
                ET.SubElement(playlist, "LocalTitle").text = playlist_name
                ET.SubElement(playlist, "RunningTime").text = "365"

                # Genres element
                genres = ET.SubElement(playlist, "Genres")
                ET.SubElement(genres, "Genre").text = "Alternative"
                ET.SubElement(genres, "Genre").text = "Indie"

                ET.SubElement(playlist, "OwnerUserId").text = owner

                # PlaylistItems element
                playlist_items_element = ET.SubElement(playlist, "PlaylistItems")
                
                with open(m3u, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()  # Remove trailing whitespace or newlines
                        if line:  # Skip empty lines
                            relative_path = line.replace('\\', '/')  # Ensure proper path formatting
                            playlist_item = ET.SubElement(playlist_items_element, "PlaylistItem")
                            ET.SubElement(playlist_item, "Path").text = f"{jellyfin_path}/{relative_path}"

                ET.SubElement(playlist, "Shares")
                ET.SubElement(playlist, "PlaylistMediaType").text = "Audio"

                # Write XML to file with pretty formatting
                tree = ET.ElementTree(playlist)
                os.makedirs(os.path.join(input_folder, 'XML Playlists', playlist_name), exist_ok=True)
                output_folder = os.path.join(input_folder, 'XML Playlists', playlist_name)
                xml_output_path = os.path.join(output_folder, 'playlist.xml')

                with open(xml_output_path, 'wb') as xml_file:
                    tree.write(xml_file, encoding="utf-8", xml_declaration=True)

                # Reformat the XML to include indentation
                reformat_xml(xml_output_path)

                print(f"XML playlist generated at {xml_output_path}")


def reformat_xml(file_path):
    """Reformats the XML file with proper indentation and standalone attribute."""
    import xml.dom.minidom as minidom

    with open(file_path, 'r', encoding='utf-8') as file:
        raw_xml = file.read()

    dom = minidom.parseString(raw_xml)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Add standalone="yes" to the XML declaration
    if "<?xml version=" in pretty_xml:
        pretty_xml = pretty_xml.replace("<?xml version=\"1.0\" ?>", "<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(pretty_xml)

# Example usage
input_folder = "C:/Users/Caleb/Desktop/m3u"
jellyfin_path = "/data/rachels_music"
owner_ID = '2957cc453ab64a2bad36f71b7196b1d4'
convert_m3u_to_xml(input_folder, jellyfin_path, owner_ID)
