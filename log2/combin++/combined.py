import os
import glob

folder_path = "."
output_file = "combined.txt"

with open(output_file, 'w', encoding='utf-8') as outfile:
    for filepath in sorted(glob.glob(os.path.join(folder_path, "*.txt"))):
        with open(filepath, 'r', encoding='utf-8') as infile:
            outfile.write(f"===== {os.path.basename(filepath)} =====\n")
            outfile.write(infile.read())
            outfile.write("\n\n")