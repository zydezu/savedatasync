from readFileLocations import *
from downloadSavesToGit import download
from uploadSavesToGit import upload
import shutil
import time

os.system("")
class bcolors:
    LINE = '\033[90m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def remove_folder(path):
    try:
        shutil.rmtree(path, True)
    except Exception as e:
        print(f"{bcolors.WARNING}Error removing folder {path}: {e}{bcolors.ENDC}")

def print_separator():
    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

def main():
    # update local files and times
    print_separator()
    print(f"\n{bcolors.OKCYAN}Checking each application's save data for changes\n{bcolors.ENDC}")
    print_separator()

    saveLocations = readLocationsFile()
    is_altered, changed = saveData(saveLocations)

    # download synced files to see if they're newer
    print_separator()
    print(f"\n{bcolors.OKCYAN}DOWNLOAD{bcolors.ENDC}\n")
    try:
        download()
    except:
        remove_folder("temp")

    # upload the changes
    print(f"\n{bcolors.OKCYAN}UPLOAD{bcolors.ENDC}\n")
    print_separator()
    upload(is_altered, changed, False)

    print(f"{bcolors.OKBLUE}Done!{bcolors.ENDC}")
    print(f"{bcolors.WARNING}Closing in 5 seconds...{bcolors.ENDC}")
    print_separator()
    time.sleep(5)

if __name__ == "__main__":
    main()