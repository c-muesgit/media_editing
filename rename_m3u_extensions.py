import os
from tkinter import Tk
from tkinter.filedialog import askopenfile

def rename_ext(file_path, new_extension, save_to_new_file=True):
    # Open the file and read lines
    with open(file_path, "r") as input_file:
        lines = input_file.readlines()

    # Create a list to store modified lines
    modified_lines = []

    for line in lines:
        # Clean up the line
        cleaned_line = line.strip()
        # Check if the line has a file extension
        if '.' in cleaned_line:
            base, ext = os.path.splitext(cleaned_line)  # Split the base name and extension
            modified_line = base + new_extension       # Replace with the new extension
            modified_lines.append(modified_line)       # Store the modified line
        else:
            # If no extension, keep the line as is
            modified_lines.append(cleaned_line)

    # Determine where to save the changes
    if save_to_new_file:
        new_file_path = file_path.replace(".m3u", "_modified.m3u")  # Create a new file name
        with open(new_file_path, "w") as output_file:
            output_file.write("\n".join(modified_lines) + "\n")
        print(f"Modified file saved as: {new_file_path}")
    else:
        # Overwrite the original file
        with open(file_path, "w") as output_file:
            output_file.write("\n".join(modified_lines) + "\n")
        print(f"Original file overwritten: {file_path}")


def main():

    Tk().withdraw()  # Hide the main Tkinter window
    file = askopenfile(title="Select input file")  # Ask for a file
    if file:
        file_path = file.name  # Extract the file path
        file.close()  # Close the file object

        # Ask the user for the new extension
        new_extension = input("Enter the new file extension (e.g., .m4a): ").strip()
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension  # Ensure it starts with a dot

        # Ask if the user wants to overwrite the original file
        save_option = input("Overwrite the original file? (yes/no): ").strip().lower()
        overwrite = save_option in ["yes", "y"]

        # Call the rename function with the appropriate option
        rename_ext(file_path, new_extension, save_to_new_file=not overwrite)


if __name__ == "__main__":
    main()
