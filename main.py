import hashlib
import os
import shutil
import subprocess
import sys
import termios
import tty
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

# ── Colors ────────────────────────────────────────────────────────────────────


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


SEP = f"{C.GRAY}{'─' * 64}{C.RESET}"


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class Save:
    name: str
    paths: list[str] = field(default_factory=list)


class Local(Enum):
    CHANGED = auto()  # files differ from last synced state
    UNCHANGED = auto()  # matches last synced state
    NEW = auto()  # no sync record yet
    MISSING = auto()  # no valid path exists


class Remote(Enum):
    NEWER = auto()  # remote has a newer version
    OLDER = auto()  # local is ahead of remote
    SAME = auto()  # in sync with remote
    UNKNOWN = auto()  # not yet checked


@dataclass
class Status:
    save: Save
    local: Local = Local.MISSING
    remote: Remote = Remote.UNKNOWN
    local_hash: str = ""
    local_time: Optional[datetime] = None
    remote_hash: str = ""
    remote_date: str = ""


# ── Utilities ─────────────────────────────────────────────────────────────────


def folder_hash(path: str, block: int = 65536) -> str:
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            with open(os.path.join(root, name), "rb") as f:
                for chunk in iter(lambda: f.read(block), b""):
                    h.update(chunk)
    return h.hexdigest()


def newest_mtime(path: str) -> datetime:
    if os.path.isfile(path):
        return datetime.fromtimestamp(os.path.getmtime(path))
    best: Optional[datetime] = None
    for root, _, files in os.walk(path):
        for name in files:
            mt = datetime.fromtimestamp(os.path.getmtime(os.path.join(root, name)))
            if best is None or mt > best:
                best = mt
    return best or datetime.fromtimestamp(0)


def human_size(b: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def rmdir(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _dir_size(path: str) -> int:
    return sum(
        os.path.getsize(os.path.join(root, name))
        for root, _, files in os.walk(path)
        for name in files
    )


def _make_zip(src: str, dest: str, level: int = 6) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=level) as zf:
        for root, dirs, files in os.walk(src):
            dirs.sort()
            for name in sorted(files):
                filepath = os.path.join(root, name)
                zf.write(filepath, os.path.relpath(filepath, src))


def read_git_url() -> str:
    with open("gitFilePath.txt") as f:
        return f.readline().strip()


# ── Config ────────────────────────────────────────────────────────────────────


def read_locations() -> list[Save]:
    with open("locations.txt") as f:
        lines = [line.rstrip() for line in f]
    while lines and not lines[-1]:
        lines.pop()

    saves: list[Save] = []
    current: Optional[Save] = None
    new_block = True
    for line in lines:
        stripped = line.strip()
        if new_block:
            current = Save(name=stripped)
            new_block = False
        elif not stripped:
            if current:
                saves.append(current)
            new_block = True
        else:
            if current:
                current.paths.append(stripped)
    if current and not new_block:
        saves.append(current)
    return saves


# ── Status checking ───────────────────────────────────────────────────────────


def check_local(saves: list[Save]) -> list[Status]:
    statuses: list[Status] = []
    for save in saves:
        st = Status(save=save)
        path = next((p for p in save.paths if os.path.exists(p)), None)

        if path is None:
            statuses.append(st)
            continue

        st.local_hash = folder_hash(path)
        st.local_time = newest_mtime(path)

        info = os.path.join("saves", f"{save.name}.txt")
        if not os.path.exists(info):
            st.local = Local.NEW
        else:
            with open(info) as f:
                stored = (f.readlines() + ["", ""])[1].strip()
            st.local = Local.UNCHANGED if stored == st.local_hash else Local.CHANGED

        statuses.append(st)
    return statuses


def _fetch_remote() -> bool:
    """Download GitHub zip into tocheck/. Returns True on success."""
    url = read_git_url()
    print(f"  {C.GRAY}Fetching remote...{C.RESET}", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, "main.zip")
        print(f" {human_size(os.path.getsize('main.zip'))}")
        shutil.unpack_archive("main.zip", "temp", "zip")
        os.remove("main.zip")
        rmdir("tocheck")
        shutil.copytree(
            os.path.join("temp", "savedatasync-main", "saves"),
            "tocheck",
            dirs_exist_ok=True,
        )
        rmdir("temp")
    except Exception as e:
        print(f"\n  {C.RED}Fetch failed: {e}{C.RESET}")
        rmdir("temp")
        return False

    # unzip any zipped saves
    for _, _, files in os.walk("tocheck"):
        for name in files:
            if name.lower().endswith(".zip"):
                shutil.unpack_archive(
                    os.path.join("tocheck", name),
                    os.path.join("tocheck", name[:-4]),
                    "zip",
                )
        break  # top-level only
    return True


def check_remote(statuses: list[Status]) -> list[Status]:
    if not _fetch_remote():
        return statuses

    for st in statuses:
        info = os.path.join("tocheck", f"{st.save.name}.txt")
        if not os.path.exists(info):
            continue
        with open(info) as f:
            lines = f.readlines()
        st.remote_date = lines[0].strip()
        st.remote_hash = lines[1].strip() if len(lines) > 1 else ""

        local_info = os.path.join("saves", f"{st.save.name}.txt")
        if not os.path.exists(local_info):
            local_date, local_hash = "0000-00-00 00:00:00.000000", ""
        else:
            with open(local_info) as f:
                ll = f.readlines()
            local_date = ll[0].strip()
            local_hash = ll[1].strip() if len(ll) > 1 else ""

        if st.remote_hash == local_hash:
            st.remote = Remote.SAME
        elif st.remote_date > local_date:
            st.remote = Remote.NEWER
        else:
            st.remote = Remote.OLDER

    # tocheck/ is kept alive so do_download() can reuse it without re-fetching
    return statuses


# ── Display ───────────────────────────────────────────────────────────────────

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


def display(statuses: list[Status]) -> None:
    print()
    w = max(len(s.save.name) for s in statuses) + 2
    print(
        f"  {C.BOLD}{'#':>2}  {'Name':<{w}}  {'Local':<12}  {'Remote':<14}  Modified{C.RESET}"
    )
    print(
        f"  {C.GRAY}{'─' * 2}  {'─' * w}  {'─' * 12}  {'─' * 14}  {'─' * 16}{C.RESET}"
    )
    for i, st in enumerate(statuses, 1):
        lc, ll = _LOCAL_LABEL[st.local]
        rc, rl = _REMOTE_LABEL[st.remote]
        ts = st.local_time.strftime("%Y-%m-%d %H:%M") if st.local_time else ""
        dim_ts = f"{C.GRAY}{ts}{C.RESET}" if st.local == Local.UNCHANGED else ts
        print(
            f"  {C.GRAY}{i:>2}{C.RESET}  {st.save.name:<{w}}  {lc}{ll}{C.RESET}  {rc}{rl}{C.RESET}  {dim_ts}"
        )
    print()


# ── Actions ───────────────────────────────────────────────────────────────────


def _stage_save(st: Status) -> bool:
    """Copy local path into saves/ and write info file. Returns True on success."""
    path = next((p for p in st.save.paths if os.path.exists(p)), None)
    if path is None or st.local_time is None:
        return False

    save_dir = os.path.join("saves", st.save.name)
    rmdir(save_dir)

    if os.path.isfile(path):
        os.makedirs(save_dir, exist_ok=True)
        shutil.copy2(path, save_dir)
    else:
        zip_path = save_dir + ".zip"
        # Pre-check: if raw size is already huge, compression won't bring it under
        # GitHub's 100 MB per-file limit so go straight to directory copy.
        if _dir_size(path) >= 200_000_000:
            shutil.copytree(path, save_dir, dirs_exist_ok=True)
        else:
            _make_zip(path, zip_path)
            if os.path.getsize(zip_path) > 100_000_000:
                shutil.copytree(path, save_dir, dirs_exist_ok=True)
                os.remove(zip_path)

    backup_path = os.path.join(
        "backup", f"{st.local_time.strftime('%Y-%m-%d_%H-%M-%S')} {st.save.name}"
    )
    rmdir(backup_path)
    if os.path.isfile(path):
        os.makedirs(backup_path, exist_ok=True)
        shutil.copy2(path, backup_path)
    else:
        shutil.copytree(path, backup_path, dirs_exist_ok=True)

    info = [str(st.local_time) + "\n", st.local_hash]
    with open(os.path.join("saves", f"{st.save.name}.txt"), "w") as f:
        f.writelines(info)
    with open(f"{backup_path}.txt", "w") as f:
        f.writelines(info)

    return True


def do_upload(statuses: list[Status]) -> None:
    targets = [st for st in statuses if st.local in (Local.CHANGED, Local.NEW)]
    if not targets:
        print(f"  {C.GREEN}Nothing to upload.{C.RESET}")
        return

    print()
    labels: list[str] = []
    for st in targets:
        if _stage_save(st):
            ts = st.local_time.strftime("%Y-%m-%d %H:%M.%S") if st.local_time else "?"
            labels.append(f"{st.save.name} [{ts}]")
            print(f"  {C.GREEN}✓{C.RESET} staged  {st.save.name}")
        else:
            print(f"  {C.RED}✗{C.RESET} skipped {st.save.name}  (path missing)")

    if not labels:
        print(f"  {C.RED}Nothing staged — no paths exist.{C.RESET}")
        return

    if len(labels) == 1:
        commit_msg = f"Updated save files: {labels[0]}"
    else:
        commit_msg = f"Updated save files: {', '.join(labels[:-1])}, and {labels[-1]}"

    print(f"\n  {C.CYAN}Pushing to git...{C.RESET}")
    subprocess.call(["git", "pull"])
    subprocess.call(["git", "add", "."])
    rc = subprocess.call(["git", "commit", "-m", f"AUTOMATED: {commit_msg}"])
    if rc == 0:
        subprocess.call(["git", "push"])
        print(f"  {C.GREEN}Upload complete.{C.RESET}")
    else:
        print(f"  {C.YELLOW}Nothing committed (git found no changes).{C.RESET}")


def do_download(statuses: list[Status]) -> None:
    targets = [st for st in statuses if st.remote == Remote.NEWER]
    if not targets:
        print(f"  {C.GREEN}Nothing to download.{C.RESET}")
        return

    if not os.path.exists("tocheck") and not _fetch_remote():
        return

    print()
    for st in targets:
        src = os.path.join("tocheck", st.save.name)
        if not os.path.isdir(src):
            print(f"  {C.YELLOW}?{C.RESET} no folder in remote for {st.save.name}")
            continue

        shutil.copytree(src, os.path.join("saves", st.save.name), dirs_exist_ok=True)
        with open(os.path.join("saves", f"{st.save.name}.txt"), "w") as f:
            f.write(st.remote_date + "\n")
            f.write(st.remote_hash)

        for path in st.save.paths:
            if os.path.isdir(path):
                shutil.copytree(
                    os.path.join("saves", st.save.name), path, dirs_exist_ok=True
                )
                print(f"  {C.GREEN}✓{C.RESET} {st.save.name} → {path}")
                break
            if os.path.isfile(path):
                save_files = os.listdir(os.path.join("saves", st.save.name))
                if save_files:
                    shutil.copy2(
                        os.path.join("saves", st.save.name, save_files[0]), path
                    )
                print(f"  {C.GREEN}✓{C.RESET} {st.save.name} → {path}")
                break

    rmdir("tocheck")
    print(f"  {C.GREEN}Download complete.{C.RESET}")


# ── Input ─────────────────────────────────────────────────────────────────────


def getch() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Main ──────────────────────────────────────────────────────────────────────


def refresh(saves: list[Save]) -> list[Status]:
    print(f"  {C.GRAY}Checking local saves...{C.RESET}")
    statuses = check_local(saves)
    print(f"  {C.GRAY}Checking remote...{C.RESET}")
    return check_remote(statuses)


def main() -> None:
    os.system("")  # enable ANSI on Windows consoles

    print(f"\n{C.BOLD}{C.CYAN}  Save Data Sync{C.RESET}")
    print(SEP)

    saves = read_locations()
    statuses = refresh(saves)

    while True:
        display(statuses)

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
        opts.append(f"[{C.YELLOW}Q{C.RESET}]uit")

        print("  " + "   ".join(opts))
        print()

        key = getch()
        print()

        if key == "q":
            rmdir("tocheck")
            print(f"  {C.GRAY}Bye!{C.RESET}\n")
            break
        elif key == "u" and n_up:
            do_upload(statuses)
        elif key == "d" and n_down:
            do_download(statuses)
        elif key == "s" and (n_up or n_down):
            do_upload(statuses)
            do_download(statuses)
        elif key == "r":
            pass
        else:
            continue  # invalid key — don't refresh

        print()
        print(SEP)
        print()
        rmdir("tocheck")
        statuses = refresh(saves)


if __name__ == "__main__":
    main()
