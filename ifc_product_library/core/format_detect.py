"""
IFC Product Library — Format Detection

Maps file extensions to:
  - human-readable format name
  - bpy.ops namespace + operator name (None for special cases)
  - special handling flag: None | "ifc" | "step"

Importer op names are verified at call time in import_ops.py to handle
any differences in Blender 5.1 vs earlier versions gracefully.
"""

import os

# ---------------------------------------------------------------------------
# Format map: extension → (label, bpy_op_string, special)
# bpy_op_string is the full "namespace.operator_name" used in getattr(bpy.ops.X, Y)
# ---------------------------------------------------------------------------

_FORMATS: dict[str, tuple[str, str | None, str | None]] = {
    # (label, bpy_op_string, special)
    ".obj":  ("OBJ",      "wm.obj_import",             None),
    ".stl":  ("STL",      "wm.stl_import",             None),
    ".gltf": ("glTF",     "import_scene.gltf",         None),
    ".glb":  ("GLB",      "import_scene.gltf",         None),
    ".fbx":  ("FBX",      "import_scene.fbx",          None),
    ".dae":  ("Collada",  "wm.collada_import",         None),
    ".ply":  ("PLY",      "wm.ply_import",             None),
    ".3ds":  ("3DS",      "import_scene.autodesk_3ds", None),
    ".x3d":  ("X3D",      "import_scene.x3d",          None),
    ".wrl":  ("X3D/VRML", "import_scene.x3d",          None),
    ".usd":  ("USD",      "wm.usd_import",             None),
    ".usda": ("USD",      "wm.usd_import",             None),
    ".usdc": ("USD",      "wm.usd_import",             None),
    ".usdz": ("USD",      "wm.usd_import",             None),
    ".dxf":  ("DXF",      "import_scene.dxf",          None),
    ".ifc":  ("IFC",      None,                        "ifc"),
    ".step": ("STEP",     None,                        "step"),
    ".stp":  ("STEP",     None,                        "step"),
}

# Extensions that need the glob filter string for the file browser
FILTER_GLOB = (
    "*.obj;*.stl;*.gltf;*.glb;*.fbx;*.dae;*.ply;*.3ds;*.x3d;*.wrl;"
    "*.usd;*.usda;*.usdc;*.usdz;*.dxf;*.ifc;*.step;*.stp"
)


def detect(filepath: str) -> dict:
    """Detect the format of a file from its extension.

    Returns a dict:
        {
            'format':  str,          # e.g. "OBJ", "STEP", "IFC", "" if unknown
            'op':      str | None,   # e.g. "wm.obj_import", None for special/unknown
            'special': str | None,   # "ifc" | "step" | None
            'known':   bool,         # False if extension not in our table
        }
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in _FORMATS:
        label, op, special = _FORMATS[ext]
        return {"format": label, "op": op, "special": special, "known": True}
    return {"format": "", "op": None, "special": None, "known": False}


def get_importer_op(op_string: str):
    """Resolve a bpy_op_string like 'wm.obj_import' to the bpy.ops callable.

    Returns the operator callable, or None if it doesn't exist in this
    Blender build (some formats require addons to be enabled).
    """
    try:
        import bpy
        namespace, name = op_string.split(".", 1)
        ns = getattr(bpy.ops, namespace, None)
        if ns is None:
            return None
        op = getattr(ns, name, None)
        return op
    except Exception:
        return None


def is_op_available(op_string: str) -> bool:
    """Return True if the importer operator exists in the current Blender build."""
    return get_importer_op(op_string) is not None


def label_for_path(filepath: str) -> str:
    """Return the format label for a filepath, or 'Unknown' if not recognised."""
    result = detect(filepath)
    return result["format"] if result["known"] else "Unknown"
