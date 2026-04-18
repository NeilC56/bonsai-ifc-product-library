"""
IFC Product Library — Import Wizard Panel Draw Helpers

These functions are called from library_browser.IFC_PT_ProductLibrary.draw()
when the wizard is active. No separate panel class is needed — the wizard
replaces the browse UI within the same sidebar panel.

Public entry point: draw_wizard(layout, context)
"""

import bpy
import os
from ..core import wizard_state, format_detect, metadata as meta_utils, templates


def _redraw_panels():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def draw_wizard(layout, context):
    """Draw the appropriate wizard step in `layout`."""
    w = wizard_state.get_wizard()
    step = w["step"]

    # Header with step indicator and cancel button
    _draw_wizard_header(layout, w)
    layout.separator(factor=0.5)

    try:
        if step == 1:
            _draw_step1(layout, context, w)
        elif step == 2:
            _draw_step2(layout, context, w)
        elif step == 3:
            _draw_step3(layout, context, w)
        elif step == 4:
            _draw_step4(layout, context, w)
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        print(f"IFC Product Library: wizard draw error (step {step}):\n{tb}")
        box = layout.box()
        box.alert = True
        box.label(text=f"Panel error (step {step}) — check console", icon="ERROR")
        for line in str(exc).splitlines()[:4]:
            box.label(text=line)
        # Always ensure user can navigate away
        layout.separator()
        layout.operator("ifclib.cancel_wizard", text="Cancel Wizard", icon="X")


# ---------------------------------------------------------------------------
# Shared header
# ---------------------------------------------------------------------------

def _draw_wizard_header(layout, w):
    step = w["step"]
    batch_label = wizard_state.get_batch_label()

    header = layout.row(align=True)
    header.scale_y = 0.9

    # Step title
    titles = {
        1: "Step 1 / 4 — Select Source",
        2: "Step 2 / 4 — Clean Up Geometry",
        3: "Step 3 / 4 — IFC Classification",
        4: "Step 4 / 4 — Product Information",
    }
    title = titles.get(step, "Import New Product")
    if batch_label:
        title = f"{title}  ({batch_label})"

    col = header.column()
    col.label(text="IMPORT NEW PRODUCT", icon="IMPORT")
    col.label(text=title)

    # Cancel button (top-right)
    header.operator("ifclib.cancel_wizard", text="", icon="X")


# ---------------------------------------------------------------------------
# Step 1 — Select geometry source
# ---------------------------------------------------------------------------

def _draw_step1(layout, context, w):
    box = layout.box()
    box.label(text="Geometry Source", icon="MESH_DATA")

    # ── Option A: Import from file ───────────────────────────────────────
    row = box.row()
    row.label(text="Import from file", icon="FILE_FOLDER")
    box.operator("ifclib.wizard_import_file", text="Browse & Import…", icon="FILEBROWSER")

    # Show detected format and any warnings
    if w.get("file_path"):
        fp = w["file_path"]
        fmt = w.get("format", "")
        name = os.path.basename(fp)

        sub = box.column(align=True)
        sub.scale_y = 0.85
        sub.label(text=f"File: {name}", icon="CHECKMARK")

        if fmt == "STEP":
            # Show Mayo guidance
            _draw_step_guidance(box)
        elif fmt == "IFC":
            box.label(text="IFC file detected — skips to Step 4", icon="INFO")
        elif fmt:
            box.label(text=f"Format: {fmt}", icon="CHECKMARK")
            if w.get("imported_object_names"):
                count = len(w["imported_object_names"])
                fc = w.get("face_count_current", 0)
                box.label(text=f"Imported: {count} object(s), {fc:,} faces")
        else:
            # File selected but not yet imported (format unknown)
            info = format_detect.detect(fp)
            if not info["known"]:
                box.label(text="Unsupported format", icon="ERROR")

    layout.separator(factor=0.3)

    # ── Option B: Use selected Blender objects ───────────────────────────
    row2 = layout.box()
    row2.label(text="Use selected object(s)", icon="OBJECT_DATA")
    sel_meshes = [o for o in context.selected_objects if o.type == "MESH"]
    if sel_meshes:
        row2.label(text=f"{len(sel_meshes)} mesh object(s) selected")
    else:
        sub = row2.row()
        sub.enabled = False
        sub.label(text="Select objects in viewport first")
    op_row = row2.row()
    op_row.enabled = bool(sel_meshes)
    op_row.operator("ifclib.wizard_use_selected", text="Use Selected", icon="CHECKMARK")

    if w.get("source_mode") == "selected" and w.get("imported_object_names"):
        row2.label(text=f"Ready: {len(w['imported_object_names'])} object(s)", icon="CHECKMARK")

    layout.separator()
    _draw_nav_buttons(layout, w, show_back=False)


def _draw_step_guidance(layout):
    """Show Mayo conversion guidance for STEP files."""
    box = layout.box()
    box.alert = True
    col = box.column(align=True)
    col.scale_y = 0.85
    col.label(text="STEP files need conversion first", icon="ERROR")
    col.separator(factor=0.3)
    col.label(text="Recommended route:")
    col.label(text="1. Open in Mayo (free, open-source)")
    col.label(text="2. Export as glTF (.glb)")
    col.label(text="3. Re-import the .glb file here")
    col.separator(factor=0.3)
    col.label(text="Alternative: FreeCAD → export as OBJ")

    # If Mayo path is configured, offer a launch button
    mayo_path = _get_mayo_path()
    if mayo_path and os.path.isfile(mayo_path):
        box.operator("wm.path_open", text="Open Mayo", icon="EXPORT").filepath = mayo_path
    else:
        col.separator(factor=0.3)
        col.label(text="Set Mayo path in Addon Preferences")


def _get_mayo_path() -> str:
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.mayo_path
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Step 2 — Geometry cleanup
# ---------------------------------------------------------------------------

def _draw_step2(layout, context, w):
    # ── Unit scale banner (shown first if model is suspiciously large) ───
    _draw_scale_warning(layout, w)

    # ── Face count traffic light ─────────────────────────────────────────
    try:
        _draw_face_count(layout, w)
    except Exception as exc:
        layout.label(text=f"Face count error: {exc}", icon="ERROR")
    layout.separator(factor=0.3)

    # ── Optimise for BIM / preview confirmation ──────────────────────────
    try:
        if not w.get("decimate_preview_active"):
            status, _ = meta_utils.face_count_label(w.get("face_count_current", 0))
            if status in ("amber", "red", "blocked"):
                layout.operator(
                    "ifclib.optimise_for_bim",
                    text="Optimise for BIM",
                    icon="MODIFIER",
                )
        else:
            raw = w.get("face_count_raw", 0)
            cur = w.get("face_count_current", 0)
            box = layout.box()
            box.label(text=f"Preview: {raw:,} \u2192 {cur:,} faces", icon="MODIFIER")
            brow = box.row(align=True)
            brow.operator("ifclib.confirm_optimise", text="Apply",  icon="CHECKMARK")
            brow.operator("ifclib.revert_optimise",  text="Revert", icon="X")
    except Exception as exc:
        layout.label(text=f"Optimise error: {exc}", icon="ERROR")

    layout.separator(factor=0.3)

    # ── Advanced cleanup options (collapsible) ───────────────────────────
    try:
        adv = layout.box()
        adv_row = adv.row()
        icon = "TRIA_DOWN" if w.get("advanced_expanded") else "TRIA_RIGHT"
        adv_row.operator(
            "ifclib.toggle_advanced_cleanup",
            text="Advanced Cleanup Options",
            icon=icon,
            emboss=False,
        )
        if w.get("advanced_expanded"):
            _draw_advanced_cleanup(adv, w)
    except Exception as exc:
        layout.label(text=f"Cleanup options error: {exc}", icon="ERROR")

    # ── Nav buttons — ALWAYS drawn ───────────────────────────────────────
    layout.separator()
    _draw_nav_buttons(layout, w)


def _draw_face_count(layout, w):
    """Draw the traffic-light face count indicator. Uses only stable icons."""
    count = w.get("face_count_current", 0)
    status, msg = meta_utils.face_count_label(count)

    box = layout.box()
    col = box.column(align=True)

    # Traffic light: use alert colouring + stable icon labels instead of
    # SEQUENCE_COLOR icons which may not exist in all Blender builds.
    if status == "green":
        row = col.row()
        row.label(text=f"  {count:,} faces", icon="CHECKMARK")
        row.label(text=msg)
    elif status == "amber":
        col.alert = False
        row = col.row()
        row.label(text=f"  {count:,} faces", icon="INFO")
        row.label(text=msg)
    else:  # red or blocked
        col.alert = True
        row = col.row()
        row.label(text=f"  {count:,} faces", icon="ERROR")
        row.label(text=msg)

    if status == "blocked":
        max_fc = _get_max_face_count_for_display()
        box.label(text=f"Maximum allowed: {max_fc:,}", icon="ERROR")


def _draw_scale_warning(layout, w):
    """Show a 'Scale mm → m' banner when the imported geometry looks like it's in mm."""
    names = w.get("imported_object_names", [])
    if not names:
        return

    try:
        import bpy
        max_dim = 0.0
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj is not None and obj.type == "MESH":
                dims = obj.dimensions  # world-space, in metres
                max_dim = max(max_dim, dims.x, dims.y, dims.z)

        # If the largest dimension exceeds 10 m, the geometry is probably in mm
        if max_dim < 10.0:
            return

        banner = layout.box()
        banner.alert = True
        col = banner.column(align=True)
        col.scale_y = 0.85
        col.label(
            text=f"Object is {max_dim:.0f} m — probably in mm units",
            icon="ERROR",
        )
        col.label(text="OBJ/STL from CAD tools often exports in mm.")
        banner.operator(
            "ifclib.scale_to_metres",
            text="Scale \u00d70.001  (mm \u2192 m)",
            icon="MODIFIER",
        )
        layout.separator(factor=0.3)
    except Exception:
        pass


def _get_max_face_count_for_display() -> int:
    try:
        from .. import _ADDON_ID
        prefs = bpy.context.preferences.addons.get(_ADDON_ID)
        if prefs:
            return prefs.preferences.max_face_count
    except Exception:
        pass
    return 50_000


def _draw_advanced_cleanup(layout, w):
    col = layout.column(align=True)
    col.scale_y = 0.9

    col.label(text="Remove Small Parts:", icon="TRASH")
    col.operator("ifclib.remove_small_parts", text="Remove Small Parts", icon="TRASH")

    col.separator(factor=0.5)
    col.label(text="Merge Objects:", icon="MESH_DATA")
    obj_count = len(w.get("imported_object_names", []))
    if obj_count > 1:
        col.operator("ifclib.merge_objects",
                     text=f"Merge {obj_count} Objects", icon="MESH_DATA")
    else:
        sub = col.row()
        sub.enabled = False
        sub.label(text="Single object — no merge needed")

    col.separator(factor=0.5)
    col.label(text="Convert to Mesh:", icon="MESH_DATA")
    col.operator("ifclib.convert_to_mesh",
                 text="Apply Modifiers / Convert", icon="MESH_DATA")

    col.separator(factor=0.5)
    col.label(text="Set Origin:", icon="OBJECT_DATA")
    origin_row = col.row(align=True)
    op = origin_row.operator("ifclib.set_origin", text="Base")
    op.mode = "BASE_CENTRE"
    op = origin_row.operator("ifclib.set_origin", text="Back")
    op.mode = "BACK_CENTRE"
    op = origin_row.operator("ifclib.set_origin", text="Centre")
    op.mode = "GEOMETRIC"


# ---------------------------------------------------------------------------
# Step 3 — IFC Classification
# ---------------------------------------------------------------------------

def _draw_step3(layout, context, w):
    box = layout.box()
    box.label(text="Select Category", icon="BOOKMARKS")

    tree = templates.get_category_tree()
    _draw_category_tree(box, tree, w, depth=0)

    if w.get("category_path"):
        layout.separator(factor=0.3)
        info = layout.box()
        info.label(text="Auto-filled from category template:", icon="INFO")
        col = info.column(align=True)
        col.scale_y = 0.85
        col.label(text=f"IFC Class:  {w.get('ifc_class', '—')}")
        col.label(text=f"Type:        {w.get('predefined_type', '—')}")

    layout.separator()
    _draw_nav_buttons(layout, w)


def _draw_category_tree(layout, cats, w, depth):
    for cat in cats:
        path = cat["path"]
        label = cat["label"]
        subs = cat.get("subcategories", [])

        if subs:
            # Parent category — draw as expander
            row = layout.row(align=True)
            row.label(text="  " * depth + label, icon="TRIA_RIGHT")
            _draw_category_tree(layout, subs, w, depth + 1)
        else:
            # Leaf category — draw as selectable button
            is_selected = (w.get("category_path") == path)
            row = layout.row(align=True)
            op = row.operator(
                "ifclib.wizard_set_category",
                text="  " * depth + ("▸ " if is_selected else "  ") + label,
                icon="LAYER_ACTIVE" if is_selected else "LAYER_USED",
                emboss=is_selected,
            )
            op.category_path = path


# ---------------------------------------------------------------------------
# Step 4 — IFC source: category picker
# ---------------------------------------------------------------------------

def _draw_ifc_category_picker(layout, w, meta):
    """Compact category picker shown at the top of Step 4 for IFC-source products.

    Steps 2 and 3 were skipped, so the user must assign a library category
    here.  Uses the same IFCLIB_OT_WizardSetCategory operator as Step 3, but
    that operator now detects step == 4 and updates only the category fields
    in the existing metadata rather than clearing it.
    """
    category_path = meta.get("category", {}).get("path", "")
    box = layout.box()

    if not category_path:
        header = box.row()
        header.alert = True
        header.label(text="Category required — choose one to enable saving", icon="ERROR")
    else:
        header = box.row()
        cat_label = templates.category_path_label(category_path)
        header.label(text=f"Category: {cat_label}", icon="BOOKMARKS")
        sub = header.row()
        sub.scale_x = 0.7
        sub.label(text="(change below)")

    # IFC class auto-detected from file
    ifc_class = meta.get("ifc", {}).get("class", "")
    if ifc_class:
        info = box.column(align=True)
        info.scale_y = 0.8
        info.label(text=f"IFC class detected: {ifc_class}", icon="INFO")

    box.separator(factor=0.3)
    tree = templates.get_category_tree()
    _draw_category_tree(box, tree, w, depth=0)


# ---------------------------------------------------------------------------
# Step 4 — Product metadata form
# ---------------------------------------------------------------------------

def _draw_step4(layout, context, w):
    meta = w.get("metadata", {})
    if not meta:
        layout.label(text="Initialising…", icon="INFO")
        return

    # ── IFC-source: category picker ───────────────────────────────────────
    # Steps 2 and 3 were skipped for IFC files, so the user must choose a
    # category here before they can save.
    if w.get("format") == "IFC":
        _draw_ifc_category_picker(layout, w, meta)
        layout.separator(factor=0.5)

    # Show any previous save error
    if w.get("save_error"):
        err_box = layout.box()
        err_box.alert = True
        for line in w["save_error"].splitlines():
            err_box.label(text=line, icon="ERROR")
        w["save_error"] = ""  # Clear after displaying

    # ── Identity ──────────────────────────────────────────────────────
    _section_header(layout, "Identity", "INFO")
    id_box = layout.box()
    identity = meta.setdefault("identity", {})
    _text_field(id_box, identity, "name",          "Name *",       section="identity")
    _text_field(id_box, identity, "manufacturer",  "Manufacturer", section="identity")
    _text_field(id_box, identity, "model_number",  "Model No.",    section="identity")
    _text_field(id_box, identity, "product_url",   "URL",          section="identity")
    _text_field(id_box, identity, "description",   "Description",  section="identity")

    # ── Dimensions ────────────────────────────────────────────────────
    _section_header(layout, "Dimensions (mm)", "NONE")
    dim_box = layout.box()
    dims = meta.setdefault("dimensions", {})
    _float_field(dim_box, dims, "width_mm",  "Width",       "dim_width_mm")
    _float_field(dim_box, dims, "depth_mm",  "Depth",       "dim_depth_mm")
    _float_field(dim_box, dims, "height_mm", "Height",      "dim_height_mm")
    _float_field(dim_box, dims, "weight_kg", "Weight (kg)", "dim_weight_kg")

    # ── Category-specific properties ──────────────────────────────────
    category_path = meta.get("category", {}).get("path", "")
    prop_fields = templates.get_property_fields(category_path)
    if prop_fields:
        cat_label = templates.category_path_label(category_path)
        _section_header(layout, f"Properties — {cat_label}", "PROPERTIES")
        prop_box = layout.box()
        props = meta.setdefault("properties", {})
        for field in prop_fields:
            _property_field(prop_box, props, field)

    # ── Classification ────────────────────────────────────────────────
    _section_header(layout, "Classification", "BOOKMARKS")
    cls_box = layout.box()
    cls = meta.setdefault("classification", {})
    uniclass = cls.setdefault("uniclass_2015", {})
    _text_field(cls_box, uniclass, "code", "Uniclass 2015",
                section="classification/uniclass_2015")
    omniclass = cls.setdefault("omniclass", {})
    _text_field(cls_box, omniclass, "code", "OmniClass",
                section="classification/omniclass")

    # ── Compliance ────────────────────────────────────────────────────
    _section_header(layout, "Compliance", "NONE")
    comp_box = layout.box()
    comp = meta.setdefault("compliance", {})
    _bool_field(comp_box, comp, "doc_m", "Doc M Compliant", "comp_doc_m")
    _text_field(comp_box, comp, "standards_str", "Standards (comma-separated)",
                section="compliance")

    # ── Tags ──────────────────────────────────────────────────────────
    _section_header(layout, "Tags", "FILTER")
    tag_box = layout.box()
    cat_meta = meta.setdefault("category", {})
    _text_field(tag_box, cat_meta, "tags_str", "Tags (comma-separated)",
                section="category")

    # ── Provenance ────────────────────────────────────────────────────
    _section_header(layout, "Provenance", "TIME")
    prov_box = layout.box()
    prov = meta.setdefault("provenance", {})
    _text_field(prov_box, prov, "geometry_source", "Geometry Source",
                section="provenance")
    _text_field(prov_box, prov, "geometry_licence", "Licence",
                section="provenance")

    layout.separator()

    # ── Save buttons ──────────────────────────────────────────────────
    # Validate before enabling Save
    errors = meta_utils.validate_metadata(meta)
    max_fc = _get_max_face_count_for_display()
    current_faces = meta_utils.count_faces(w.get("imported_object_names", []))
    face_ok = current_faces <= max_fc

    save_row = layout.row(align=True)
    save_row.enabled = (not errors) and face_ok
    save_row.scale_y = 1.4
    save_row.operator("ifclib.save_to_library",  text="Save to Library",  icon="FILE")
    save_row.operator("ifclib.save_and_insert",  text="Save & Insert",   icon="IMPORT")

    if errors:
        for err in errors:
            layout.label(text=f"  ✗ {err}", icon="ERROR")

    if not face_ok:
        layout.label(
            text=f"Face count {current_faces:,} exceeds max {max_fc:,}",
            icon="ERROR",
        )

    layout.separator(factor=0.5)
    layout.operator("ifclib.wizard_back", text="← Back", icon="BACK")


# ---------------------------------------------------------------------------
# Metadata form helpers
# ---------------------------------------------------------------------------

def _section_header(layout, title: str, icon: str = "NONE"):
    row = layout.row()
    row.scale_y = 0.7
    row.label(text=f"── {title} ──", icon=icon)


def _text_field(layout, d: dict, key: str, label: str, section: str = "identity"):
    """Draw a clickable text button that opens an edit dialog.

    Reads the current value directly from d[key] — no scene property writes.
    The operator receives field_section so it can write back to the correct
    sub-dict of wizard_state["metadata"] without needing any scene-level storage.
    """
    current_val = str(d.get(key, ""))
    row = layout.row()
    row.label(text=label + ":", icon="NONE")
    op = row.operator(
        "ifclib.edit_text_field",
        text=current_val if current_val else f"(enter {label.lower()})",
        icon="NONE",
    )
    op.field_key = key
    op.field_section = section


def _float_field(layout, d: dict, key: str, label: str, pg_attr: str):
    """Draw a float input backed by IFCLibMetaFormProps.

    row.prop() reads/writes the PropertyGroup value — no ID-class writes.
    The sync line (d[key] = ...) writes to a plain Python dict, which is
    permitted inside draw functions.
    """
    pg = bpy.context.scene.ifclib_meta_form
    row = layout.row()
    row.label(text=label + ":")
    if hasattr(pg, pg_attr):
        row.prop(pg, pg_attr, text="")
        d[key] = getattr(pg, pg_attr)          # Python dict write — OK in draw
    else:
        row.label(text=str(round(float(d.get(key, 0.0)), 2)))


def _bool_field(layout, d: dict, key: str, label: str, pg_attr: str):
    """Draw a bool checkbox backed by IFCLibMetaFormProps."""
    pg = bpy.context.scene.ifclib_meta_form
    row = layout.row()
    row.label(text=label + ":")
    if hasattr(pg, pg_attr):
        row.prop(pg, pg_attr, text="")
        d[key] = getattr(pg, pg_attr)          # Python dict write — OK in draw
    else:
        row.label(text="Yes" if d.get(key) else "No")


def _property_field(layout, props: dict, field: dict):
    key = field["key"]
    label = field["label"]
    ftype = field.get("type", "str")
    unit = field.get("unit", "")
    label_text = f"{label}" + (f" ({unit})" if unit else "")
    pg_attr = f"tp_{key}"       # matches IFCLibMetaFormProps naming convention

    if ftype == "bool":
        _bool_field(layout, props, key, label_text, pg_attr)
    elif ftype in ("int", "float"):
        _float_field(layout, props, key, label_text, pg_attr)
    elif ftype == "enum":
        options = field.get("options", [])
        _enum_field(layout, props, key, label_text, options)
    else:
        _text_field(layout, props, key, label_text, section="properties")


def _enum_field(layout, d: dict, key: str, label: str, options: list):
    """Draw an enum as a row of small buttons."""
    row = layout.row()
    row.label(text=label)
    current = d.get(key, options[0] if options else "")
    sub = row.row(align=True)
    sub.scale_x = 0.7
    for opt in options[:5]:  # cap at 5 to avoid overflow
        is_active = (current == opt)
        op = sub.operator(
            "ifclib.set_enum_field",
            text=opt,
            depress=is_active,
        )
        op.field_key = key
        op.field_value = opt


# ---------------------------------------------------------------------------
# Navigation buttons (shared by steps 2, 3, 4)
# ---------------------------------------------------------------------------

def _draw_nav_buttons(layout, w, show_back=True):
    row = layout.row(align=True)
    row.scale_y = 1.2
    if show_back and w["step"] > 1:
        row.operator("ifclib.wizard_back", text="← Back", icon="BACK")
    if w["step"] < 4:
        row.operator("ifclib.wizard_next", text="Next →", icon="FORWARD")


# ---------------------------------------------------------------------------
# Inline edit operators used by the metadata form
# ---------------------------------------------------------------------------

class IFCLIB_OT_EditTextField(bpy.types.Operator):
    """Edit a wizard metadata text field"""
    bl_idname = "ifclib.edit_text_field"
    bl_label = "Edit Field"
    bl_description = "Click to edit this text field"
    bl_options = {"REGISTER", "UNDO"}

    field_key:     bpy.props.StringProperty(name="Field Key",     options={"HIDDEN"})
    field_section: bpy.props.StringProperty(name="Field Section", options={"HIDDEN"},
                                             default="identity")
    value:         bpy.props.StringProperty(name="Value")

    def invoke(self, context, event):
        # Pre-fill from wizard_state — no scene property reads
        w = wizard_state.get_wizard()
        meta = w.get("metadata", {})
        d = _navigate_section(meta, self.field_section)
        self.value = str(d.get(self.field_key, ""))
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(self, "value", text="")

    def execute(self, context):
        w = wizard_state.get_wizard()
        meta = w.get("metadata", {})
        d = _navigate_section(meta, self.field_section)
        d[self.field_key] = self.value

        # Special post-processing for comma-separated list fields
        if self.field_key == "tags_str":
            d["tags"] = [t.strip() for t in self.value.split(",") if t.strip()]
        elif self.field_key == "standards_str":
            d["standards"] = [s.strip() for s in self.value.split(",") if s.strip()]

        _redraw_panels()
        return {"FINISHED"}


class IFCLIB_OT_SetEnumField(bpy.types.Operator):
    """Set an enum value in the wizard metadata"""
    bl_idname = "ifclib.set_enum_field"
    bl_label = "Set Value"
    bl_options = {"REGISTER", "UNDO"}

    field_key: bpy.props.StringProperty(name="Field Key", options={"HIDDEN"})
    field_value: bpy.props.StringProperty(name="Value", options={"HIDDEN"})

    def execute(self, context):
        w = wizard_state.get_wizard()
        meta = w.get("metadata", {})
        props = meta.setdefault("properties", {})
        props[self.field_key] = self.field_value
        pass  # _redraw_panels is defined at module level above
        _redraw_panels()
        return {"FINISHED"}


class IFCLIB_OT_ToggleAdvancedCleanup(bpy.types.Operator):
    """Toggle the advanced cleanup options section"""
    bl_idname = "ifclib.toggle_advanced_cleanup"
    bl_label = "Toggle Advanced Cleanup"
    bl_options = {"REGISTER"}

    def execute(self, context):
        w = wizard_state.get_wizard()
        w["advanced_expanded"] = not w.get("advanced_expanded", False)
        pass  # _redraw_panels is defined at module level above
        _redraw_panels()
        return {"FINISHED"}


def _navigate_section(meta: dict, section: str) -> dict:
    """Navigate a '/'-delimited section path in meta, creating dicts as needed.

    Examples:
        "identity"                       → meta["identity"]
        "classification/uniclass_2015"   → meta["classification"]["uniclass_2015"]
        "properties"                     → meta["properties"]
    """
    d = meta
    for part in section.split("/"):
        if part:
            d = d.setdefault(part, {})
    return d


# ---------------------------------------------------------------------------
# Panel classes to register (no standalone panel — these are helper operators)
# ---------------------------------------------------------------------------

classes = (
    IFCLIB_OT_EditTextField,
    IFCLIB_OT_SetEnumField,
    IFCLIB_OT_ToggleAdvancedCleanup,
)
