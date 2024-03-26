from readFileLocations import *
import shutil
import os
import urllib.request

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

def download():
    def normalisedSize(bytes, units=[' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']):
        if bytes < 1024 or len(units) == 1:
            return f"{round(bytes, 2):.2f}{units[0]}"
        else:
            return normalisedSize(bytes / 1024, units[1:])

    def downloadRepoFile(url):
        print(f"{bcolors.WARNING}Downloading files from github...{bcolors.ENDC}")
        urllib.request.urlretrieve(url, "main.zip")
        fileSize = os.path.getsize("main.zip")
        print(f"{bcolors.WARNING}Size: {normalisedSize(fileSize)}{bcolors.ENDC}")
        shutil.unpack_archive("main.zip", "temp", "zip")
        print(f"{bcolors.WARNING}Cleaning up...{bcolors.ENDC}")
        os.remove("main.zip")

    filepath = ""
    with open("gitFilePath.txt", "r") as f:
        filepath = f.readline()
    saveLocations = readLocationsFile()
    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

    downloadRepoFile(filepath)
    shutil.rmtree("tocheck", True)
    shutil.copytree(os.path.join("temp","savedatasync-main","saves"), "tocheck", dirs_exist_ok=True)
    shutil.rmtree("temp", True)
    print("Done!")

    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")
    print(f"{bcolors.OKBLUE}Checking whether to update local save data{bcolors.ENDC}")
    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

    for foldername, subfolders, filenames in os.walk("tocheck"):
        ### unzip zip files
        for file in filenames:
            if (file.lower().endswith(".zip")):
                shutil.unpack_archive(os.path.join("tocheck", file), os.path.join("tocheck", file.removesuffix(".zip")), "zip")

    updatedApps = []

    for foldername, subfolders, filenames in os.walk("tocheck"):
        for folder in subfolders:
            print(f"Checking save data |{bcolors.OKGREEN}", folder, f"{bcolors.ENDC}")
            f = open(os.path.join("tocheck", folder+".txt"), "r")
            lines = f.readlines()
            downloadeddate = lines[0].strip()
            downloadedhash = lines[1].strip()
            print("Downloaded file hash |", downloadeddate)
            print("Downloaded file hash |", downloadedhash)
            f.close()

            currentdate = ""
            currenthash = ""
            try:
                with open(os.path.join("saves", folder+".txt"), "r") as f:
                    lines = f.readlines()
                    currentdate = lines[0].strip()
                    currenthash = lines[1].strip()
                print("Current file date |", currentdate)
                print("Current file hash |", currenthash)
            except:
                currentdate = "0000-00-00 00:00:00.000000"
                currenthash = ""

            if (downloadedhash == currenthash):
                print(f"{bcolors.WARNING}Files are the same... not overriding files{bcolors.ENDC}")
            else:
                if (downloadeddate > currentdate):
                    print("Downloaded files are newer... overriding files")
                    shutil.copytree(os.path.join("tocheck", folder), os.path.join("saves", folder), dirs_exist_ok=True)
                    with open(os.path.join("saves", folder+".txt"), 'w') as f:
                        f.write(downloadeddate + "\n")
                        f.write(downloadedhash)

                    for save in saveLocations:
                        if (save.appName == folder):
                            for path in save.filePaths:
                                if os.path.isdir(path):
                                    updatedApps.append(save.appName)
                                    shutil.copytree(os.path.join("saves", folder), path, dirs_exist_ok=True)
                                    break
                                if os.path.isfile(path):
                                    updatedApps.append(save.appName)
                                    shutil.copy2(os.path.join("saves", folder, os.listdir(os.path.join("saves", folder)[0])), path)
                                    break
                else:
                    print(f"{bcolors.WARNING}Downloaded files are older... not overriding files{bcolors.ENDC}")
            print(f"{bcolors.LINE}---------------------------------------------------------------------------{bcolors.ENDC}")

        shutil.rmtree("tocheck")

    if (updatedApps):
        if len(updatedApps) > 1:
            updatedString = f"{", ".join(updatedApps[:-1])}, and {updatedApps[-1]}"
            print(f"{bcolors.OKBLUE}",updatedString,f"now have the newest save data{bcolors.ENDC}")
        else:
            updatedString = updatedApps[0]
            print(f"{bcolors.OKBLUE}",updatedString,f"now has the newest save data{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKBLUE}Nothing has been overwritten{bcolors.ENDC}")
    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

if __name__ == "__main__":
    download()
    print("Press ENTER to close")
    input()