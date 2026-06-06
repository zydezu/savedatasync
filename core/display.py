import os
import select
import sys
import termios
import tty

from .models import Local, Remote, Status
from .utils import dir_size, human_size


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


SEP = f"{C.GRAY}{'─' * 64}{C.RESET}"

_LOCAL_LABEL: dict[Local, tuple[str, str]] = {
    Local.CHANGED: (C.YELLOW, "CHANGED  "),
    Local.UNCHANGED: (C.GREEN, "unchanged"),
    Local.NEW: (C.CYAN, "new      "),
    Local.MISSING: (C.GRAY, "missing  "),
}
_REMOTE_LABEL: dict[Remote, tuple[str, str]] = {
    Remote.NEWER: (C.YELLOW, "REMOTE NEWER"),
    Remote.OLDER: (C.GREEN, "local newer "),
    Remote.SAME: (C.GREEN, "in sync     "),
    Remote.UNKNOWN: (C.GRAY, "─           "),
}


def clear_screen() -> None:
    print("\033[3J\033[2J\033[H", end="", flush=True)


def print_header() -> None:
    print(f"{C.BOLD}{C.CYAN}  Save Data Sync{C.RESET}")
    print(SEP)


PAGE_SIZE = 15


def display(statuses: list[Status], page: int = 0) -> int:
    """Render the status table for the given page. Returns total_pages."""
    print()
    total_pages = max(1, -(-len(statuses) // PAGE_SIZE))
    page = min(page, total_pages - 1)
    start = page * PAGE_SIZE
    page_items = statuses[start : start + PAGE_SIZE]

    w = max(len(s.save.name) for s in statuses) + 2
    print(
        f"  {C.BOLD}{'#':>2}  {'Name':<{w}}  {'Local':<9}  {'Remote':<12}  Modified{C.RESET}"
    )
    print(f"  {C.GRAY}{'─' * 2}  {'─' * w}  {'─' * 9}  {'─' * 12}  {'─' * 16}{C.RESET}")
    for i, st in enumerate(page_items, start + 1):
        lc, ll = _LOCAL_LABEL[st.local]
        rc, rl = _REMOTE_LABEL[st.remote]
        ts = st.local_time.strftime("%Y-%m-%d %H:%M") if st.local_time else ""
        dim_ts = f"{C.GRAY}{ts}{C.RESET}" if st.local == Local.UNCHANGED else ts
        print(
            f"  {C.GRAY}{i:>2}{C.RESET}  {st.save.name:<{w}}  {lc}{ll}{C.RESET}  {rc}{rl}{C.RESET}  {dim_ts}"
        )

    for _ in range(PAGE_SIZE - len(page_items)):
        print()

    n_changed = sum(1 for s in statuses if s.local in (Local.CHANGED, Local.NEW))
    n_synced = sum(
        1 for s in statuses if s.local == Local.UNCHANGED and s.remote == Remote.SAME
    )
    n_remote = sum(1 for s in statuses if s.remote == Remote.NEWER)
    total = sum(
        dir_size(p) for s in statuses for p in s.save.paths if os.path.exists(p)
    )
    parts = [f"{len(statuses)} saves", human_size(total)]
    if n_synced:
        parts.append(f"{n_synced} in sync")
    if n_changed:
        parts.append(f"{n_changed} to upload")
    if n_remote:
        parts.append(f"{n_remote} to download")

    print(f"  {C.GRAY}Page {page + 1}/{total_pages}{C.RESET}")
    print(f"  {C.GRAY}{' • '.join(parts)}{C.RESET}")
    print()
    return total_pages


def getch() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b" and select.select([fd], [], [], 0.05)[0]:
            ch2 = os.read(fd, 1)
            if ch2 == b"[" and select.select([fd], [], [], 0.05)[0]:
                ch3 = os.read(fd, 1)
                return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(
                    ch3.decode(), ""
                )
        return ch.decode().lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
