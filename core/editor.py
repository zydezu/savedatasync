import json

from .config import read_locations
from .display import C
from .models import Save, Status


def _write_locations(saves: list[Save]) -> None:
    data = [{"name": s.name, "paths": s.paths} for s in saves]
    with open("locations.json", "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def add_save() -> bool:
    """Interactively append a new entry to locations.txt. Returns True if added."""
    print(f"\n  {C.CYAN}Add new save{C.RESET}")
    print(f"  {C.GRAY}Leave the name blank to cancel.{C.RESET}\n")

    name = input("  Name: ").strip()
    if not name:
        print(f"  {C.YELLOW}Cancelled.{C.RESET}")
        return False

    saves = read_locations()
    if any(s.name == name for s in saves):
        print(f"  {C.RED}'{name}' already exists.{C.RESET}")
        return False

    print(f"  {C.GRAY}Enter paths one per line, blank line when done:{C.RESET}")
    paths: list[str] = []
    while True:
        path = input("  Path: ").strip()
        if not path:
            break
        paths.append(path)

    if not paths:
        print(f"  {C.YELLOW}No paths entered, not saved.{C.RESET}")
        return False

    saves.append(Save(name=name, paths=paths))
    _write_locations(saves)
    print(f"  {C.GREEN}Added '{name}'.{C.RESET}")
    return True


def remove_save(statuses: list[Status]) -> bool:
    """Interactively remove an entry from locations.txt. Returns True if removed."""
    print(f"\n  {C.CYAN}Remove save{C.RESET}")
    print(f"  {C.GRAY}Enter a non-numeric value or leave blank to cancel.{C.RESET}\n")

    try:
        choice = int(input(f"  Number to remove (1-{len(statuses)}): ").strip())
    except (ValueError, EOFError):
        print(f"  {C.YELLOW}Cancelled.{C.RESET}")
        return False

    if not 1 <= choice <= len(statuses):
        print(f"  {C.RED}Invalid number.{C.RESET}")
        return False

    target = statuses[choice - 1].save
    confirm = input(f"  Remove '{target.name}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print(f"  {C.YELLOW}Cancelled.{C.RESET}")
        return False

    saves = [s for s in read_locations() if s.name != target.name]
    _write_locations(saves)
    print(f"  {C.GREEN}Removed '{target.name}'.{C.RESET}")
    return True
