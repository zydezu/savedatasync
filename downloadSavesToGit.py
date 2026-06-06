import os
import shutil
import urllib.request

from readFileLocations import (
    bcolors,
    print_separator,
    readLocationsFile,
)


def _human_size(n: float) -> str:
    for unit in (" bytes", "KB", "MB", "GB", "TB", "PB", "EB"):
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f} EB"


def download():
    with open("gitFilePath.txt") as f:
        url = f.readline().strip()

    saves = {s.appName: s for s in readLocationsFile()}
    print_separator()

    print(f"{bcolors.WARNING}Downloading files from github...{bcolors.ENDC}")
    urllib.request.urlretrieve(url, "main.zip")
    print(
        f"{bcolors.WARNING}Size: {_human_size(os.path.getsize('main.zip'))}{bcolors.ENDC}"
    )
    shutil.unpack_archive("main.zip", "temp", "zip")
    os.remove("main.zip")
    shutil.rmtree("tocheck", True)
    shutil.copytree(
        os.path.join("temp", "savedatasync-main", "saves"),
        "tocheck",
        dirs_exist_ok=True,
    )
    shutil.rmtree("temp", True)
    print("Done!")

    print_separator()
    print(f"{bcolors.OKBLUE}Checking whether to update local save data{bcolors.ENDC}")
    print_separator()

    for _, _, filenames in os.walk("tocheck"):
        for name in filenames:
            if name.lower().endswith(".zip"):
                shutil.unpack_archive(
                    os.path.join("tocheck", name),
                    os.path.join("tocheck", name.removesuffix(".zip")),
                    "zip",
                )
        break  # top-level only

    updated = []

    for _, subfolders, _ in os.walk("tocheck"):
        for folder in subfolders:
            print(f"Checking save data | {bcolors.OKGREEN}{folder}{bcolors.ENDC}")

            with open(os.path.join("tocheck", folder + ".txt")) as f:
                lines = f.readlines()
            dl_date = lines[0].strip()
            dl_hash = lines[1].strip()
            print("Downloaded file date |", dl_date)
            print("Downloaded file hash |", dl_hash)

            try:
                with open(os.path.join("saves", folder + ".txt")) as f:
                    lines = f.readlines()
                cur_date = lines[0].strip()
                cur_hash = lines[1].strip()
                print("Current file date |", cur_date)
                print("Current file hash |", cur_hash)
            except Exception:
                cur_date = "0000-00-00 00:00:00.000000"
                cur_hash = ""

            if dl_hash == cur_hash:
                print(
                    f"{bcolors.WARNING}Files are the same... not overriding files{bcolors.ENDC}"
                )
            elif dl_date > cur_date:
                print("Downloaded files are newer... overriding files")
                shutil.copytree(
                    os.path.join("tocheck", folder),
                    os.path.join("saves", folder),
                    dirs_exist_ok=True,
                )
                with open(os.path.join("saves", folder + ".txt"), "w") as f:
                    f.write(dl_date + "\n")
                    f.write(dl_hash)

                save = saves.get(folder)
                if save:
                    for path in save.filePaths:
                        if os.path.isdir(path):
                            updated.append(save.appName)
                            shutil.copytree(
                                os.path.join("saves", folder), path, dirs_exist_ok=True
                            )
                            break
                        if os.path.isfile(path):
                            files = os.listdir(os.path.join("saves", folder))
                            if files:
                                shutil.copy2(
                                    os.path.join("saves", folder, files[0]), path
                                )
                            updated.append(save.appName)
                            break
            else:
                print(
                    f"{bcolors.WARNING}Downloaded files are older... not overriding files{bcolors.ENDC}"
                )

            print_separator("-")
        break  # top-level only

    shutil.rmtree("tocheck", True)

    if updated:
        noun = "have" if len(updated) > 1 else "has"
        names = (
            f"{', '.join(updated[:-1])}, and {updated[-1]}"
            if len(updated) > 1
            else updated[0]
        )
        print(f"{bcolors.OKBLUE}{names} now {noun} the newest save data{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKBLUE}Nothing has been overwritten{bcolors.ENDC}")
    print_separator()


if __name__ == "__main__":
    download()
    print("Press ENTER to close")
    input()
