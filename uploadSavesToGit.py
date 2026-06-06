import subprocess

from readFileLocations import (
    bcolors,
    print_separator,
    readLocationsFile,
    saveData,
)


def upload(is_altered=None, changed=None):
    if is_altered is None:
        print_separator()
        print(
            f"{bcolors.OKBLUE}Checking each application's save data for changes{bcolors.ENDC}"
        )
        print_separator()
        saveLocations = readLocationsFile()
        is_altered, changed = saveData(saveLocations)

    if is_altered:
        label = (
            f"{', '.join(changed[:-1])}, and {changed[-1]}"
            if len(changed) > 1
            else changed[0]
        )
        noun = "have" if len(changed) > 1 else "has"
        print(f"{bcolors.OKBLUE}{label} {noun} been updated{bcolors.ENDC}")
        commit_msg = f"Updated save files: {label}"
    else:
        print(f"{bcolors.OKBLUE}No save data has changed!{bcolors.ENDC}")
        commit_msg = "update save files"

    print_separator()
    print("Checking git repo status...")
    print_separator()

    subprocess.call(["git", "pull"])
    subprocess.call(["git", "add", "."])
    rc = subprocess.call(["git", "commit", "-m", f"AUTOMATED: {commit_msg}"])
    if rc == 0:
        subprocess.call(["git", "push"])

    print_separator()


if __name__ == "__main__":
    upload()
    print("Press ENTER to close")
    input()
