import os
import shutil

def resolve_music_file_path(source_dir, m3u_dir, line):
    """
    Resolve the file path from the .m3u entry.
    Handles both relative and absolute paths.
    """
    line = line.strip().strip('"').strip()

    # Check if the line is an absolute path
    if os.path.isabs(line):
        return os.path.normpath(line)
    
    # Otherwise, treat it as a relative path from the .m3u file's directory
    return os.path.normpath(os.path.join(m3u_dir, line))

def copy_music_from_m3u(source_dir, target_dir):
    """
    Copies music files listed in .m3u files from the source directory
    to the target directory.

    Args:
        source_dir (str): The path to the main folder containing .m3u files and music subfolders.
        target_dir (str): The path to the folder where the music should be copied.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Iterate through all files in the source directory
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.m3u'):
                m3u_path = os.path.join(root, file)
                print(f"Processing playlist: {m3u_path}")

                # Read the .m3u file and collect referenced file paths
                with open(m3u_path, 'r', encoding='utf-8') as m3u_file:
                    for line in m3u_file:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue

                        # Resolve the file path
                        music_file_path = resolve_music_file_path(source_dir, root, line)

                        print(f"Resolved path: {music_file_path}")

                        if os.path.exists(music_file_path):
                            # Ensure the target folder structure is preserved
                            rel_path = os.path.relpath(music_file_path, source_dir)
                            target_path = os.path.join(target_dir, rel_path)
                            target_folder = os.path.dirname(target_path)

                            # Create target folders if they don't exist
                            if not os.path.exists(target_folder):
                                os.makedirs(target_folder)
                            
                            # Copy the file to the target location
                            shutil.copy2(music_file_path, target_path)
                            print(f"Copied: {music_file_path} -> {target_path}")
                        else:
                            print(f"File not found: {music_file_path}")

if __name__ == "__main__":
    # Input paths from the user
    source_dir = '/Users/calebmueller/Library/CloudStorage/OneDrive-UNBC/Music/ALAC iPod Music'
    target_dir = '/Users/calebmueller/Desktop/Filtered ALAC'
    copy_music_from_m3u(source_dir, target_dir)
