"""Main sidebar panel — the Product Library N-panel tab in the 3D Viewport."""

import bpy
from ..core import library_index, wizard_state
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
        if selected_slug:
            product = library_index.get_product(selected_slug)
            if product:
                layout.separator(factor=0.5)
                _draw_product_detail(layout, product)

        # ══ INSERT button ═════════════════════════════════════════════════
        layout.separator(factor=0.5)
        row = layout.row()
        row.enabled = bool(selected_slug)
        row.scale_y = 1.6
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
