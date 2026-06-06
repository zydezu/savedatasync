import time

from downloadSavesToGit import download
from readFileLocations import (
    bcolors,
    print_separator,
    readLocationsFile,
    remove_folder,
    saveData,
)
from uploadSavesToGit import upload


def main():
    print_separator()
    print(
        f"\n{bcolors.OKCYAN}Checking each application's save data for changes\n{bcolors.ENDC}"
    )
    print_separator()

    saveLocations = readLocationsFile()
    is_altered, changed = saveData(saveLocations)

    print_separator()
    print(f"\n{bcolors.OKCYAN}DOWNLOAD{bcolors.ENDC}\n")
    try:
        download()
    except Exception:
        remove_folder("temp")

    print(f"\n{bcolors.OKCYAN}UPLOAD{bcolors.ENDC}\n")
    upload(is_altered, changed)

    print(f"{bcolors.OKBLUE}Done!{bcolors.ENDC}")
    print(f"{bcolors.WARNING}Closing in 5 seconds...{bcolors.ENDC}")
    print_separator()
    time.sleep(5)


if __name__ == "__main__":
    main()
