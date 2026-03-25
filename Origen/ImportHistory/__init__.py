"""Import History - Tracks all imported components with metadata."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ImportHistory:
    """Manages a JSON-based history of imported components."""

    def __init__(self, history_dir: Optional[Path] = None):
        if history_dir is None:
            history_dir = Path(__file__).resolve().parent.parent
        self.history_file = Path(history_dir) / "import_history.json"
        self._history: List[Dict] = []
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load import history: {e}")
            self._history = []

    def _save(self) -> None:
        """Save history to disk."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Could not save import history: {e}")

    def add_entry(
        self,
        component_name: str,
        source: str,
        library_name: str,
        zip_file: str = "",
        profile: str = "",
    ) -> None:
        """Record a successful import."""
        entry = {
            "component": component_name,
            "source": source,
            "library": library_name,
            "file": zip_file,
            "profile": profile,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._history.append(entry)
        self._save()
        logger.info(f"History: recorded import of '{component_name}' from {source}")

    def get_entries(self, limit: int = 0) -> List[Dict]:
        """Return history entries, newest first. limit=0 means all."""
        entries = list(reversed(self._history))
        if limit > 0:
            return entries[:limit]
        return entries

    def get_count(self) -> int:
        """Return total number of imports."""
        return len(self._history)

    def get_summary_text(self, limit: int = 50) -> str:
        """Return a formatted text summary for display in the GUI."""
        entries = self.get_entries(limit)
        if not entries:
            return "No imports recorded yet."

        lines = [f"Import History ({self.get_count()} total):\n"]
        for entry in entries:
            date = entry.get("date", "?")
            comp = entry.get("component", "?")
            src = entry.get("source", "?")
            lib = entry.get("library", "?")
            lines.append(f"  [{date}] {comp} ({src}) -> {lib}")

        return "\n".join(lines)

    def is_already_imported(self, component_name: str) -> Optional[Dict]:
        """Check if a component was already imported. Returns the entry or None."""
        for entry in reversed(self._history):
            if entry.get("component", "").upper() == component_name.upper():
                return entry
        return None

    def get_stats_by_source(self) -> Dict[str, int]:
        """Return component count grouped by source."""
        stats: Dict[str, int] = {}
        for entry in self._history:
            source = entry.get("source", "Unknown")
            stats[source] = stats.get(source, 0) + 1
        return stats

    def get_summary_with_stats(self, limit: int = 50) -> str:
        """Return formatted summary with statistics."""
        try:
            from i18n import _ as tr
        except ImportError:
            def tr(key, **kwargs):
                return key

        text = self.get_summary_text(limit)

        stats = self.get_stats_by_source()
        if stats:
            text += f"\n{tr('messages.history_stats_header')}"
            for source, count in sorted(stats.items(), key=lambda x: -x[1]):
                text += f"\n{tr('messages.history_stats_source', source=source, count=count)}"
            text += f"\n{tr('messages.history_stats_total', count=self.get_count())}"

        return text

    def clear(self) -> None:
        """Clear all history."""
        self._history = []
        self._save()
