"""Learning gap tracking — what you don't yet understand."""

import fcntl
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def _atomic_write(path: Path, text: str):
    """Write `text` to `path` atomically, so a crash cannot truncate it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


@contextmanager
def _locked(path: Path):
    """Hold an exclusive lock for a read-modify-write cycle on `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@dataclass
class Gap:
    """A single learning gap — something you accepted without verifying."""

    topic: str
    question: str
    status: str = "open"
    resolution: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "question": self.question,
            "status": self.status,
            "resolution": self.resolution,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Gap":
        return cls(
            id=data["id"],
            topic=data["topic"],
            question=data["question"],
            status=data["status"],
            resolution=data.get("resolution", ""),
            created_at=data["created_at"],
            resolved_at=data.get("resolved_at", ""),
        )


class GapTracker:
    """Manages learning gaps with JSON persistence."""

    def __init__(self, path: Path):
        self.path = path
        self.gaps: list[Gap] = []
        self._load()

    def _load(self):
        """Load gaps from disk, quarantining the file if it is unreadable.

        An unreadable file is moved aside rather than deleted or left in
        place: leaving it would make every gap tool raise forever.
        """
        if not self.path.exists():
            self.gaps = []
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            salvaged = self.path.with_name(f"{self.path.name}.corrupt-{int(time.time() * 1000)}")
            self.path.rename(salvaged)
            self.gaps = []
            return
        self.gaps = [Gap.from_dict(g) for g in data]

    def _save(self):
        _atomic_write(self.path, json.dumps([g.to_dict() for g in self.gaps], indent=2))

    def add(self, topic: str, question: str) -> Gap:
        """Add a new open gap."""
        gap = Gap(topic=topic, question=question)
        with _locked(self.path):
            self._load()  # re-read inside the lock so we don't clobber a concurrent write
            self.gaps.append(gap)
            self._save()
        return gap

    def resolve(self, gap_id: str, resolution: str) -> Gap | None:
        """Mark a gap as resolved with an explanation."""
        with _locked(self.path):
            self._load()  # re-read inside the lock so we don't clobber a concurrent write
            for gap in self.gaps:
                if gap.id == gap_id:
                    gap.status = "resolved"
                    gap.resolution = resolution
                    gap.resolved_at = datetime.now().isoformat()
                    self._save()
                    return gap
        return None

    def get(self, gap_id: str) -> Gap | None:
        """Get a gap by ID."""
        for gap in self.gaps:
            if gap.id == gap_id:
                return gap
        return None

    def list_open(self) -> list[Gap]:
        """List all open gaps."""
        return [g for g in self.gaps if g.status == "open"]

    def list_all(self) -> list[Gap]:
        """List all gaps (open and resolved)."""
        return list(self.gaps)

    def gaps_since(self, since: str) -> tuple[list[Gap], list[Gap]]:
        """Return (added, resolved) gaps since a given ISO timestamp."""
        added = [g for g in self.gaps if g.created_at >= since]
        resolved = [
            g for g in self.gaps
            if g.status == "resolved" and g.resolved_at >= since
        ]
        return added, resolved


class StudySession:
    """Tracks whether study mode is active, with session persistence."""

    def __init__(self, path: Path):
        self.path = path
        self.active = False
        self.started_at = ""
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self.path.rename(self.path.with_name(f"{self.path.name}.corrupt-{int(time.time() * 1000)}"))
            return
        self.active = data.get("active", False)
        self.started_at = data.get("started_at", "")

    def _save(self):
        _atomic_write(self.path, json.dumps({
            "active": self.active,
            "started_at": self.started_at,
        }, indent=2))

    def start(self) -> str:
        """Start a study session. Returns the start timestamp."""
        self.active = True
        self.started_at = datetime.now().isoformat()
        self._save()
        return self.started_at

    def stop(self) -> str:
        """Stop the study session. Returns the start timestamp for summary."""
        started = self.started_at
        self.active = False
        self.started_at = ""
        self._save()
        return started

    def is_active(self) -> bool:
        return self.active
