from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

@dataclass
class Save:
    name:  str
    paths: list[str] = field(default_factory=list)


class Local(Enum):
    CHANGED   = auto()  # files differ from last synced state
    UNCHANGED = auto()  # matches last synced state
    NEW       = auto()  # no sync record yet
    MISSING   = auto()  # no valid path exists


class Remote(Enum):
    NEWER   = auto()  # remote has a newer version
    OLDER   = auto()  # local is ahead of remote
    SAME    = auto()  # in sync with remote
    UNKNOWN = auto()  # not yet checked


@dataclass
class Status:
    save:        Save
    local:       Local              = Local.MISSING
    remote:      Remote             = Remote.UNKNOWN
    local_hash:  str                = ""
    local_time:  Optional[datetime] = None
    remote_hash: str                = ""
    remote_date: str                = ""
