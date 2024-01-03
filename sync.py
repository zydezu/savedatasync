from readFileLocations import *
from downloadSavesToGit import download
from uploadSavesToGit import upload
import shutil
import time

def remove_folder(path):
    try:
        shutil.rmtree(path, True)
    except Exception as e:
        print(f"Error removing folder {path}: {e}")

def print_separator():
    print("=" * 75)

def main():
    # update local files and times
    print_separator()
    print("\nChecking each application's save data for changes\n")
    print_separator()

    saveLocations = readLocationsFile()
    is_altered, changed = saveData(saveLocations)

    # download synced files to see if they're newer
    print_separator()
    print("\nDOWNLOAD\n")
    try:
        download()
    except:
        remove_folder("temp")

    # upload the changes
    print("\nUPLOAD\n")
    print_separator()
    upload(is_altered, changed, False)

    print("Done!")
    print("Closing in 5 seconds...")
    print_separator()
    time.sleep(5)

if __name__ == "__main__":
    main()