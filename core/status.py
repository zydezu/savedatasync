import os
import shutil
import urllib.request

from .config import read_git_url
from .display import C
from .models import Local, Remote, Save, Status
from .utils import folder_hash, human_size, newest_mtime, rmdir


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
    """Download GitHub zip into tocheck/."""
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

    # tocheck/ stays alive so do_download() can reuse it without re-fetching
    return statuses
