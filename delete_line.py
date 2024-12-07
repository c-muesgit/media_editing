input_file = '/Users/calebmueller/Library/CloudStorage/OneDrive-UNBC/Music/iPod Music/Best.m3u'
output_file = '/Users/calebmueller/Library/CloudStorage/OneDrive-UNBC/Music/iPod Music/Best_edit.m3u'

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        # Write the line to the output file if it doesn't start with a number
        if not line.lstrip().startswith(tuple("0123456789")):
            outfile.write(line)

print(f"Filtered playlist saved to {output_file}")
