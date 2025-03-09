import os
import shutil
import hashlib
from datetime import datetime

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

class Savelocation:
    def __init__(self, appname):
        assert (appname != ""), "Appname is empty, check formatting of locations.txt"
        self.appName = appname
        self.filePaths = []

    def __str__(self):
        return f"Checking application: {bcolors.OKGREEN}{self.appName}{bcolors.ENDC} | paths: {self.filePaths}"

    def addLocation(self, location):
        self.filePaths.append(location)

def calculateFolderHash(folderPath, algorithm='sha256', block_size=65536):
    """Calculate the hash of all files in a folder using the specified algorithm"""
    hash_object = hashlib.new(algorithm)
    for foldername, subfolders, filenames in os.walk(folderPath):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    hash_object.update(block)
    return hash_object.hexdigest()

def readLocationsFile():
    """Make a list of Savelocation instances and return it"""
    
    f = open("locations.txt", "r")
    lines = f.readlines()
    f.close()

    while len(lines) > 0 and lines[-1].strip() == "":
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
    else:
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files]
        return max(paths, key=os.path.getmtime)

def saveData(saveLocations, output=True):
    isaltered = False
    changed = []

    for save in saveLocations:
        if output: print(save)

        if (not save.filePaths):
            if output: print("There are no file paths for this item... skipping")
            continue

        for path in save.filePaths:
            if not os.path.isdir(path):
                if os.path.isfile(path):
                    if output: print("Is single file... continue")
                else:
                    if output: print("Path doesn't exist |", path)
                    if (path == save.filePaths[-1]):
                        if output: print(f"{bcolors.LINE}---------------------------------------------------------------------------{bcolors.ENDC}")
                    continue # skip to next path iteration

            pathHash = calculateFolderHash(path)
            try:
                fileTime = datetime.fromtimestamp(os.stat(newestFile(path)).st_mtime)
            except:
                fileTime = datetime.fromtimestamp(0)
                print("Folder is empty!")
            if output: print("File modified |", fileTime)
            fileInfoPath = os.path.join('saves', f'{save.appName}.txt')
            backupPath = os.path.join('backup', f'{save.appName} {fileTime.strftime("%Y-%m-%d_%H-%M-%S")}')
            if output: print("Save data hash |", pathHash)

            # check if an info file exists, and 
            # if it does read the hash from it
            oldHash = ""
            if (os.path.isfile(fileInfoPath)):
                with open(fileInfoPath, "r") as f:
                    lines = f.readlines()
                    oldHash = lines[1]
                    if output: print("Info file hash |", oldHash)
            else:
                if output: print("No info file |", fileInfoPath)

            if (oldHash != pathHash):
                if output: print(f"{bcolors.WARNING}Copying path |", path, f"{bcolors.ENDC}")

                isaltered = True
                changed.append(f"{save.appName} [{fileTime.strftime("%Y-%m-%d %H:%M.%S")}]")
                remove_folder(os.path.join('saves', save.appName))

                if os.path.isfile(path):
                    newdir = os.path.join('saves', save.appName)
                    if not os.path.exists(newdir): os.makedirs(newdir)
                    shutil.copy2(path, os.path.join('saves', save.appName))
                    pass
                else:
                    if output: print(f"{bcolors.WARNING}Compressing file...{bcolors.ENDC}")
                    shutil.make_archive(os.path.join('saves', save.appName), 'zip', path)  # zip file
                    fileSize = os.path.getsize(os.path.join('saves', f'{save.appName}.zip'))  # check file size of zip
                    if (fileSize > 100000000): # files above 100MB are too big for github, so just use the folder instead
                        if output: print("Zip is too big, using folder directory instead")
                        shutil.copytree(path, os.path.join('saves', save.appName), dirs_exist_ok=True)
                        os.remove(os.path.join('saves', f'{save.appName}.zip'))
                    

                newinfo = [str(fileTime) + "\n", pathHash]
                with open(fileInfoPath, 'w') as f:
                    f.writelines(newinfo)

                if output: print(f"{bcolors.WARNING}Backing up path |", path, f"{bcolors.ENDC}")
                remove_folder(backupPath)
                
                if os.path.isfile(path):
                    os.makedirs(backupPath)
                    shutil.copy2(path, backupPath)
                    with open(f'{backupPath}.txt', 'w') as f:
                        f.writelines(newinfo)
                else:
                    shutil.copytree(path, backupPath, dirs_exist_ok=True)
                    with open(f'{backupPath}.txt', 'w') as f:
                        f.writelines(newinfo)
            else:
                if output: print(f"{bcolors.WARNING}Files are the same... not copying files{bcolors.ENDC}")
            if output: print(f"{bcolors.LINE}---------------------------------------------------------------------------{bcolors.ENDC}")

    return isaltered, changed