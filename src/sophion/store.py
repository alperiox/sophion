"""Knowledge store directory management."""

from pathlib import Path

import frontmatter

from sophion.config import Config


class Store:
    """Manages the ~/.sophion/ directory structure."""

    def __init__(self, config: Config):
        self.base = config.base_dir
        self.raw = self.base / "knowledge" / "raw"
        self.wiki = self.base / "knowledge" / "wiki"
        self.gaps = self.base / "knowledge" / "gaps"
        self.conversations = self.base / "conversations"
        self.learner_state = self.base / "learner_state"

    def initialize(self):
        """Create all required directories."""
        for path in [
            self.raw,
            self.wiki,
            self.gaps,
            self.conversations,
            self.learner_state,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def uncompiled_files(self) -> list[Path]:
        """Find raw markdown files that haven't been compiled yet."""
        uncompiled = []
        for path in sorted(self.raw.glob("*.md")):
            post = frontmatter.load(str(path))
            if not post.get("compiled", False):
                uncompiled.append(path)
        return uncompiled
