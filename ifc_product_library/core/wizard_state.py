"""
IFC Product Library — Import Wizard State

Module-level state dict that tracks the wizard's progress across panel redraws.
Same pattern as library_index._index — module-level dict, accessor functions.

Reset between wizard sessions via reset_wizard().
"""

# ---------------------------------------------------------------------------
# State dict
# ---------------------------------------------------------------------------

_wizard: dict = {
    "active": False,
    "step": 1,               # 1 = source, 2 = cleanup, 3 = classify, 4 = metadata

    # Batch mode
    "batch_files": [],       # list of absolute path strings (populated when >1 file selected)
    "batch_index": 0,        # index into batch_files for the current file being processed

    # Step 1 — source selection
    "source_mode": "file",   # "file" | "selected" | "ifc"
    "file_path": "",         # absolute path to the selected file
    "format": "",            # "OBJ", "STL", "glTF", "IFC", "STEP", etc.

    # Step 2 — cleanup
    "imported_object_names": [],   # bpy.data.objects names belonging to this wizard session
    "face_count_raw": 0,           # face count immediately after import (before any cleanup)
    "face_count_current": 0,       # live face count (updated after every cleanup op)
    "decimate_preview_active": False,  # True when Decimate modifier has been applied but not confirmed
    "advanced_expanded": False,    # True when the "Advanced cleanup options" box is open

    # Step 3 — IFC classification
    "category_path": "",           # e.g. "sanitaryware/basins/wall-hung"
    "ifc_class": "",               # e.g. "IfcSanitaryTerminal"
    "predefined_type": "",         # e.g. "WASHHANDBASIN"
    "ifc_version": "IFC4",

    # Step 4 — metadata
    "metadata": {},                # dict matching product.json schema
    "save_error": "",              # non-empty string if last save attempt failed
}


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_wizard() -> dict:
    """Return the live wizard state dict (mutable reference)."""
    return _wizard


def reset_wizard() -> None:
    """Reset all wizard state to defaults. Called on cancel or after successful save."""
    global _wizard
    _wizard.update({
        "active": False,
        "step": 1,
        "batch_files": [],
        "batch_index": 0,
        "source_mode": "file",
        "file_path": "",
        "format": "",
        "imported_object_names": [],
        "face_count_raw": 0,
        "face_count_current": 0,
        "decimate_preview_active": False,
        "advanced_expanded": False,
        "category_path": "",
        "ifc_class": "",
        "predefined_type": "",
        "ifc_version": "IFC4",
        "metadata": {},
        "save_error": "",
    })


def set_wizard_step(step: int) -> None:
    """Set the wizard's current step (1–4)."""
    _wizard["step"] = max(1, min(4, step))


def get_batch_label() -> str:
    """Return a human-readable batch progress label, e.g. 'File 2 of 5'.
    Returns an empty string when not in batch mode."""
    files = _wizard["batch_files"]
    if len(files) <= 1:
        return ""
    return f"File {_wizard['batch_index'] + 1} of {len(files)}"


def advance_batch() -> bool:
    """Move to the next file in a batch.
    Returns True if there is a next file, False if the batch is complete."""
    files = _wizard["batch_files"]
    next_idx = _wizard["batch_index"] + 1
    if next_idx < len(files):
        _wizard["batch_index"] = next_idx
        # Reset per-file state but keep batch list and category
        _wizard.update({
            "step": 1,
            "source_mode": "file",
            "file_path": files[next_idx],
            "format": "",
            "imported_object_names": [],
            "face_count_raw": 0,
            "face_count_current": 0,
            "decimate_preview_active": False,
            "advanced_expanded": False,
            "metadata": {},
            "save_error": "",
            # Keep: category_path, ifc_class, predefined_type, ifc_version
        })
        return True
    return False
