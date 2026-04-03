"""Conversation and message data models with JSON persistence."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Message:
    """A single message in a conversation."""

    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
        )


@dataclass
class Conversation:
    """A conversation thread with persistence."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Conversation"
    messages: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: str, content: str) -> Message:
        """Add a message and update the timestamp."""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
        return msg

    def generate_name(self) -> str:
        """Generate a name from the first user message."""
        for msg in self.messages:
            if msg.role == "user":
                text = msg.content[:50]
                if len(msg.content) > 50:
                    text += "..."
                return text
        return "New Conversation"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        return cls(
            id=data["id"],
            name=data["name"],
            messages=[Message.from_dict(m) for m in data["messages"]],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def save(self, conversations_dir: Path) -> Path:
        """Save conversation to a JSON file."""
        path = conversations_dir / f"{self.id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "Conversation":
        """Load conversation from a JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    @classmethod
    def list_all(cls, conversations_dir: Path) -> list["Conversation"]:
        """Load all conversations from a directory, newest first."""
        convos = []
        for path in sorted(conversations_dir.glob("*.json"), reverse=True):
            try:
                convos.append(cls.load(path))
            except (json.JSONDecodeError, KeyError):
                continue
        return convos
