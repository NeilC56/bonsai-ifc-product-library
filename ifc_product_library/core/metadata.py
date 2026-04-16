"""
IFC Product Library — Metadata Utilities

Functions for:
  - Generating product slugs from names
  - Building product.json templates
  - Writing product.json to disk with validation
  - Extracting bounding-box dimensions from Blender objects
"""

import json
import os
import re
import datetime


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert a product name to a filesystem-safe slug.

    'Contour 21 Basin 500mm' → 'contour-21-basin-500mm'
    'Edit L Wall-Hung Basin 500×450' → 'edit-l-wall-hung-basin-500x450'
    """
    s = name.lower().strip()
    # Replace × (multiplication sign) with x
    s = s.replace("×", "x")
    # Replace any non-alphanumeric character (except hyphens) with a hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing hyphens and collapse runs
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def unique_slug(base_slug: str, folder_path: str) -> str:
    """Return a slug that doesn't already exist as a subdirectory of folder_path.

    If 'contour-21-basin' already exists, returns 'contour-21-basin-2', etc.
    """
    if not os.path.exists(os.path.join(folder_path, base_slug)):
        return base_slug
    counter = 2
    while True:
        candidate = f"{base_slug}-{counter}"
        if not os.path.exists(os.path.join(folder_path, candidate)):
            return candidate
        counter += 1


# ---------------------------------------------------------------------------
# Template builder
# ---------------------------------------------------------------------------

def product_json_template(category_path: str = "") -> dict:
    """Return a product.json dict pre-filled with defaults for a category path."""
    today = datetime.date.today().isoformat()
    return {
        "$schema": "https://example.com/ifc-product-library/v0.1/product.schema.json",
        "schema_version": "0.1",
        "identity": {
            "name": "",
            "slug": "",
            "description": "",
            "manufacturer": "",
            "model_number": "",
            "product_url": "",
        },
        "category": {
            "path": category_path,
            "tags": [],
        },
        "ifc": {
            "class": "",
            "predefined_type": "",
            "ifc_version": "IFC4",
        },
        "classification": {
            "uniclass_2015": {"code": "", "description": ""},
            "omniclass": {"code": "", "description": ""},
        },
        "dimensions": {
            "width_mm": 0,
            "depth_mm": 0,
            "height_mm": 0,
            "weight_kg": 0,
            "unit_system": "metric",
        },
        "properties": {},
        "compliance": {
            "doc_m": False,
            "building_regs": [],
            "standards": [],
        },
        "provenance": {
            "created_date": today,
            "created_by": "",
            "geometry_source": "",
            "geometry_licence": "",
            "ifc_authored_in": "IFC Product Library addon",
            "last_modified": today,
            "library_version": "0.1",
        },
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = [
    ("identity", "name"),
    ("category", "path"),
    ("ifc", "class"),
]


def validate_metadata(meta: dict) -> list[str]:
    """Return a list of error strings. Empty list means valid."""
    errors = []
    for section, field in _REQUIRED_FIELDS:
        val = meta.get(section, {}).get(field, "")
        if not val or not str(val).strip():
            errors.append(f"'{section}.{field}' is required")
    return errors


# ---------------------------------------------------------------------------
# Write product.json
# ---------------------------------------------------------------------------

def write_product_json(folder_path: str, metadata: dict) -> None:
    """Write metadata to <folder_path>/product.json.

    Raises ValueError if required fields are missing.
    Raises OSError if the folder doesn't exist.
    """
    errors = validate_metadata(metadata)
    if errors:
        raise ValueError("Metadata validation failed:\n  " + "\n  ".join(errors))

    out_path = os.path.join(folder_path, "product.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Dimension extraction from Blender objects
# ---------------------------------------------------------------------------

def extract_dimensions_from_objects(object_names: list[str]) -> dict:
    """Compute the axis-aligned bounding box of all named objects combined.

    Returns dimensions in millimetres (Blender uses metres internally).

    Returns:
        {'width_mm': float, 'depth_mm': float, 'height_mm': float}
    or zeros if no objects are found.
    """
    try:
        import bpy
        import mathutils

        min_co = mathutils.Vector((float("inf"),) * 3)
        max_co = mathutils.Vector((float("-inf"),) * 3)
        found_any = False

        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "MESH":
                continue
            found_any = True
            mat = obj.matrix_world
            for v in obj.data.vertices:
                world_co = mat @ v.co
                min_co.x = min(min_co.x, world_co.x)
                min_co.y = min(min_co.y, world_co.y)
                min_co.z = min(min_co.z, world_co.z)
                max_co.x = max(max_co.x, world_co.x)
                max_co.y = max(max_co.y, world_co.y)
                max_co.z = max(max_co.z, world_co.z)

        if not found_any:
            return {"width_mm": 0, "depth_mm": 0, "height_mm": 0}

        # Blender units are metres; multiply by 1000 for mm, round to 1 dp
        scale = 1000.0
        return {
            "width_mm":  round((max_co.x - min_co.x) * scale, 1),
            "depth_mm":  round((max_co.y - min_co.y) * scale, 1),
            "height_mm": round((max_co.z - min_co.z) * scale, 1),
        }
    except Exception:
        return {"width_mm": 0, "depth_mm": 0, "height_mm": 0}


def count_faces(object_names: list[str]) -> int:
    """Return total polygon count across all named mesh objects.

    Uses the evaluated mesh (post-modifiers) when a depsgraph is available,
    so the Decimate modifier preview is reflected in the count.
    """
    try:
        import bpy
        total = 0
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "MESH":
                continue
            eval_obj = obj.evaluated_get(depsgraph)
            total += len(eval_obj.data.polygons)
        return total
    except Exception:
        # Fallback: count base mesh polygons without modifier evaluation
        try:
            import bpy
            total = 0
            for name in object_names:
                obj = bpy.data.objects.get(name)
                if obj is not None and obj.type == "MESH":
                    total += len(obj.data.polygons)
            return total
        except Exception:
            return 0


def face_count_label(count: int) -> tuple[str, str]:
    """Return (status, message) for a face count.

    Status is one of: 'green', 'amber', 'red', 'blocked'.
    """
    if count < 5_000:
        return "green", "Good for BIM"
    elif count < 20_000:
        return "amber", "Moderate — consider simplifying"
    elif count < 50_000:
        return "red", "Heavy — recommend simplifying"
    else:
        return "blocked", "Too large — exceeds maximum"
