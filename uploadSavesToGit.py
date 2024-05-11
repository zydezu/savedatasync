import subprocess
from readFileLocations import *

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

def upload(overrideAltered, overrideChangedMessage, output=True):
    if output: print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")
    if output: print(f"{bcolors.OKBLUE}Checking each application's save data for changes")
    if output: print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")
    
    saveLocations = readLocationsFile()
    isaltered, changed = saveData(saveLocations, output)
    if overrideAltered:
        isaltered = overrideAltered
    if overrideChangedMessage:
        changed = overrideChangedMessage

    changedString = "update repo"
    if (isaltered):
        if len(changed) > 1:
            changedString = f"{", ".join(changed[:-1])}, and {changed[-1]}"
            print(f"{bcolors.OKBLUE}",changedString,f"have been updated{bcolors.ENDC}")
        else:
            changedString = changed[0]
            print(f"{bcolors.OKBLUE}" + changedString + f" has been updated{bcolors.ENDC}")
        changedString = f"updated savefiles: {changedString}"
    else:
        print(f"{bcolors.OKBLUE}No save data has changed!{bcolors.ENDC}")

    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")
    print("Checking git repo status...")
    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

    for i in range(0,2):
        print(i)
        subprocess.call(["git", "pull"])
        subprocess.call(["git", "add", "."])
        subprocess.call(["git", "commit", "-m", changedString])
        subprocess.call(["git", "push"])

    print(f"{bcolors.LINE}==========================================================================={bcolors.ENDC}")

if __name__ == "__main__":
    upload()
    print("Press ENTER to close")
    input()