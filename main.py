import os

from core.actions import do_download, do_upload, refresh
from core.backup import browse_backups
from core.config import read_locations
from core.display import SEP, C, clear_screen, display, getch, print_header
from core.editor import add_save, remove_save
from core.models import Local, Remote
from core.utils import rmdir


def main() -> None:
    os.system("")  # enable ANSI on Windows consoles

    saves = read_locations()
    clear_screen()
    print_header()
    statuses = refresh(saves)
    page = 0

    while True:
        clear_screen()
        print_header()
        total_pages = display(statuses, page)

        n_up = sum(1 for s in statuses if s.local in (Local.CHANGED, Local.NEW))
        n_down = sum(1 for s in statuses if s.remote == Remote.NEWER)

        opts: list[str] = []
        if n_up:
            opts.append(f"[{C.YELLOW}U{C.RESET}]pload {C.GRAY}({n_up}){C.RESET}")
        if n_down:
            opts.append(f"[{C.YELLOW}D{C.RESET}]ownload {C.GRAY}({n_down}){C.RESET}")
        if n_up or n_down:
            opts.append(f"[{C.YELLOW}S{C.RESET}]ync both")
        opts.append(f"[{C.YELLOW}R{C.RESET}]efresh")
        if total_pages > 1:
            opts.append(f"[{C.YELLOW}←{C.RESET}/{C.YELLOW}→{C.RESET}] page")
        opts.append(f"[{C.YELLOW}A{C.RESET}]dd save")
        opts.append(f"[{C.YELLOW}X{C.RESET}] remove save")
        opts.append(f"[{C.YELLOW}B{C.RESET}]ackups")
        opts.append(f"[{C.YELLOW}Q{C.RESET}]uit")

        print(f"  {C.BOLD}What would you like to do?{C.RESET}")
        print("  " + "   ".join(opts))
        print(f"  {C.GRAY}Press the corresponding key to select an option{C.RESET}")
        print()

        key = getch()

        if key == "q":
            rmdir("tocheck")
            clear_screen()
            print(f"  {C.GRAY}Exited!{C.RESET}\n")
            break
        elif key == "right" and page < total_pages - 1:
            page += 1
            continue
        elif key == "left" and page > 0:
            page -= 1
            continue
        elif key == "u" and n_up:
            clear_screen()
            do_upload(statuses)
        elif key == "d" and n_down:
            clear_screen()
            do_download(statuses)
        elif key == "s" and (n_up or n_down):
            clear_screen()
            do_upload(statuses)
            do_download(statuses)
        elif key == "a":
            clear_screen()
            print_header()
            add_save()
        elif key == "x":
            clear_screen()
            print_header()
            display(statuses, page)
            remove_save(statuses)
        elif key == "b":
            clear_screen()
            browse_backups()
        elif key == "r":
            clear_screen()
        else:
            continue  # invalid key - don't refresh

        print()
        print(SEP)
        print()
        rmdir("tocheck")
        saves = read_locations()
        statuses = refresh(saves)


if __name__ == "__main__":
    main()
