"""
IFC Product Library — Blender Addon
Phase 1: Browse & Insert MVP

Blender 5.x extension format (blender_manifest.toml).
Requires: Bonsai (BlenderBIM) for the insert operation.
"""

import os
import bpy

# Expose the full package name BEFORE importing sub-modules so they can
# import it with `from .. import _ADDON_ID`.
#
# In development (addon loaded from folder):  "ifc_product_library"
# Installed as Blender extension:             "bl_ext.user_default.ifc_product_library"
#
# Using __package__.split(".")[0] would give "bl_ext" in the installed case,
# which breaks every addons.get() lookup.  Always use the full name.
_ADDON_ID: str = __package__

from . import preferences, props
from .panels import library_browser
from .operators import browse_ops, insert_ops, import_ops, convert_ops
from .panels import import_wizard

# All classes that need to be registered with Blender
_classes = (
    preferences.IFCProductLibraryPreferences,
    props.IFCProductLibraryState,
    props.IFCLibMetaFormProps,
    # Phase 1 — Browse & Insert
    browse_ops.IFCLIB_OT_BrowseCategory,
    browse_ops.IFCLIB_OT_SelectProduct,
    browse_ops.IFCLIB_OT_RefreshLibrary,
    insert_ops.IFCLIB_OT_InsertProduct,
    # Phase 2 — Import Wizard (step operators)
    *import_ops.classes,
    # Phase 2 — Import Wizard (save operators)
    *convert_ops.classes,
    # Phase 2 — Import Wizard (panel helper operators)
    *import_wizard.classes,
    # Panel (must be last — operators it references must already be registered)
    library_browser.IFC_PT_ProductLibrary,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    # Attach the search-query property to every Scene
    bpy.types.Scene.ifc_product_library = bpy.props.PointerProperty(
        type=props.IFCProductLibraryState
    )
    # Attach the Step 4 metadata form property group to every Scene
    bpy.types.Scene.ifclib_meta_form = bpy.props.PointerProperty(
        type=props.IFCLibMetaFormProps
    )

    # Auto-load the library using the current (or default) preferences path
    _try_initial_load()


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    if hasattr(bpy.types.Scene, "ifc_product_library"):
        del bpy.types.Scene.ifc_product_library
    if hasattr(bpy.types.Scene, "ifclib_meta_form"):
        del bpy.types.Scene.ifclib_meta_form


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _try_initial_load() -> None:
    """Attempt to load the library on addon activation.

    Wrapped in a broad try/except because bpy.context may be restricted
    during registration (e.g. when Blender starts with the addon pre-enabled).
    If this fails, the panel's draw-time lazy-load will pick it up.
    """
    from .core import library_index
    print(f"IFC Product Library: _try_initial_load() — package={_ADDON_ID!r}")
    try:
        addon_prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        print(f"  addon_prefs: {addon_prefs}")
        if addon_prefs is None:
            print("  → no addon_prefs found; will rely on panel lazy-load")
            return
        lib_path = addon_prefs.preferences.library_path
        print(f"  stored library_path: {lib_path!r}")
        if lib_path and lib_path.strip():
            library_index.load_library(lib_path)
        else:
            # Fall back to the path computed relative to __file__ at install time
            from .preferences import _DEFAULT_LIBRARY_PATH
            print(f"  preference blank — trying default: {_DEFAULT_LIBRARY_PATH!r}")
            print(f"  default exists: {os.path.isdir(_DEFAULT_LIBRARY_PATH)}")
            if os.path.isdir(_DEFAULT_LIBRARY_PATH):
                library_index.load_library(_DEFAULT_LIBRARY_PATH)
            else:
                print("  → default path not found either; panel will prompt user")
    except Exception as exc:
        print(f"IFC Product Library: _try_initial_load() exception: {exc}")
