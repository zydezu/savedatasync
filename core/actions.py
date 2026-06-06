import os
import shutil
import subprocess

from .display import C
from .models import Local, Remote, Save, Status
from .status import _fetch_remote, check_local, check_remote
from .utils import dir_size, make_zip, rmdir


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
        if dir_size(path) >= 200_000_000:
            # Raw size already too large — compression can't bring it under GitHub's
            # 100 MB per-file limit, so store the directory directly instead.
            shutil.copytree(path, save_dir, dirs_exist_ok=True)
        else:
            make_zip(path, zip_path)
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

    commit_msg = (
        f"Updated save files: {', '.join(labels[:-1])}, and {labels[-1]}"
        if len(labels) > 1
        else f"Updated save files: {labels[0]}"
    )

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
                shutil.copytree(os.path.join("saves", st.save.name), path, dirs_exist_ok=True)
                print(f"  {C.GREEN}✓{C.RESET} {st.save.name} → {path}")
                break
            if os.path.isfile(path):
                save_files = os.listdir(os.path.join("saves", st.save.name))
                if save_files:
                    shutil.copy2(os.path.join("saves", st.save.name, save_files[0]), path)
                print(f"  {C.GREEN}✓{C.RESET} {st.save.name} → {path}")
                break

    rmdir("tocheck")
    print(f"  {C.GREEN}Download complete.{C.RESET}")


def refresh(saves: list[Save]) -> list[Status]:
    print(f"  {C.GRAY}Checking local saves...{C.RESET}")
    statuses = check_local(saves)
    print(f"  {C.GRAY}Checking remote...{C.RESET}")
    return check_remote(statuses)
