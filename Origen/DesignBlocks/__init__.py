"""
Design Blocks support for KiCad 10.
Provides functions to manage .kicad_blocks libraries and register them in KiCad.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

def _get_kicad_appdata() -> Path:
    """Return the KiCad 10.0 settings directory."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return Path(appdata) / "kicad" / "10.0"
    # Fallback for non-Windows
    home = Path.home()
    return home / ".config" / "kicad" / "10.0"


def _get_lib_table_path() -> Path:
    """Return path to the design-block-lib-table file."""
    return _get_kicad_appdata() / "design-block-lib-table"


# ─── Core library helpers ──────────────────────────────────────────────────────

def get_design_blocks_path(dest_path: str, lib_name: str) -> Path:
    """
    Return path to ``{dest_path}/{lib_name}.kicad_blocks``.
    Creates the directory if it does not exist.
    """
    blocks_path = Path(dest_path) / f"{lib_name}.kicad_blocks"
    blocks_path.mkdir(parents=True, exist_ok=True)
    return blocks_path


def list_design_blocks(blocks_path: Path) -> List[dict]:
    """
    Return a list of dicts describing every design block in *blocks_path*.

    Each dict has the keys:
        name, description, keywords, has_sch, has_pcb
    """
    results = []
    blocks_path = Path(blocks_path)
    if not blocks_path.exists():
        return results

    for block_dir in sorted(blocks_path.iterdir()):
        if not block_dir.is_dir() or not block_dir.name.endswith(".kicad_block"):
            continue

        block_name = block_dir.stem
        description = ""
        keywords = ""

        json_file = block_dir / f"{block_name}.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                description = meta.get("description", "")
                keywords = meta.get("keywords", "")
            except Exception as e:
                logger.warning(f"Could not read metadata for {block_name}: {e}")

        has_sch = (block_dir / f"{block_name}.kicad_sch").exists()
        has_pcb = (block_dir / f"{block_name}.kicad_pcb").exists()

        results.append({
            "name": block_name,
            "description": description,
            "keywords": keywords,
            "has_sch": has_sch,
            "has_pcb": has_pcb,
        })

    return results


def _write_block_metadata(block_dir: Path, block_name: str,
                          description: str = "", keywords: str = "") -> None:
    """Write (or overwrite) the .json metadata file for a design block."""
    json_file = block_dir / f"{block_name}.json"
    meta = {
        "description": description,
        "keywords": keywords,
        "fields": [],
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def create_design_block(
    blocks_path: Path,
    name: str,
    sch_content: Optional[str] = None,
    pcb_content: Optional[str] = None,
    description: str = "",
    keywords: str = "",
) -> Path:
    """
    Create a new design block folder with optional content files.
    Returns the path to the created ``.kicad_block`` directory.
    """
    blocks_path = Path(blocks_path)
    block_dir = blocks_path / f"{name}.kicad_block"
    block_dir.mkdir(parents=True, exist_ok=True)

    _write_block_metadata(block_dir, name, description, keywords)

    if sch_content is not None:
        sch_file = block_dir / f"{name}.kicad_sch"
        sch_file.write_text(sch_content, encoding="utf-8")

    if pcb_content is not None:
        pcb_file = block_dir / f"{name}.kicad_pcb"
        pcb_file.write_text(pcb_content, encoding="utf-8")

    logger.info(f"Created design block '{name}' at {block_dir}")
    return block_dir


def delete_design_block(blocks_path: Path, name: str) -> None:
    """Remove the ``.kicad_block`` folder for *name*."""
    blocks_path = Path(blocks_path)
    block_dir = blocks_path / f"{name}.kicad_block"
    if block_dir.exists():
        shutil.rmtree(block_dir)
        logger.info(f"Deleted design block '{name}'")
    else:
        logger.warning(f"Design block '{name}' not found at {block_dir}")


def import_sch_as_block(
    blocks_path: Path,
    sch_file_path: str,
    block_name: Optional[str] = None,
) -> str:
    """
    Copy *sch_file_path* into a new design block.
    If *block_name* is not supplied the stem of the file is used.
    Returns the final block name.
    """
    src = Path(sch_file_path)
    if block_name is None:
        block_name = src.stem

    block_dir = create_design_block(blocks_path, block_name)
    dest = block_dir / f"{block_name}.kicad_sch"
    shutil.copy2(str(src), str(dest))
    logger.info(f"Imported '{src.name}' as design block '{block_name}'")
    return block_name


def update_block_metadata(
    blocks_path: Path,
    name: str,
    description: Optional[str] = None,
    keywords: Optional[str] = None,
) -> None:
    """Update the .json metadata file of an existing design block."""
    blocks_path = Path(blocks_path)
    block_dir = blocks_path / f"{name}.kicad_block"
    json_file = block_dir / f"{name}.json"

    meta: dict = {}
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read existing metadata for '{name}': {e}")

    if description is not None:
        meta["description"] = description
    if keywords is not None:
        meta["keywords"] = keywords
    if "fields" not in meta:
        meta["fields"] = []

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Updated metadata for design block '{name}'")


# ─── KiCad registration ────────────────────────────────────────────────────────

def register_in_kicad(blocks_path: Path, lib_name: str) -> bool:
    """
    Register the blocks library in ``design-block-lib-table``.
    Returns True if the entry was added, False if it was already present.
    """
    blocks_path = Path(blocks_path).resolve()
    table_path = _get_lib_table_path()

    # Read existing content (or start fresh)
    if table_path.exists():
        content = table_path.read_text(encoding="utf-8")
    else:
        table_path.parent.mkdir(parents=True, exist_ok=True)
        content = "(design_block_lib_table\n  (version 7)\n)\n"

    # Check if already registered (look for the lib name)
    if f'(name "{lib_name}")' in content or f"(name {lib_name})" in content:
        logger.info(f"Design block library '{lib_name}' already registered")
        return False

    uri = str(blocks_path).replace("\\", "/")
    new_entry = (
        f'  (lib (name "{lib_name}") (type "") '
        f'(uri "{uri}") (options "") (descr ""))\n'
    )

    # Insert before the closing paren
    if content.rstrip().endswith(")"):
        content = content.rstrip()[:-1].rstrip() + "\n" + new_entry + ")\n"
    else:
        content = content + new_entry

    table_path.write_text(content, encoding="utf-8")
    logger.info(f"Registered design block library '{lib_name}' -> {uri}")
    return True
