"""
IFC Product Library — Import & Cleanup Operators

Operators for the Import Wizard steps 1 and 2:
  - Start / cancel wizard
  - File selection + import (all supported formats)
  - Use already-selected Blender objects as source
  - Navigation (Next / Back)
  - Geometry cleanup: remove small parts, merge, Optimise for BIM (decimate), set origin

All operators call _redraw_panels() after mutating wizard state so the sidebar
panel updates immediately.
"""

import bpy
import os
from bpy.props import StringProperty, CollectionProperty, BoolProperty, FloatProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper

from ..core import wizard_state, format_detect, metadata as meta_utils, templates


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _redraw_panels():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _get_wizard_objects() -> list:
    """Return the live bpy.types.Object references for the current wizard session."""
    w = wizard_state.get_wizard()
    objs = []
    for name in w["imported_object_names"]:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            objs.append(obj)
    return objs


def _update_face_count():
    """Recompute and store the current face count in wizard state."""
    w = wizard_state.get_wizard()
    count = meta_utils.count_faces(w["imported_object_names"])
    w["face_count_current"] = count
    return count


# ---------------------------------------------------------------------------
# Start / Cancel
# ---------------------------------------------------------------------------

class IFCLIB_OT_StartWizard(bpy.types.Operator):
    """Open the Import New Product wizard"""
    bl_idname = "ifclib.start_wizard"
    bl_label = "Add New Product"
    bl_description = "Open the wizard to import a new product into the library"

    def execute(self, context):
        wizard_state.reset_wizard()
        wizard_state.get_wizard()["active"] = True
        wizard_state.set_wizard_step(1)
        _redraw_panels()
        return {"FINISHED"}


class IFCLIB_OT_CancelWizard(bpy.types.Operator):
    """Cancel the Import Wizard and clean up imported objects"""
    bl_idname = "ifclib.cancel_wizard"
    bl_label = "Cancel"
    bl_description = "Cancel the import wizard and remove any imported geometry"

    def execute(self, context):
        # Delete objects that were imported during this wizard session
        objs = _get_wizard_objects()
        for obj in objs:
            bpy.data.objects.remove(obj, do_unlink=True)

        wizard_state.reset_wizard()
        _redraw_panels()
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Step navigation
# ---------------------------------------------------------------------------

class IFCLIB_OT_WizardNext(bpy.types.Operator):
    """Advance the wizard to the next step"""
    bl_idname = "ifclib.wizard_next"
    bl_label = "Next"
    bl_description = "Proceed to the next step"

    def execute(self, context):
        w = wizard_state.get_wizard()
        step = w["step"]

        # Validate current step before advancing
        error = self._validate(w, step)
        if error:
            self.report({"WARNING"}, error)
            return {"CANCELLED"}

        # If we're on step 1 and format is IFC, skip cleanup + classification
        if step == 1 and w.get("format") == "IFC":
            wizard_state.set_wizard_step(4)
        else:
            wizard_state.set_wizard_step(step + 1)

        # Auto-populate metadata when entering step 4
        if wizard_state.get_wizard()["step"] == 4:
            _prefill_metadata(w)
            # Load float/bool values into the registered PropertyGroup.
            # Must be done here (operator), not inside the panel draw function.
            from ..props import load_meta_to_pg
            load_meta_to_pg(context, w["metadata"])

        _redraw_panels()
        return {"FINISHED"}

    def _validate(self, w, step) -> str:
        """Return an error string or empty string if valid."""
        if step == 1:
            if w["source_mode"] == "file" and not w["file_path"]:
                return "Please select a file first"
            if w["source_mode"] == "file" and not w["imported_object_names"]:
                return "File not yet imported — click the format button first"
            if w["source_mode"] == "selected" and not w["imported_object_names"]:
                return "No objects tagged — select objects and click 'Use Selected'"
        if step == 2:
            if not w["imported_object_names"]:
                return "No geometry to proceed with"
            max_faces = _get_max_face_count()
            if w["face_count_current"] > max_faces:
                return (
                    f"Face count ({w['face_count_current']:,}) exceeds the "
                    f"maximum ({max_faces:,}). Use 'Optimise for BIM' first."
                )
        if step == 3:
            if not w["category_path"]:
                return "Please select a category"
        return ""


def _prefill_metadata(w: dict) -> None:
    """Pre-fill the metadata dict when entering step 4."""
    if w.get("metadata"):
        return  # already set
    tmpl = meta_utils.product_json_template(w.get("category_path", ""))
    tmpl["ifc"]["class"] = w.get("ifc_class", "")
    tmpl["ifc"]["predefined_type"] = w.get("predefined_type", "")
    tmpl["ifc"]["ifc_version"] = w.get("ifc_version", "IFC4")

    # Pre-fill dimensions from bounding box
    dims = meta_utils.extract_dimensions_from_objects(w.get("imported_object_names", []))
    tmpl["dimensions"].update(dims)

    # Pre-fill uniclass hint
    hint = templates.get_uniclass_hint(w.get("category_path", ""))
    if hint:
        tmpl["classification"]["uniclass_2015"]["code"] = hint

    # Pre-fill property defaults from template
    for field in templates.get_property_fields(w.get("category_path", "")):
        tmpl["properties"][field["key"]] = field.get("default", "")

    w["metadata"] = tmpl


def _get_max_face_count() -> int:
    """Read the max_face_count from addon preferences, defaulting to 50,000."""
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.max_face_count
    except Exception:
        pass
    return 50_000


class IFCLIB_OT_WizardBack(bpy.types.Operator):
    """Go back to the previous wizard step"""
    bl_idname = "ifclib.wizard_back"
    bl_label = "Back"
    bl_description = "Return to the previous step"

    def execute(self, context):
        w = wizard_state.get_wizard()
        wizard_state.set_wizard_step(w["step"] - 1)
        _redraw_panels()
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Step 1 — File import
# ---------------------------------------------------------------------------

class IFCLIB_OT_WizardImportFile(bpy.types.Operator, ImportHelper):
    """Select and import a geometry file into the wizard"""
    bl_idname = "ifclib.wizard_import_file"
    bl_label = "Browse & Import File"
    bl_description = "Select a 3D file to import into the product library wizard"

    # ImportHelper provides self.filepath
    filter_glob: StringProperty(
        default=format_detect.FILTER_GLOB,
        options={"HIDDEN"},
    )

    # Support multiple file selection for batch mode
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    directory: StringProperty(
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def execute(self, context):
        w = wizard_state.get_wizard()

        # Build list of full paths
        if self.files and len(self.files) > 0:
            file_paths = [
                os.path.join(self.directory, f.name)
                for f in self.files
                if f.name
            ]
        else:
            file_paths = [self.filepath]

        file_paths = [p for p in file_paths if os.path.isfile(p)]
        if not file_paths:
            self.report({"ERROR"}, "No valid files selected")
            return {"CANCELLED"}

        # Store batch list (even if only 1 file)
        w["batch_files"] = file_paths
        w["batch_index"] = 0

        # Import the first file
        return self._import_file(context, file_paths[0], w)

    def _import_file(self, context, filepath: str, w: dict):
        info = format_detect.detect(filepath)

        w["file_path"] = filepath
        w["format"] = info["format"]

        # Handle STEP — show guidance, don't import
        if info["special"] == "step":
            _redraw_panels()
            return {"FINISHED"}

        # Handle IFC — store path only, skip to metadata (Next will jump to step 4)
        if info["special"] == "ifc":
            _redraw_panels()
            return {"FINISHED"}

        if not info["known"] or not info["op"]:
            self.report({"WARNING"}, f"Unsupported format: {os.path.splitext(filepath)[1]}")
            _redraw_panels()
            return {"CANCELLED"}

        # Check the importer op exists in this Blender build
        if not format_detect.is_op_available(info["op"]):
            self.report(
                {"WARNING"},
                f"{info['format']} importer not available. "
                "Make sure the required addon is enabled in Preferences.",
            )
            _redraw_panels()
            return {"CANCELLED"}

        # Snapshot existing object names
        existing_names = {obj.name for obj in bpy.data.objects}

        # Call the appropriate importer
        result = _call_importer(info["op"], filepath)
        if result == {"CANCELLED"}:
            self.report({"WARNING"}, f"Import failed for: {os.path.basename(filepath)}")
            return {"CANCELLED"}

        # Identify newly imported objects
        new_names = [
            obj.name for obj in bpy.data.objects
            if obj.name not in existing_names and obj.type == "MESH"
        ]
        w["imported_object_names"] = new_names

        # Calculate initial face count
        count = meta_utils.count_faces(new_names)
        w["face_count_raw"] = count
        w["face_count_current"] = count

        _redraw_panels()
        return {"FINISHED"}


def _call_importer(op_string: str, filepath: str) -> set:
    """Call a Blender importer operator by its op_string."""
    try:
        namespace, name = op_string.split(".", 1)
        ns = getattr(bpy.ops, namespace)
        op = getattr(ns, name)
        result = op("EXEC_DEFAULT", filepath=filepath)
        return result
    except Exception as e:
        print(f"IFC Product Library: importer {op_string} failed: {e}")
        return {"CANCELLED"}


class IFCLIB_OT_WizardUseSelected(bpy.types.Operator):
    """Use the currently selected Blender objects as the product geometry"""
    bl_idname = "ifclib.wizard_use_selected"
    bl_label = "Use Selected Objects"
    bl_description = "Tag the currently selected mesh objects as the product geometry"

    def execute(self, context):
        selected_meshes = [
            obj.name for obj in context.selected_objects
            if obj.type == "MESH"
        ]
        if not selected_meshes:
            self.report({"WARNING"}, "No mesh objects selected")
            return {"CANCELLED"}

        w = wizard_state.get_wizard()
        w["source_mode"] = "selected"
        w["imported_object_names"] = selected_meshes
        w["file_path"] = ""
        w["format"] = "Blender"

        count = meta_utils.count_faces(selected_meshes)
        w["face_count_raw"] = count
        w["face_count_current"] = count

        _redraw_panels()
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Step 2 — Cleanup operators
# ---------------------------------------------------------------------------

class IFCLIB_OT_RemoveSmallParts(bpy.types.Operator):
    """Remove objects whose bounding box is smaller than the threshold"""
    bl_idname = "ifclib.remove_small_parts"
    bl_label = "Remove Small Parts"
    bl_description = "Delete objects smaller than the threshold in all three axes"
    bl_options = {"REGISTER", "UNDO"}

    threshold_mm: FloatProperty(
        name="Threshold (mm)",
        description="Objects with all dimensions below this are removed",
        default=5.0,
        min=0.1,
        max=500.0,
    )

    def execute(self, context):
        w = wizard_state.get_wizard()
        removed = []
        kept = []

        for name in list(w["imported_object_names"]):
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "MESH":
                continue

            # Compute world-space bounding box dimensions in mm
            dims_m = obj.dimensions  # in Blender metres, world scale applied
            w_mm = dims_m.x * 1000
            d_mm = dims_m.y * 1000
            h_mm = dims_m.z * 1000

            if w_mm < self.threshold_mm and d_mm < self.threshold_mm and h_mm < self.threshold_mm:
                removed.append(name)
                bpy.data.objects.remove(obj, do_unlink=True)
            else:
                kept.append(name)

        w["imported_object_names"] = kept
        _update_face_count()
        _redraw_panels()

        if removed:
            self.report({"INFO"}, f"Removed {len(removed)} small part(s)")
        else:
            self.report({"INFO"}, "No parts below threshold")

        return {"FINISHED"}

    def invoke(self, context, event):
        # Read default from prefs
        try:
            from .. import _ADDON_ID
            prefs = bpy.context.preferences.addons.get(_ADDON_ID)
            if prefs:
                self.threshold_mm = prefs.preferences.small_part_threshold_mm
        except Exception:
            pass
        return self.execute(context)


class IFCLIB_OT_MergeObjects(bpy.types.Operator):
    """Merge all wizard objects into a single mesh"""
    bl_idname = "ifclib.merge_objects"
    bl_label = "Merge into Single Object"
    bl_description = "Join all parts into one mesh object (required for single IFC entity)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        if len(objs) <= 1:
            self.report({"INFO"}, "Already a single object — nothing to merge")
            return {"FINISHED"}

        # Deselect all, then select wizard objects
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objs:
            obj.select_set(True)

        # Make the first object active
        context.view_layer.objects.active = objs[0]

        # Join
        bpy.ops.object.join()

        # After join, all selected objects become one with the active object's name
        merged_name = objs[0].name
        w["imported_object_names"] = [merged_name]

        _update_face_count()
        _redraw_panels()
        self.report({"INFO"}, f"Merged {len(objs)} objects into '{merged_name}'")
        return {"FINISHED"}


class IFCLIB_OT_ConvertToMesh(bpy.types.Operator):
    """Apply all modifiers and convert to plain mesh"""
    bl_idname = "ifclib.convert_to_mesh"
    bl_label = "Convert to Mesh"
    bl_description = "Apply all modifiers and make instances real (required for IFC export)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        bpy.ops.object.select_all(action="DESELECT")
        for obj in objs:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            try:
                bpy.ops.object.convert(target="MESH")
            except Exception:
                pass

        _update_face_count()
        _redraw_panels()
        return {"FINISHED"}


class IFCLIB_OT_OptimiseForBIM(bpy.types.Operator):
    """Apply a Decimate modifier to target ~4,000 faces (preview — not yet applied to mesh)"""
    bl_idname = "ifclib.optimise_for_bim"
    bl_label = "Optimise for BIM"
    bl_description = "Add a Decimate modifier to reduce polygon count for BIM use"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        if not objs:
            self.report({"WARNING"}, "No geometry to optimise")
            return {"CANCELLED"}

        current = w.get("face_count_current", 0)
        if current == 0:
            current = meta_utils.count_faces(w["imported_object_names"])

        target = _get_bim_face_target()

        if current <= target:
            self.report({"INFO"}, f"Already at {current:,} faces — no optimisation needed")
            return {"FINISHED"}

        ratio = max(0.01, min(0.99, target / current))

        # Add Decimate modifier to each wizard object
        for obj in objs:
            # Remove any existing optimise modifier first
            for mod in list(obj.modifiers):
                if mod.name == "IFCLib_Decimate":
                    obj.modifiers.remove(mod)
            mod = obj.modifiers.new(name="IFCLib_Decimate", type="DECIMATE")
            mod.ratio = ratio

        w["decimate_preview_active"] = True
        _update_face_count()
        _redraw_panels()

        after = w["face_count_current"]
        self.report({"INFO"}, f"Preview: {current:,} → {after:,} faces (ratio {ratio:.2f})")
        return {"FINISHED"}


def _get_bim_face_target() -> int:
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.bim_face_target
    except Exception:
        pass
    return 4_000


class IFCLIB_OT_ConfirmOptimise(bpy.types.Operator):
    """Apply the Decimate modifier permanently to the mesh"""
    bl_idname = "ifclib.confirm_optimise"
    bl_label = "Confirm Optimise"
    bl_description = "Apply the decimate modifier permanently to the mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        bpy.ops.object.select_all(action="DESELECT")
        for obj in objs:
            if obj.type != "MESH":
                continue
            context.view_layer.objects.active = obj
            obj.select_set(True)
            # Apply just the IFCLib_Decimate modifier
            for mod in obj.modifiers:
                if mod.name == "IFCLib_Decimate":
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except Exception as e:
                        print(f"IFC Product Library: could not apply modifier: {e}")
                    break
            obj.select_set(False)

        w["decimate_preview_active"] = False
        _update_face_count()
        _redraw_panels()
        self.report({"INFO"}, f"Mesh optimised: {w['face_count_current']:,} faces")
        return {"FINISHED"}


class IFCLIB_OT_RevertOptimise(bpy.types.Operator):
    """Remove the Decimate modifier preview"""
    bl_idname = "ifclib.revert_optimise"
    bl_label = "Revert Optimise"
    bl_description = "Remove the Decimate modifier and restore the original mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        for obj in objs:
            for mod in list(obj.modifiers):
                if mod.name == "IFCLib_Decimate":
                    obj.modifiers.remove(mod)

        w["decimate_preview_active"] = False
        _update_face_count()
        _redraw_panels()
        self.report({"INFO"}, "Decimate modifier removed")
        return {"FINISHED"}


class IFCLIB_OT_SetOrigin(bpy.types.Operator):
    """Move the object origin to a standard insertion point"""
    bl_idname = "ifclib.set_origin"
    bl_label = "Set Origin"
    bl_description = "Move the origin to the selected reference point"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(
        name="Origin Mode",
        items=[
            ("BASE_CENTRE",    "Base Centre",    "Floor of bounding box, centred on X and Y"),
            ("BACK_CENTRE",    "Back Centre",    "Back face of bounding box, centred on X, at base Z"),
            ("GEOMETRIC",      "Geometric Centre","Object's geometric centre"),
        ],
        default="BASE_CENTRE",
    )

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        if not objs:
            self.report({"WARNING"}, "No geometry available")
            return {"CANCELLED"}

        # Work with the first (or only) object
        # If multiple objects, merge first then set origin
        if len(objs) > 1:
            self.report({"WARNING"}, "Merge objects first before setting origin")
            return {"CANCELLED"}

        obj = objs[0]
        context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)

        if self.mode == "GEOMETRIC":
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")

        elif self.mode == "BASE_CENTRE":
            _set_origin_to_base_centre(context, obj)

        elif self.mode == "BACK_CENTRE":
            _set_origin_to_back_centre(context, obj)

        _redraw_panels()
        self.report({"INFO"}, f"Origin set to {self.mode.replace('_', ' ').title()}")
        return {"FINISHED"}


def _set_origin_to_base_centre(context, obj):
    """Set origin to the centre of the bottom face of the bounding box."""
    import mathutils
    mesh = obj.data
    mat = obj.matrix_world

    min_z = min((mat @ v.co).z for v in mesh.vertices)
    sum_x = sum((mat @ v.co).x for v in mesh.vertices)
    sum_y = sum((mat @ v.co).y for v in mesh.vertices)
    n = len(mesh.vertices)

    new_origin = mathutils.Vector((sum_x / n, sum_y / n, min_z))
    _move_origin_to(context, obj, new_origin)


def _set_origin_to_back_centre(context, obj):
    """Set origin to the back-centre of the bounding box at base height."""
    import mathutils
    mesh = obj.data
    mat = obj.matrix_world

    world_verts = [mat @ v.co for v in mesh.vertices]
    min_z = min(v.z for v in world_verts)
    max_y = max(v.y for v in world_verts)
    sum_x = sum(v.x for v in world_verts)
    n = len(world_verts)

    new_origin = mathutils.Vector((sum_x / n, max_y, min_z))
    _move_origin_to(context, obj, new_origin)


def _move_origin_to(context, obj, world_pos):
    """Translate object origin to world_pos without moving the mesh visually."""
    # Move 3D cursor to desired origin position
    old_cursor = context.scene.cursor.location.copy()
    context.scene.cursor.location = world_pos

    # Set origin to cursor
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    # Restore cursor
    context.scene.cursor.location = old_cursor


# ---------------------------------------------------------------------------
# Step 3 — IFC classification update operator
# ---------------------------------------------------------------------------

class IFCLIB_OT_WizardSetCategory(bpy.types.Operator):
    """Update IFC class and predefined type when category changes"""
    bl_idname = "ifclib.wizard_set_category"
    bl_label = "Set Category"
    bl_description = "Set the product category and auto-fill IFC class"

    category_path: StringProperty(name="Category Path")

    def execute(self, context):
        w = wizard_state.get_wizard()
        w["category_path"] = self.category_path
        w["ifc_class"] = templates.get_ifc_class(self.category_path)
        w["predefined_type"] = templates.get_predefined_type(self.category_path)
        # Clear any previously pre-filled metadata so it gets re-generated on step 4
        w["metadata"] = {}
        _redraw_panels()
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Scale correction operator
# ---------------------------------------------------------------------------

class IFCLIB_OT_ScaleToMetres(bpy.types.Operator):
    """Scale all wizard objects by 0.001 to convert millimetres to metres"""
    bl_idname = "ifclib.scale_to_metres"
    bl_label = "Scale ×0.001 (mm → m)"
    bl_description = (
        "The imported geometry appears to be in millimetres. "
        "Scale by 0.001 to convert to Blender's metre units."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        objs = _get_wizard_objects()

        if not objs:
            self.report({"WARNING"}, "No wizard objects to scale")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        for obj in objs:
            obj.select_set(True)
        context.view_layer.objects.active = objs[0]

        # Scale in object mode
        bpy.ops.transform.resize(value=(0.001, 0.001, 0.001))
        bpy.ops.object.transform_apply(scale=True)

        _update_face_count()
        _redraw_panels()
        self.report({"INFO"}, f"Scaled {len(objs)} object(s) by 0.001 (mm → m)")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    IFCLIB_OT_StartWizard,
    IFCLIB_OT_CancelWizard,
    IFCLIB_OT_WizardNext,
    IFCLIB_OT_WizardBack,
    IFCLIB_OT_WizardImportFile,
    IFCLIB_OT_WizardUseSelected,
    IFCLIB_OT_RemoveSmallParts,
    IFCLIB_OT_MergeObjects,
    IFCLIB_OT_ConvertToMesh,
    IFCLIB_OT_OptimiseForBIM,
    IFCLIB_OT_ConfirmOptimise,
    IFCLIB_OT_RevertOptimise,
    IFCLIB_OT_SetOrigin,
    IFCLIB_OT_WizardSetCategory,
    IFCLIB_OT_ScaleToMetres,
)
