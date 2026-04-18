"""Span table loader and query helper for the Array Insert span advisory.

Span table JSON files live in:
    <library_root>/span-tables/*.json

Each file declares a list of load_cases and a list of sections.  Each section
has a ``spans`` dict keyed by load_case key, then by spacing in mm (as a
string: "400", "450", "600").  The value is the maximum clear span in mm for
that depth / load case / spacing combination.

Module-level cache avoids re-parsing JSON on every panel redraw.  Call
``invalidate_cache()`` whenever the library folder changes.
"""

import os
import json

# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------

_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def get_span_tables_dir(library_path: str) -> str:
    """Return the span-tables sub-directory path (may not exist yet)."""
    return os.path.join(library_path, "span-tables")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def list_span_tables(library_path: str) -> list[dict]:
    """Return a list of dicts describing each JSON span table found.

    Each dict has: ``filename``, ``manufacturer``, ``system``.
    Returns ``[]`` silently if the directory doesn't exist or contains no
    valid JSON files.
    """
    tables_dir = get_span_tables_dir(library_path)
    if not os.path.isdir(tables_dir):
        return []

    result = []
    try:
        entries = sorted(os.listdir(tables_dir))
    except OSError:
        return []

    for fname in entries:
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(tables_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            result.append({
                "filename":     fname,
                "manufacturer": data.get("manufacturer", fname),
                "system":       data.get("system", ""),
            })
        except Exception as exc:
            print(f"IFC Product Library [span_tables]: skipping {fname}: {exc}")
            # Still include the file so the user knows it exists but is broken
            result.append({
                "filename":     fname,
                "manufacturer": fname,
                "system":       "(parse error)",
            })

    return result


def load_span_table(library_path: str, filename: str) -> dict | None:
    """Load and cache a span table JSON.  Returns ``None`` on any error."""
    if not filename:
        return None

    if filename in _cache:
        return _cache[filename]

    tables_dir = get_span_tables_dir(library_path)
    path = os.path.join(tables_dir, filename)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        _cache[filename] = data
        return data
    except Exception as exc:
        print(f"IFC Product Library [span_tables]: could not load {filename}: {exc}")
        return None


def invalidate_cache() -> None:
    """Clear the in-memory cache.  Call when the library folder changes."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_load_case_names(table: dict) -> list[str]:
    """Return the human-readable load case names from a loaded table."""
    return [lc["name"] for lc in table.get("load_cases", [])]


def query_span_table(
    table: dict,
    span_mm: int,
    load_case_key: str,
    spacing_mm: int,
) -> list[dict]:
    """Look up all sections for a given load case key and span.

    Parameters
    ----------
    table:          Parsed JSON dict from ``load_span_table()``.
    span_mm:        The user's span length in mm (compared against max spans).
    load_case_key:  The load case ``key`` string (e.g. ``"domestic_floor"``).
    spacing_mm:     The user's joist spacing in mm.  The nearest available
                    spacing key in the JSON is used automatically.

    Returns
    -------
    List of dicts with keys:
        depth_mm, top_chord, max_span_mm, status, used_spacing_mm

    ``status`` is one of ``"Short"``, ``"OK"``, or ``"Generous"``
    (>= 10 % headroom).  Returns ``[]`` if the load case is not found.
    """
    # Find the load case
    load_case = None
    for lc in table.get("load_cases", []):
        if lc.get("key") == load_case_key:
            load_case = lc
            break
    if load_case is None:
        return []

    results = []
    for section in table.get("sections", []):
        spans_for_lc = section.get("spans", {}).get(load_case_key)
        if not spans_for_lc:
            continue

        # Find the nearest available spacing key
        available = sorted(int(k) for k in spans_for_lc.keys())
        nearest = min(available, key=lambda s: abs(s - spacing_mm))
        max_span = spans_for_lc[str(nearest)]

        margin = max_span - span_mm
        if margin < 0:
            status = "Short"
        elif max_span > 0 and margin / max_span >= 0.10:
            status = "Generous"
        else:
            status = "OK"

        results.append({
            "depth_mm":        section.get("depth_mm", 0),
            "top_chord":       section.get("top_chord", ""),
            "max_span_mm":     max_span,
            "status":          status,
            "used_spacing_mm": nearest,
        })

    return results
