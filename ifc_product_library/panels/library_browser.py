"""Main sidebar panel — the Product Library N-panel tab in the 3D Viewport."""

import bpy
from ..core import library_index, wizard_state, span_tables
from ..operators.array_insert_ops import _is_beam_product
from .. import _ADDON_ID   # full package name, safe for both dev and installed extension


# ---------------------------------------------------------------------------
# Shared panel redraw helper (imported by import_wizard.py too)
# ---------------------------------------------------------------------------

def _redraw_panels():
    """Tag all VIEW_3D areas for redraw."""
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_category_node(
    layout: bpy.types.UILayout,
    cat: dict,
    depth: int,
    state: dict,
    index: dict,
) -> None:
    """Recursively draw one node (and its children) of the category tree."""
    path = cat["path"]
    label = cat["label"]
    subcats = cat.get("subcategories", [])

    count = library_index.count_products_in_tree(path, subcats)
    if count == 0:
        return  # Don't clutter the tree with empty branches

    is_expanded = path in state["expanded_categories"]
    is_selected = state["selected_category"] == path

    row = layout.row(align=True)

    # Indentation: one icon-width per depth level
    for _ in range(depth):
        row.label(text="", icon="BLANK1")

    if subcats:
        # Parent category — click toggles expand/collapse
        icon = "TRIA_DOWN" if is_expanded else "TRIA_RIGHT"
        op = row.operator(
            "ifclib.browse_category",
            text=f"{label} ({count})",
            icon=icon,
            emboss=is_selected,
        )
        op.category_path = path
        op.has_subcategories = True
    else:
        # Leaf category — click selects and shows products
        icon = "LAYER_ACTIVE" if is_selected else "LAYER_USED"
        op = row.operator(
            "ifclib.browse_category",
            text=f"{label} ({count})",
            icon=icon,
            emboss=is_selected,
        )
        op.category_path = path
        op.has_subcategories = False

    # Recurse into children if expanded
    if is_expanded:
        for subcat in subcats:
            _draw_category_node(layout, subcat, depth + 1, state, index)


def _draw_product_row(
    layout: bpy.types.UILayout,
    slug: str,
    product: dict,
    state: dict,
) -> None:
    """Draw a single selectable product row."""
    identity = product.get("identity", {})
    name = identity.get("name", slug)
    manufacturer = identity.get("manufacturer", "")
    is_selected = state["selected_product_slug"] == slug

    col = layout.column(align=True)
    op = col.operator(
        "ifclib.select_product",
        text=name,
        icon="OBJECT_DATA",
        emboss=is_selected,
    )
    op.product_slug = slug

    if manufacturer and not is_selected:
        # Show manufacturer in a subdued line when not selected
        sub = col.row()
        sub.scale_y = 0.6
        sub.label(text=f"    {manufacturer}")


def _draw_product_detail(layout: bpy.types.UILayout, product: dict) -> None:
    """Draw the detail box for the selected product."""
    identity      = product.get("identity", {})
    dims          = product.get("dimensions", {})
    ifc_data      = product.get("ifc", {})
    classification = product.get("classification", {})
    category      = product.get("category", {})
    props         = product.get("properties", {})

    box = layout.box()
    col = box.column(align=True)

    # ── Identity ───────────────────────────────────────────────────────────
    col.label(text=identity.get("name", ""), icon="OBJECT_DATA")
    if identity.get("manufacturer"):
        col.label(text=identity["manufacturer"])
    if identity.get("model_number"):
        col.label(text=f"Ref: {identity['model_number']}")

    # ── Dimensions ─────────────────────────────────────────────────────────
    w = dims.get("width_mm")
    d = dims.get("depth_mm")
    h = dims.get("height_mm")
    if w is not None and d is not None and h is not None:
        col.separator(factor=0.5)
        col.label(text=f"{w} × {d} × {h} mm", icon="DRIVER_DISTANCE")
    if dims.get("weight_kg") is not None:
        col.label(text=f"{dims['weight_kg']} kg")

    # ── IFC class ──────────────────────────────────────────────────────────
    ifc_class  = ifc_data.get("class", "")
    predefined = ifc_data.get("predefined_type", "")
    ifc_ver    = ifc_data.get("ifc_version", "")
    if ifc_class:
        col.separator(factor=0.5)
        col.label(text=f"IFC: {ifc_class}", icon="FILE_SCRIPT")
        if predefined and predefined not in ("NOTDEFINED", ""):
            col.label(text=f"     {predefined}")
        if ifc_ver:
            col.label(text=f"     ({ifc_ver})")

    # ── Uniclass ───────────────────────────────────────────────────────────
    uniclass = classification.get("uniclass_2015", {})
    if uniclass.get("code"):
        col.separator(factor=0.5)
        col.label(text=f"Uniclass: {uniclass['code']}", icon="BOOKMARKS")
        if uniclass.get("description"):
            col.label(text=f"          {uniclass['description']}")

    # ── Tags ───────────────────────────────────────────────────────────────
    tags = category.get("tags", [])
    if tags:
        col.separator(factor=0.5)
        col.label(text="Tags: " + ", ".join(tags), icon="FILTER")

    # ── Key properties ─────────────────────────────────────────────────────
    material = props.get("material", "")
    mounting = props.get("mounting", "")
    if material or mounting:
        col.separator(factor=0.5)
        if material:
            col.label(text=f"Material: {material}")
        if mounting:
            col.label(text=f"Mounting: {mounting}")

    # ── Compliance ─────────────────────────────────────────────────────────
    if product.get("compliance", {}).get("doc_m"):
        col.separator(factor=0.5)
        col.label(text="Doc M compliant", icon="KEYTYPE_KEYFRAME_VEC")


# ---------------------------------------------------------------------------
# Array Insert UI helpers
# ---------------------------------------------------------------------------

def _draw_span_advisory(col, context, pg):
    """Draw the collapsible Span Advisory section.

    The three disclaimer blocks (warning, source, limitations) are always
    visible whenever the advisory section is expanded.  They are NOT
    collapsible and must not be hidden.
    """
    col.separator(factor=0.5)

    # Collapsible header
    header_row = col.row(align=True)
    adv_icon   = "TRIA_DOWN" if pg.show_span_advisory else "TRIA_RIGHT"
    header_row.prop(pg, "show_span_advisory", text="Span Advisory", icon=adv_icon, emboss=False)

    if not pg.show_span_advisory:
        return

    lib_path         = library_index.get_index().get("library_path", "")
    available_tables = span_tables.list_span_tables(lib_path)

    adv_box = col.box()
    adv_col = adv_box.column(align=True)

    # ── Disclaimer 1 (always visible) ─────────────────────────────────────
    adv_col.label(text="Advisory only — verify with structural engineer", icon="ERROR")
    adv_col.separator(factor=0.3)

    # ── Span table selector ────────────────────────────────────────────────
    if not available_tables:
        adv_col.label(text="No span tables found in library", icon="INFO")
        adv_col.label(
            text=f"Expected: {span_tables.get_span_tables_dir(lib_path)}",
        )
        # Still show limitations even when no tables are present
        _draw_advisory_limitations(adv_col)
        return

    adv_col.label(text="Span Table:")
    tbl_row = adv_col.row(align=True)
    for tbl_info in available_tables:
        fname     = tbl_info["filename"]
        is_active = pg.active_span_table == fname
        label     = tbl_info.get("system") or fname
        op        = tbl_row.operator(
            "ifclib.set_span_table",
            text=label,
            depress=is_active,
        )
        op.filename = fname

    # ── Load case selector ─────────────────────────────────────────────────
    tbl = None
    if pg.active_span_table:
        tbl = span_tables.load_span_table(lib_path, pg.active_span_table)

    if tbl is None:
        adv_col.separator(factor=0.3)
        adv_col.label(text="Select a span table above", icon="INFO")
        _draw_advisory_limitations(adv_col)
        return

    adv_col.separator(factor=0.3)
    adv_col.prop(pg, "load_case", text="Load Case")

    # ── Results ────────────────────────────────────────────────────────────
    span_mm    = int(pg.span_length_mm)
    spacing_mm = int(pg.spacing_mm)
    results    = span_tables.query_span_table(
        tbl, span_mm, pg.load_case, spacing_mm
    )

    if results:
        adv_col.separator(factor=0.3)
        adv_col.label(text=f"Span: {span_mm}mm  |  Spacing: {spacing_mm}mm ctrs")

        # Table header
        hdr = adv_col.row()
        hdr.scale_y = 0.75
        hdr.label(text="Section")
        hdr.label(text="Max span")
        hdr.label(text="Status")

        for entry in results:
            row = adv_col.row()
            status = entry["status"]
            if status == "Short":
                row.alert = True
            row.label(text=f"{entry['depth_mm']}mm  {entry['top_chord']}")
            row.label(text=f"{entry['max_span_mm']}mm")
            row.label(text=status)

    # ── Disclaimer 2 — source reference (always visible) ──────────────────
    adv_col.separator(factor=0.5)
    mfr = tbl.get("manufacturer", "")
    sys = tbl.get("system", "")
    adv_col.label(text=f"Source: {mfr} {sys}".strip(), icon="INFO")

    # ── Disclaimer 3 — limitations (always visible) ────────────────────────
    _draw_advisory_limitations(adv_col)


def _draw_advisory_limitations(col):
    """Draw the always-visible advisory limitations text."""
    col.separator(factor=0.3)
    col.label(text="Actual capacity depends on loading,")
    col.label(text="support conditions, and penetrations.")
    col.label(text="Verify with manufacturer tables and")
    col.label(text="structural engineer's calculations.")


def _draw_array_insert(layout, context, product):
    """Draw the Array Insert UI section for beam/joist products.

    Only called when _is_beam_product() is True for the selected product.
    All mutable state is read via prop() (allowed in draw).  Preset buttons
    use small operators so writes happen in execute(), not draw().
    """
    pg = context.scene.ifclib_array_insert

    box = layout.box()
    col = box.column(align=True)
    col.label(text="Placement Mode", icon="MOD_ARRAY")

    # ── Mode radio ────────────────────────────────────────────────────────
    row = col.row(align=True)
    row.prop(pg, "placement_mode", expand=True)

    if pg.placement_mode != "ARRAY":
        return  # Single mode — nothing more to draw

    col.separator(factor=0.5)

    # ── Array direction ────────────────────────────────────────────────────
    row = col.row(align=True)
    row.label(text="Direction:")
    row.prop(pg, "array_direction", expand=True)

    col.separator(factor=0.4)

    # ── Beam length ────────────────────────────────────────────────────────
    col.prop(pg, "beam_length_mm")

    col.separator(factor=0.4)

    # ── Spacing + presets ──────────────────────────────────────────────────
    col.prop(pg, "spacing_mm")
    row = col.row(align=True)
    row.label(text="Preset:")
    for s in (400, 450, 600):
        op = row.operator("ifclib.set_spacing", text=f"{s}")
        op.spacing = s

    col.separator(factor=0.4)

    # ── Span length ────────────────────────────────────────────────────────
    col.prop(pg, "span_length_mm")

    col.separator(factor=0.4)

    # ── Wall offsets ───────────────────────────────────────────────────────
    sub = col.column(align=True)

    sub.prop(pg, "start_offset_mm")
    row = sub.row(align=True)
    row.label(text="  Presets:")
    op = row.operator("ifclib.set_wall_offset", text="Masonry 20mm")
    op.end = "start"; op.value_mm = 20
    op2 = row.operator("ifclib.set_wall_offset", text="Timber 10mm")
    op2.end = "start"; op2.value_mm = 10

    sub.separator(factor=0.3)

    sub.prop(pg, "end_offset_mm")
    row = sub.row(align=True)
    row.label(text="  Presets:")
    op = row.operator("ifclib.set_wall_offset", text="Masonry 20mm")
    op.end = "end"; op.value_mm = 20
    op2 = row.operator("ifclib.set_wall_offset", text="Timber 10mm")
    op2.end = "end"; op2.value_mm = 10

    col.separator(factor=0.4)

    # ── Odd spacing side ───────────────────────────────────────────────────
    col.prop(pg, "odd_at_start")

    # ── Live preview (pure reads — no ID writes) ───────────────────────────
    col.separator(factor=0.5)
    span_mm    = pg.span_length_mm
    spacing_mm = pg.spacing_mm
    start_mm   = pg.start_offset_mm
    end_mm     = pg.end_offset_mm

    usable_mm  = span_mm - start_mm - end_mm
    if usable_mm <= 0:
        warn = col.row()
        warn.alert = True
        warn.label(text="Offsets exceed span", icon="ERROR")
    else:
        n_spaces  = int(usable_mm / spacing_mm) if spacing_mm > 0 else 0
        n_joists  = n_spaces + 1
        odd_mm    = round(usable_mm - n_spaces * spacing_mm)
        odd_side  = "start" if pg.odd_at_start else "end"

        preview_box = col.box()
        pb = preview_box.column(align=True)
        pb.scale_y = 0.85
        pb.label(
            text=f"{n_joists} joists,  {n_spaces} spaces",
            icon="INFO",
        )
        if odd_mm > 1:
            pb.label(text=f"Odd gap: {odd_mm}mm at {odd_side}")
        else:
            pb.label(text="Even spacing")
        pb.label(
            text=f"Offsets: {int(start_mm)}mm start, {int(end_mm)}mm end"
        )
        pb.label(text=f"Total: {int(span_mm)}mm")

    # ── Span Advisory ─────────────────────────────────────────────────────
    _draw_span_advisory(col, context, pg)


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class IFC_PT_ProductLibrary(bpy.types.Panel):
    bl_label = "Product Library"
    bl_idname = "IFC_PT_ProductLibrary"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Product Library"

    def draw(self, context):
        layout = self.layout

        # ── Import Wizard takes over when active ──────────────────────────
        if wizard_state.get_wizard()["active"]:
            from .import_wizard import draw_wizard
            draw_wizard(layout, context)
            return

        index = library_index.get_index()

        # ── Draw-time lazy-load ────────────────────────────────────────────
        # Blender's DIR_PATH file-picker doesn't always fire the update
        # callback on the StringProperty.  As a fallback, whenever the panel
        # draws and the library isn't loaded we check whether a path is
        # configured and attempt to load if we haven't tried that path yet.
        if not index["loaded"]:
            try:
                addon_prefs = context.preferences.addons.get(_ADDON_ID)
                if addon_prefs:
                    pref_path = addon_prefs.preferences.library_path.strip()
                    last_tried = index.get("library_path", "")
                    if pref_path and pref_path != last_tried:
                        print(
                            f"IFC Product Library [panel draw]: pref path differs "
                            f"from last attempt — trying '{pref_path}'"
                        )
                        library_index.load_library(pref_path)
                        index = library_index.get_index()  # refresh reference
            except Exception as exc:
                print(f"IFC Product Library [panel draw]: lazy-load error: {exc}")

        # ══ Not loaded ════════════════════════════════════════════════════
        if not index["loaded"]:
            col = layout.column(align=True)
            if index["error"]:
                col.label(text="Library error:", icon="ERROR")
                for chunk in _wrap(index["error"], 34):
                    col.label(text=f"  {chunk}")
            else:
                col.label(text="Library not loaded.", icon="INFO")

            # Show what path was attempted so the user can diagnose easily
            tried = index.get("library_path", "")
            if tried:
                col.separator(factor=0.3)
                col.label(text="Tried path:", icon="FILE_FOLDER")
                for chunk in _wrap(tried, 34):
                    col.label(text=f"  {chunk}")
            else:
                col.separator(factor=0.3)
                col.label(text="No path attempted yet.", icon="INFO")

            col.separator(factor=0.5)
            col.operator("ifclib.refresh_library", text="Load Library", icon="FILE_REFRESH")
            col.operator(
                "screen.userpref_show",
                text="Set Library Path…",
                icon="PREFERENCES",
            ).section = "ADDONS"
            return

        # ══ Header ════════════════════════════════════════════════════════
        meta = index["library_meta"]
        row = layout.row(align=True)
        row.label(
            text=meta.get("name", "Product Library"),
            icon="ASSET_MANAGER",
        )
        row.operator("ifclib.refresh_library", text="", icon="FILE_REFRESH")

        product_count = len(index["products"])
        sub = layout.row()
        sub.scale_y = 0.7
        sub.label(
            text=f"{product_count} product{'s' if product_count != 1 else ''}"
        )

        layout.separator(factor=0.3)

        # ══ Search field ══════════════════════════════════════════════════
        layout.prop(
            context.scene.ifc_product_library,
            "search_query",
            text="",
            icon="VIEWZOOM",
        )

        state = library_index.get_ui_state()
        query = context.scene.ifc_product_library.search_query.strip()

        layout.separator(factor=0.3)

        if query:
            # ══ Search results ════════════════════════════════════════════
            results = library_index.search_products(query)
            if not results:
                layout.label(text="No results found", icon="INFO")
            else:
                sub = layout.row()
                sub.scale_y = 0.7
                sub.label(text=f"{len(results)} result{'s' if len(results) != 1 else ''}:")
                col = layout.column(align=True)
                for slug, product in results[:30]:  # cap display at 30
                    _draw_product_row(col, slug, product, state)

        else:
            # ══ Category tree ═════════════════════════════════════════════
            categories = index["library_meta"].get("categories", [])
            if not categories:
                layout.label(text="No categories found in library.json", icon="INFO")
            else:
                col = layout.column(align=True)
                for cat in categories:
                    _draw_category_node(col, cat, 0, state, index)

            # ══ Product list for the selected category ════════════════════
            selected_cat = state["selected_category"]
            if selected_cat:
                products = library_index.get_products_in_category(selected_cat)
                if products:
                    layout.separator(factor=0.3)
                    # Derive a readable label from the path
                    cat_label = selected_cat.split("/")[-1].replace("-", " ").title()
                    row = layout.row()
                    row.label(text=cat_label + ":", icon="FILE_FOLDER")
                    col = layout.column(align=True)
                    for slug, product in products:
                        _draw_product_row(col, slug, product, state)

        # ══ Product detail ════════════════════════════════════════════════
        selected_slug = state["selected_product_slug"]
        selected_product = None
        if selected_slug:
            selected_product = library_index.get_product(selected_slug)
            if selected_product:
                layout.separator(factor=0.5)
                _draw_product_detail(layout, selected_product)

                # ══ Array Insert UI (beam/joist products only) ════════════
                if _is_beam_product(selected_product):
                    layout.separator(factor=0.3)
                    _draw_array_insert(layout, context, selected_product)

        # ══ INSERT / INSERT ARRAY button ═════════════════════════════
        layout.separator(factor=0.5)
        row = layout.row()
        row.enabled = bool(selected_slug)
        row.scale_y = 1.6

        pg = context.scene.ifclib_array_insert
        if (
            selected_product
            and _is_beam_product(selected_product)
            and pg.placement_mode == "ARRAY"
        ):
            row.operator(
                "ifclib.insert_product_array",
                text="INSERT ARRAY",
                icon="MOD_ARRAY",
            )
        else:
            row.operator(
                "ifclib.insert_product",
                text="INSERT INTO MODEL",
                icon="IMPORT",
            )

        # ══ Add New Product button ════════════════════════════════════════
        layout.separator(factor=0.3)
        layout.operator(
            "ifclib.start_wizard",
            text="+ Add New Product",
            icon="ADD",
        )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int) -> list[str]:
    """Very simple word-wrap for error messages in the panel."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return lines or [text]
