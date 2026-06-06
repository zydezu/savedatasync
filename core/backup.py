import os
import shutil
from dataclasses import dataclass
from datetime import datetime

from .config import read_locations
from .display import C, clear_screen, getch, print_header
from .utils import dir_size, human_size, rmdir

PAGE_SIZE = 15


@dataclass
class Backup:
    save_name: str
    time: datetime
    path: str


def _scan() -> list[Backup]:
    if not os.path.isdir("backup"):
        return []
    backups: list[Backup] = []
    for entry in os.listdir("backup"):
        full = os.path.join("backup", entry)
        if not os.path.isdir(full) or len(entry) < 20 or entry[19] != " ":
            continue
        try:
            dt = datetime.strptime(entry[:19], "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue
        backups.append(Backup(save_name=entry[20:], time=dt, path=full))
    return sorted(backups, key=lambda b: b.time, reverse=True)


def _display(backups: list[Backup], page: int, total_pages: int) -> None:
    print()
    if not backups:
        print(f"  {C.GRAY}No backups found.{C.RESET}")
        print()
        return

    start = page * PAGE_SIZE
    page_items = backups[start : start + PAGE_SIZE]

    all_names = [b.save_name for b in backups]
    w = max(len(n) for n in all_names) + 2

    print(
        f"  {C.BOLD}{'#':>2}  {'Save':<{w}}  {'Date & Time':<19}  {'Size':<10}{C.RESET}"
    )
    print(f"  {C.GRAY}{'─' * 2}  {'─' * w}  {'─' * 19}  {'─' * 10}{C.RESET}")

    for i, b in enumerate(page_items, start + 1):
        ts = b.time.strftime("%Y-%m-%d %H:%M:%S")
        size = human_size(dir_size(b.path))
        print(f"  {C.GRAY}{i:>2}{C.RESET}  {b.save_name:<{w}}  {ts}  {size}")

    for _ in range(PAGE_SIZE - len(page_items)):
        print()

    page_label = f"Page {page + 1}/{total_pages}"
    print(f"  {C.GRAY}{page_label}{C.RESET}")

    total_size = human_size(sum(dir_size(b.path) for b in backups))
    unique_saves = len(set(b.save_name for b in backups))
    print(
        f"  {C.GRAY}{len(backups)} backups • {unique_saves} unique saves • {total_size} total{C.RESET}"
    )
    print()


def _restore(backup: Backup) -> None:
    save_dir = os.path.join("saves", backup.save_name)
    rmdir(save_dir)
    shutil.copytree(backup.path, save_dir)

    info_src = backup.path + ".txt"
    if os.path.exists(info_src):
        shutil.copy2(info_src, os.path.join("saves", f"{backup.save_name}.txt"))

    saves = read_locations()
    save = next((s for s in saves if s.name == backup.save_name), None)
    if save is None:
        print(
            f"  {C.YELLOW}'{backup.save_name}' not in locations.json — staged in saves/ but not copied to game path.{C.RESET}"
        )
        return

    for path in save.paths:
        if os.path.isdir(path):
            shutil.copytree(save_dir, path, dirs_exist_ok=True)
            print(f"  {C.GREEN}Restored '{backup.save_name}' → {path}{C.RESET}")
            return
        if os.path.isfile(path):
            files = os.listdir(save_dir)
            if files:
                shutil.copy2(os.path.join(save_dir, files[0]), path)
            print(f"  {C.GREEN}Restored '{backup.save_name}' → {path}{C.RESET}")
            return

    print(
        f"  {C.YELLOW}No valid path found for '{backup.save_name}' — staged in saves/ only.{C.RESET}"
    )


def browse_backups() -> None:
    page = 0

    while True:
        clear_screen()
        print_header()
        backups = _scan()
        total_pages = max(1, -(-len(backups) // PAGE_SIZE))  # ceil division
        page = min(page, total_pages - 1)

        _display(backups, page, total_pages)

        opts: list[str] = []
        if total_pages > 1:
            opts.append(f"[{C.YELLOW}←{C.RESET}/{C.YELLOW}→{C.RESET}] page")
        if backups:
            opts.append(f"[{C.YELLOW}R{C.RESET}]estore")
        opts.append(f"[{C.YELLOW}Q{C.RESET}]uit/back")
        print("  " + "   ".join(opts))
        print()

        key = getch()

        if key == "q":
            break
        elif key in ("right", "n") and page < total_pages - 1:
            page += 1
        elif key in ("left", "p") and page > 0:
            page -= 1
        elif key == "r" and backups:
            clear_screen()
            print_header()
            _display(backups, page, total_pages)

            raw = input(
                f"  Restore number\n  {C.GRAY}Leave blank to cancel{C.RESET}\n  (1-{len(backups)}):"
            ).strip()
            if not raw:
                print(f"  {C.YELLOW}Cancelled.{C.RESET}")
            elif not raw.isdigit() or not (1 <= int(raw) <= len(backups)):
                print(f"  {C.RED}Invalid number.{C.RESET}")
            else:
                target = backups[int(raw) - 1]
                ts = target.time.strftime("%Y-%m-%d %H:%M:%S")
                confirm = (
                    input(f"  Restore '{target.save_name}' from {ts}? [y/N]: ")
                    .strip()
                    .lower()
                )
                if confirm == "y":
                    _restore(target)
                else:
                    print(f"  {C.YELLOW}Cancelled.{C.RESET}")
