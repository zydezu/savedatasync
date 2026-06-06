import hashlib
import os
import shutil
from datetime import datetime


class bcolors:
    LINE = "\033[90m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_separator(char="="):
    line = char * 75
    print(f"{bcolors.LINE}{line}{bcolors.ENDC}")


class Savelocation:
    def __init__(self, appname):
        assert appname != "", "Appname is empty, check formatting of locations.txt"
        self.appName = appname
        self.filePaths = []

    def __str__(self):
        return f"Checking application: {bcolors.OKGREEN}{self.appName}{bcolors.ENDC} | paths: {self.filePaths}"

    def addLocation(self, location):
        self.filePaths.append(location)


def calculateFolderHash(folderPath, algorithm="sha256", block_size=65536):
    hash_object = hashlib.new(algorithm)
    for foldername, subfolders, filenames in os.walk(folderPath):
        subfolders.sort()
        for filename in sorted(filenames):
            file_path = os.path.join(foldername, filename)
            with open(file_path, "rb") as f:
                for block in iter(lambda: f.read(block_size), b""):
                    hash_object.update(block)
    return hash_object.hexdigest()


def readLocationsFile():
    with open("locations.txt", "r") as f:
        lines = f.readlines()

    while lines and lines[-1].strip() == "":
        lines.pop()

    saveLocations = []
    currentSaveLocation = None
    blank = True
    for line in lines:
        linestripped = line.strip()
        if blank:
            currentSaveLocation = Savelocation(linestripped)
            blank = False
        elif len(linestripped) <= 1:
            blank = True
            saveLocations.append(currentSaveLocation)
        else:
            currentSaveLocation.addLocation(linestripped)

    if not blank:
        saveLocations.append(currentSaveLocation)

    return saveLocations


def remove_folder(path):
    try:
        shutil.rmtree(path, True)
    except Exception as e:
        print(f"Error removing folder {path}: {e}")


def newestFile(path):
    if os.path.isfile(path):
        return path
    newest = None
    newest_mtime = -1
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            fpath = os.path.join(dirpath, filename)
            mtime = os.path.getmtime(fpath)
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest = fpath
    return newest


def saveData(saveLocations, output=True):
    isaltered = False
    changed = []

    for save in saveLocations:
        if output:
            print(save)

        if not save.filePaths:
            if output:
                print("There are no file paths for this item... skipping")
            continue

        for path in save.filePaths:
            if not os.path.isdir(path):
                if os.path.isfile(path):
                    if output:
                        print("Is single file... continue")
                else:
                    if output:
                        print("Path doesn't exist |", path)
                    if path == save.filePaths[-1]:
                        if output:
                            print_separator("-")
                    continue

            pathHash = calculateFolderHash(path)
            try:
                fileTime = datetime.fromtimestamp(os.stat(newestFile(path)).st_mtime)
            except Exception:
                fileTime = datetime.fromtimestamp(0)
                print("Folder is empty!")
            if output:
                print("File modified |", fileTime)
            fileInfoPath = os.path.join("saves", f"{save.appName}.txt")
            backupPath = os.path.join(
                "backup", f"{fileTime.strftime('%Y-%m-%d_%H-%M-%S')} {save.appName}"
            )
            if output:
                print("Save data hash |", pathHash)

            oldHash = ""
            if os.path.isfile(fileInfoPath):
                with open(fileInfoPath, "r") as f:
                    lines = f.readlines()
                    oldHash = lines[1]
                    if output:
                        print("Info file hash |", oldHash)
            else:
                if output:
                    print("No info file |", fileInfoPath)

            if oldHash != pathHash:
                if output:
                    print(f"{bcolors.WARNING}Copying path |", path, f"{bcolors.ENDC}")

                isaltered = True
                changed.append(
                    f"{save.appName} [{fileTime.strftime('%Y-%m-%d %H:%M.%S')}]"
                )
                remove_folder(os.path.join("saves", save.appName))

                if os.path.isfile(path):
                    newdir = os.path.join("saves", save.appName)
                    if not os.path.exists(newdir):
                        os.makedirs(newdir)
                    shutil.copy2(path, os.path.join("saves", save.appName))
                else:
                    if output:
                        print(f"{bcolors.WARNING}Compressing file...{bcolors.ENDC}")
                    shutil.make_archive(
                        os.path.join("saves", save.appName), "zip", path
                    )
                    fileSize = os.path.getsize(
                        os.path.join("saves", f"{save.appName}.zip")
                    )
                    if fileSize > 100000000:
                        if output:
                            print("Zip is too big, using folder directory instead")
                        shutil.copytree(
                            path,
                            os.path.join("saves", save.appName),
                            dirs_exist_ok=True,
                        )
                        os.remove(os.path.join("saves", f"{save.appName}.zip"))

                newinfo = [str(fileTime) + "\n", pathHash]
                with open(fileInfoPath, "w") as f:
                    f.writelines(newinfo)

                if output:
                    print(
                        f"{bcolors.WARNING}Backing up path |", path, f"{bcolors.ENDC}"
                    )
                remove_folder(backupPath)

                if os.path.isfile(path):
                    os.makedirs(backupPath)
                    shutil.copy2(path, backupPath)
                    with open(f"{backupPath}.txt", "w") as f:
                        f.writelines(newinfo)
                else:
                    shutil.copytree(path, backupPath, dirs_exist_ok=True)
                    with open(f"{backupPath}.txt", "w") as f:
                        f.writelines(newinfo)
            else:
                if output:
                    print(
                        f"{bcolors.WARNING}Files are the same... not copying files{bcolors.ENDC}"
                    )
            if output:
                print_separator("-")

    return isaltered, changed
