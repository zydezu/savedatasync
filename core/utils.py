import hashlib
import os
import shutil
import zipfile
from datetime import datetime
from typing import Optional


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


def dir_size(path: str) -> int:
    return sum(
        os.path.getsize(os.path.join(root, name))
        for root, _, files in os.walk(path)
        for name in files
    )


def make_zip(src: str, dest: str, level: int = 6) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=level) as zf:
        for root, dirs, files in os.walk(src):
            dirs.sort()
            for name in sorted(files):
                filepath = os.path.join(root, name)
                zf.write(filepath, os.path.relpath(filepath, src))
