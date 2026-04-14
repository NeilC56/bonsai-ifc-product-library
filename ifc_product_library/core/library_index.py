"""
Library index
=============
Walks the library folder tree on demand, reads every product.json, and
builds a fast in-memory index.

Also owns UI state (expanded categories, selected product) as plain Python
module-level variables.  These persist across panel redraws within a Blender
session without needing a bpy.types.PropertyGroup for every slug.
"""

import os
import json

# ---------------------------------------------------------------------------
# In-memory index — rebuilt whenever load_library() is called
# ---------------------------------------------------------------------------

_index: dict = {
    "products": {},       # slug → product dict  (with "_folder_path" injected)
    "by_category": {},    # category path → [slug, ...]
    "library_meta": {},   # parsed library.json
    "loaded": False,
    "library_path": "",
    "error": "",
}

# ---------------------------------------------------------------------------
# UI state — persists across redraws, reset on library reload
# ---------------------------------------------------------------------------

_ui_state: dict = {
    "expanded_categories": set(),   # set of expanded category path strings
    "selected_category": "",        # category path the user last clicked
    "selected_product_slug": "",    # product the user last clicked
}


# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

def load_library(library_path: str) -> None:
    """Walk *library_path*, read every product.json, and rebuild the index."""
    global _index

    # ── Diagnostic: log the raw incoming value ─────────────────────────────
    print(f"IFC Product Library: load_library() called")
    print(f"  raw path  : {library_path!r}")
    print(f"  type      : {type(library_path)}")

    _index = {
        "products": {},
        "by_category": {},
        "library_meta": {},
        "loaded": False,
        "library_path": library_path,
        "error": "",
    }
    _ui_state["selected_category"] = ""
    _ui_state["selected_product_slug"] = ""

    if not library_path or not library_path.strip():
        msg = "No library path configured — open Addon Preferences to set it."
        print(f"  → ABORT: {msg}")
        _index["error"] = msg
        return

    # Strip trailing slash/whitespace that Blender's DIR_PATH sometimes adds
    library_path = library_path.strip().rstrip("/").rstrip("\\")
    print(f"  stripped  : {library_path!r}")

    resolved = os.path.realpath(library_path)
    print(f"  realpath  : {resolved!r}")
    print(f"  exists    : {os.path.exists(resolved)}")
    print(f"  isdir     : {os.path.isdir(resolved)}")

    # Also try os.path.exists on the un-resolved path in case realpath breaks
    # something with Unicode or symlinks
    print(f"  exists(raw): {os.path.exists(library_path)}")
    print(f"  isdir(raw) : {os.path.isdir(library_path)}")

    if not os.path.isdir(resolved):
        # Fallback: try the un-resolved path (handles some symlink edge cases)
        if os.path.isdir(library_path):
            print(f"  realpath failed but raw path is a dir — using raw")
            resolved = library_path
        else:
            msg = f"Folder not found: {resolved}"
            print(f"  → ABORT: {msg}")
            _index["error"] = msg
            _index["library_path"] = resolved
            return

    _index["library_path"] = resolved

    # ── library.json ───────────────────────────────────────────────────────
    library_json_path = os.path.join(resolved, "library.json")
    print(f"  library.json: {library_json_path!r}  exists={os.path.exists(library_json_path)}")
    if os.path.exists(library_json_path):
        try:
            with open(library_json_path, "r", encoding="utf-8") as fh:
                _index["library_meta"] = json.load(fh)
            print(f"  library.json loaded OK")
        except Exception as exc:
            print(f"  library.json ERROR: {exc}")

    # ── Walk for product.json files ────────────────────────────────────────
    loaded = 0
    print(f"  walking tree...")
    for root, _dirs, files in os.walk(resolved):
        if "product.json" not in files:
            continue

        product_json_path = os.path.join(root, "product.json")
        try:
            with open(product_json_path, "r", encoding="utf-8") as fh:
                product = json.load(fh)

            slug = product.get("identity", {}).get("slug") or os.path.basename(root)
            product["_folder_path"] = root

            _index["products"][slug] = product

            cat_path = product.get("category", {}).get("path", "")
            if cat_path:
                _index["by_category"].setdefault(cat_path, []).append(slug)

            loaded += 1
            print(f"    loaded: {slug}")

        except Exception as exc:
            print(f"    ERROR reading {product_json_path}: {exc}")

    _index["loaded"] = True
    print(f"IFC Product Library: ✓ Loaded {loaded} products from {resolved}")


# ---------------------------------------------------------------------------
# Index accessors
# ---------------------------------------------------------------------------

def get_index() -> dict:
    return _index


def get_product(slug: str) -> dict | None:
    return _index["products"].get(slug)


def get_products_in_category(category_path: str) -> list[tuple[str, dict]]:
    """Return [(slug, product), …] for a single (non-recursive) category path."""
    return [
        (s, _index["products"][s])
        for s in _index["by_category"].get(category_path, [])
    ]


def count_products_in_tree(category_path: str, subcategories: list) -> int:
    """Recursively count products in *category_path* and all its subcategories."""
    count = len(_index["by_category"].get(category_path, []))
    for sub in subcategories:
        count += count_products_in_tree(sub["path"], sub.get("subcategories", []))
    return count


def search_products(query: str) -> list[tuple[str, dict]]:
    """Case-insensitive substring search across name, manufacturer, description, tags."""
    if not query:
        return []
    q = query.lower()
    results = []
    for slug, product in _index["products"].items():
        identity = product.get("identity", {})
        category = product.get("category", {})
        haystack = " ".join([
            identity.get("name", ""),
            identity.get("manufacturer", ""),
            identity.get("description", ""),
            " ".join(category.get("tags", [])),
        ]).lower()
        if q in haystack:
            results.append((slug, product))
    # Sort by name for stable ordering
    results.sort(key=lambda t: t[1].get("identity", {}).get("name", ""))
    return results


# ---------------------------------------------------------------------------
# UI state mutators
# ---------------------------------------------------------------------------

def get_ui_state() -> dict:
    return _ui_state


def toggle_category(category_path: str) -> None:
    if category_path in _ui_state["expanded_categories"]:
        _ui_state["expanded_categories"].discard(category_path)
    else:
        _ui_state["expanded_categories"].add(category_path)


def select_category(category_path: str) -> None:
    _ui_state["selected_category"] = category_path
    _ui_state["selected_product_slug"] = ""


def select_product(slug: str) -> None:
    _ui_state["selected_product_slug"] = slug
