from readFileLocations import *
import shutil
import os
import urllib.request

def download():
    def normalisedSize(bytes, units=[' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']):
        if bytes < 1024 or len(units) == 1:
            return f"{round(bytes, 2):.2f}{units[0]}"
        else:
            return normalisedSize(bytes / 1024, units[1:])

    def downloadRepoFile(url):
        print("Downloading files from github...")
        urllib.request.urlretrieve(url, "main.zip")
        fileSize = os.path.getsize("main.zip")
        print(f"Size: {normalisedSize(fileSize)}")
        shutil.unpack_archive("main.zip", "temp", "zip")
        print("Cleaning up...")
        os.remove("main.zip")

    filepath = ""
    with open("gitFilePath.txt", "r") as f:
        filepath = f.readline()
    saveLocations = readLocationsFile()
    print("===========================================================================")

    downloadRepoFile(filepath)
    shutil.rmtree("tocheck", True)
    shutil.copytree(os.path.join("temp","savedatasync-main","saves"), "tocheck", dirs_exist_ok=True)
    shutil.rmtree("temp", True)
    print("Done!")

    print("===========================================================================")
    print("Checking whether to update local save data")
    print("===========================================================================")

    for foldername, subfolders, filenames in os.walk("tocheck"):
        ### unzip zip files
        for file in filenames:
            if (file.lower().endswith(".zip")):
                shutil.unpack_archive(os.path.join("tocheck", file), os.path.join("tocheck", file.removesuffix(".zip")), "zip")

    updatedApps = []

    for foldername, subfolders, filenames in os.walk("tocheck"):
        for folder in subfolders:
            print("Checking save data |", folder)
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
                print("Files are the same... not overriding files")
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
                else:
                    print("Downloaded files are older... not overriding files")
            print("---------------------------------------------------------------------------")

        shutil.rmtree("tocheck")

    if (updatedApps):
        if len(updatedApps) > 1:
            updatedString = f"{", ".join(updatedApps[:-1])}, and {updatedApps[-1]}"
            print(updatedString,"now have the newest save data")
        else:
            updatedString = updatedApps[0]
            print(updatedString,"now has the newest save data")
    else:
        print("Nothing has been overwritten")
    print("===========================================================================")

if __name__ == "__main__":
    download()
    print("Press ENTER to close")
    input()