"""
IFC Product Library — Save to Library Operators

Operators for Step 4 (Save to Library):
  - IFCLIB_OT_SaveToLibrary  — writes product.ifc + product.json, refreshes index
  - IFCLIB_OT_SaveAndInsert  — does the above, then inserts the product into the active project
"""

import os
import shutil
import bpy
from bpy.props import BoolProperty

from ..core import wizard_state, metadata as meta_utils, ifc_writer
from ..core import library_index


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _redraw_panels():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _get_library_path() -> str:
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.library_path
    except Exception:
        pass
    return ""


def _get_max_face_count() -> int:
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.max_face_count
    except Exception:
        pass
    return 50_000


def _get_wizard_objects() -> list:
    w = wizard_state.get_wizard()
    return [
        bpy.data.objects[name]
        for name in w["imported_object_names"]
        if name in bpy.data.objects
    ]


# ---------------------------------------------------------------------------
# Save pipeline
# ---------------------------------------------------------------------------

def _do_save(operator) -> tuple[bool, str]:
    """Execute the full save pipeline. Returns (success, product_slug_or_error)."""
    w = wizard_state.get_wizard()
    meta = w.get("metadata", {})

    # Route IFC-source products to a different pipeline: copy the file rather
    # than creating one from Blender mesh geometry.
    if w.get("format") == "IFC" and w.get("file_path"):
        return _do_save_ifc_source(w, meta)

    # ------------------------------------------------------------------
    # Validate metadata
    # ------------------------------------------------------------------
    errors = meta_utils.validate_metadata(meta)
    if errors:
        return False, "Metadata incomplete:\n  " + "\n  ".join(errors)

    # ------------------------------------------------------------------
    # Face count check
    # ------------------------------------------------------------------
    max_faces = _get_max_face_count()
    current = meta_utils.count_faces(w["imported_object_names"])
    if current > max_faces:
        return False, (
            f"Face count ({current:,}) exceeds the maximum ({max_faces:,}). "
            "Use 'Optimise for BIM' to reduce the polygon count first."
        )

    # ------------------------------------------------------------------
    # Find the single mesh object
    # ------------------------------------------------------------------
    objs = _get_wizard_objects()
    mesh_objs = [o for o in objs if o.type == "MESH"]
    if not mesh_objs:
        return False, "No mesh geometry to save"
    if len(mesh_objs) > 1:
        return False, "Merge objects into a single mesh before saving"

    mesh_obj = mesh_objs[0]

    # ------------------------------------------------------------------
    # If decimate is still in preview mode, apply it now
    # ------------------------------------------------------------------
    if w.get("decimate_preview_active"):
        _apply_decimate_modifier(mesh_obj)
        w["decimate_preview_active"] = False

    # ------------------------------------------------------------------
    # Determine library path and category folder
    # ------------------------------------------------------------------
    library_path = _get_library_path()
    if not library_path or not os.path.isdir(library_path):
        return False, f"Library path not set or doesn't exist: {library_path!r}"

    category_path = meta.get("category", {}).get("path", "")
    if not category_path:
        return False, "No category selected"

    category_folder = os.path.join(library_path, category_path.replace("/", os.sep))
    os.makedirs(category_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # Generate unique slug
    # ------------------------------------------------------------------
    product_name = meta["identity"]["name"].strip()
    base_slug = meta_utils.slugify(product_name)
    slug = meta_utils.unique_slug(base_slug, category_folder)
    meta["identity"]["slug"] = slug
    meta["category"]["path"] = category_path

    product_folder = os.path.join(category_folder, slug)
    os.makedirs(product_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # Inject final bounding-box dimensions into metadata
    # ------------------------------------------------------------------
    dims = meta_utils.extract_dimensions_from_objects(w["imported_object_names"])
    if dims["width_mm"] > 0:
        meta["dimensions"].update(dims)

    # ------------------------------------------------------------------
    # Write product.ifc
    # ------------------------------------------------------------------
    ifc_path = os.path.join(product_folder, "product.ifc")
    try:
        ifc_writer.create_product_ifc(mesh_obj.name, meta, ifc_path)
    except Exception as e:
        return False, f"IFC export failed: {e}"

    # ------------------------------------------------------------------
    # Write product.json
    # ------------------------------------------------------------------
    try:
        meta_utils.write_product_json(product_folder, meta)
    except Exception as e:
        if os.path.exists(ifc_path):
            os.remove(ifc_path)
        try:
            os.rmdir(product_folder)
        except OSError:
            pass
        return False, f"JSON write failed: {e}"

    # ------------------------------------------------------------------
    # Refresh library index
    # ------------------------------------------------------------------
    try:
        library_index.load_library(library_path)
    except Exception as e:
        print(f"IFC Product Library: index refresh failed after save: {e}")

    return True, f"{category_path}/{slug}"


def _do_save_ifc_source(w: dict, meta: dict) -> tuple[bool, str]:
    """Save pipeline for IFC-source products.

    Copies the original manufacturer IFC file as product.ifc rather than
    generating one from Blender mesh geometry.  The file is assumed to already
    be valid IFC — we don't re-export it.
    """
    # ------------------------------------------------------------------
    # Validate metadata
    # ------------------------------------------------------------------
    errors = meta_utils.validate_metadata(meta)
    if errors:
        return False, "Metadata incomplete:\n  " + "\n  ".join(errors)

    src_ifc = w.get("file_path", "")
    if not src_ifc or not os.path.isfile(src_ifc):
        return False, f"Source IFC file not found: {src_ifc!r}"

    # ------------------------------------------------------------------
    # Library path and category folder
    # ------------------------------------------------------------------
    library_path = _get_library_path()
    if not library_path or not os.path.isdir(library_path):
        return False, f"Library path not set or doesn't exist: {library_path!r}"

    category_path = meta.get("category", {}).get("path", "")
    if not category_path:
        return False, "No category selected — choose a category in the form above"

    category_folder = os.path.join(library_path, category_path.replace("/", os.sep))
    os.makedirs(category_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # Generate unique slug and create product folder
    # ------------------------------------------------------------------
    product_name = meta["identity"]["name"].strip()
    base_slug = meta_utils.slugify(product_name)
    slug = meta_utils.unique_slug(base_slug, category_folder)
    meta["identity"]["slug"] = slug
    meta["category"]["path"] = category_path

    product_folder = os.path.join(category_folder, slug)
    os.makedirs(product_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # Copy source IFC file → product.ifc
    # ------------------------------------------------------------------
    dst_ifc = os.path.join(product_folder, "product.ifc")
    try:
        shutil.copy2(src_ifc, dst_ifc)
    except Exception as e:
        try:
            os.rmdir(product_folder)
        except OSError:
            pass
        return False, f"Failed to copy IFC file: {e}"

    # ------------------------------------------------------------------
    # Write product.json
    # ------------------------------------------------------------------
    try:
        meta_utils.write_product_json(product_folder, meta)
    except Exception as e:
        if os.path.exists(dst_ifc):
            os.remove(dst_ifc)
        try:
            os.rmdir(product_folder)
        except OSError:
            pass
        return False, f"JSON write failed: {e}"

    # ------------------------------------------------------------------
    # Refresh library index
    # ------------------------------------------------------------------
    try:
        library_index.load_library(library_path)
    except Exception as e:
        print(f"IFC Product Library: index refresh failed after save: {e}")

    return True, f"{category_path}/{slug}"


def _apply_decimate_modifier(obj):
    """Apply the IFCLib_Decimate modifier if present."""
    bpy.context.view_layer.objects.active = obj
    for mod in obj.modifiers:
        if mod.name == "IFCLib_Decimate":
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print(f"IFC Product Library: could not apply decimate modifier: {e}")
            break


# ---------------------------------------------------------------------------
# SaveToLibrary operator
# ---------------------------------------------------------------------------

class IFCLIB_OT_SaveToLibrary(bpy.types.Operator):
    """Save the product to the library (writes product.ifc and product.json)"""
    bl_idname = "ifclib.save_to_library"
    bl_label = "Save to Library"
    bl_description = "Save this product to the library"

    def execute(self, context):
        w = wizard_state.get_wizard()

        success, result = _do_save(self)

        if not success:
            w["save_error"] = result
            self.report({"ERROR"}, result)
            _redraw_panels()
            return {"CANCELLED"}

        # Success — clean up wizard objects and reset state
        product_path = result
        _cleanup_wizard_objects()
        wizard_state.reset_wizard()

        self.report({"INFO"}, f"Saved: {product_path}")
        _redraw_panels()
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# SaveAndInsert operator
# ---------------------------------------------------------------------------

class IFCLIB_OT_SaveAndInsert(bpy.types.Operator):
    """Save the product to the library and immediately insert it into the active project"""
    bl_idname = "ifclib.save_and_insert"
    bl_label = "Save & Insert into Model"
    bl_description = "Save to library and insert into the active Bonsai IFC project"

    def execute(self, context):
        w = wizard_state.get_wizard()

        success, result = _do_save(self)

        if not success:
            w["save_error"] = result
            self.report({"ERROR"}, result)
            _redraw_panels()
            return {"CANCELLED"}

        product_slug = result.split("/")[-1] if "/" in result else result
        _cleanup_wizard_objects()
        wizard_state.reset_wizard()
        _redraw_panels()

        # Select the newly saved product in the library UI state, then insert
        try:
            library_index.select_product(product_slug)
            bpy.ops.ifclib.insert_product("INVOKE_DEFAULT")
        except Exception as e:
            self.report({"WARNING"}, f"Saved OK but insert failed: {e}")
            return {"FINISHED"}

        self.report({"INFO"}, f"Saved and inserted: {product_slug}")
        return {"FINISHED"}


def _cleanup_wizard_objects():
    """Remove all objects that were imported during the wizard session."""
    w = wizard_state.get_wizard()
    for name in list(w.get("imported_object_names", [])):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    IFCLIB_OT_SaveToLibrary,
    IFCLIB_OT_SaveAndInsert,
)
