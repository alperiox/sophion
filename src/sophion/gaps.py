"""Learning gap tracking — what you don't yet understand."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


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
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.gaps = [Gap.from_dict(g) for g in data]

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([g.to_dict() for g in self.gaps], indent=2))

    def add(self, topic: str, question: str) -> Gap:
        """Add a new open gap."""
        gap = Gap(topic=topic, question=question)
        self.gaps.append(gap)
        self._save()
        return gap

    def resolve(self, gap_id: str, resolution: str) -> Gap | None:
        """Mark a gap as resolved with an explanation."""
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
