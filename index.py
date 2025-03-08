import shutil
import os

# Source file path
source_file = 'index.html'

# Destination directory
destination_dir = 'templates'

# Check if the destination directory exists, if not create it
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)

# Construct the destination file path
destination_file = os.path.join(destination_dir, os.path.basename(source_file))

# Move the file
shutil.move(source_file, destination_file)

print(f"File moved to {destination_file}")
