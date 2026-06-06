# savedatasync

<img width="1366" height="786" alt="image" src="https://github.com/user-attachments/assets/6efac1f4-bae7-4b2b-9fbc-c5afb2144e11" />

A terminal UI for syncing game save files to a GitHub repository. Tracks local changes, compares against remote, and lets you upload, download, or restore from backups. Useful for syncing your emulator saves across multiple machines.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/boysaremoe)

## Features

- Status table showing local and remote state for all configured saves
- Upload changed saves, download newer remote saves, or sync both at once
- Add and remove saves interactively
- Paginated backup browser with restore support
- ZIP compression before upload, with size-based fallbacks
- Local backups created automatically before any overwrite

## Setup

1. Clone this repo
2. Add a `gitFilePath.txt` containing the URL to your repository's `master.zip`:
   ```
   https://github.com/yourname/yourrepo/archive/master.zip
   ```
3. Run `main.py` and use the `Add` option to add your saves interactively, or edit `locations.json` to list your saves:
   ```json
   [
     {
       "name": "PS2 Memory Cards",
       "paths": ["/home/user/.config/PCSX2/memcards"]
     },
     {
       "name": "Dolphin Settings",
       "paths": [
         "/home/user/.local/share/dolphin-emu/GameSettings",
         "/home/user2/.local/share/dolphin-emu/GameSettings"
       ]
     }
   ]
   ```
   Multiple paths are checked in order — the first valid one is used. Useful for syncing across machines with different home directories.

## Usage

The main screen shows all configured saves with their local and remote status:

```
  Save Data Sync
────────────────────────────────────────────────────────────────

   #  Name                  Local      Remote        Modified
  ──  ────────────────────  ─────────  ────────────  ────────────────
   1  PS2 Memory Cards      unchanged  in sync       2026-05-14 21:33
   2  PCSX2 Settings        CHANGED    local newer   2026-06-01 10:12
   3  PS3 Saves             new        ─             2026-06-06 09:44
  ...

  Page 1/1
  11 saves • 65 MB • 8 in sync • 2 to upload
```

### Keys

| Key | Action |
|-----|--------|
| `U` | Upload all changed/new saves |
| `D` | Download all saves where remote is newer |
| `S` | Sync both directions |
| `R` | Refresh status |
| `←` / `→` | Navigate pages |
| `A` | Add a new save entry |
| `X` | Remove a save entry |
| `B` | Open backup browser |
| `Q` | Quit |

### Backup browser

Press `B` to browse local backups. Backups are stored in `backup/` as folders named `YYYY-MM-DD_HH-MM-SS save_name`. The browser shows all backups paginated, with total size and date range. Press `R` to restore a backup to its original path.

## How it works

**Uploading:** each save's folder is hashed with SHA-256. If the hash differs from what's stored in `saves/`, the folder is zipped and copied there, a backup is made, and the repo is committed and pushed.

**Downloading:** the repo is downloaded as a zip from the URL in `gitFilePath.txt`, extracted to `tocheck/`, and each save's hash and date are compared against the local copy. Newer remote saves are extracted and copied to the configured path.

**Backups:** created automatically before any local file is overwritten. Stored in `backup/` and browsable from within the app.

## Notes

- `backup/`, `temp/`, and `tocheck/` are gitignored and never uploaded
- If a save has multiple paths, only the first existing one is used on each machine
- Saves larger than 100 MB are not compressed; if the zip exceeds 100 MB the raw directory is used instead

![2023-10-01_07-07-11_582_Vita3K](https://github.com/zydezu/savedatasync/assets/50119098/008ae336-b24b-4d6c-bf30-329a38cb1932)
![Shin Megami Tensei - Persona 3 FES_SLUS-21621_20240512203921](https://github.com/user-attachments/assets/e35615bf-77dd-4acd-92cb-9fd3567156f4)
