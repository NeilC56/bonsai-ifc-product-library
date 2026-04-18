"""Operators for navigating the library browser: expand categories, select
products, reload the library from disk."""

import bpy
from ..core import library_index
from .. import _ADDON_ID   # full package name, safe for both dev and installed extension


class IFCLIB_OT_BrowseCategory(bpy.types.Operator):
    """Expand or collapse a category, and make it the active category
    so its products appear in the list below the tree."""
    bl_idname = "ifclib.browse_category"
    bl_label = "Browse Category"
    bl_options = {"INTERNAL"}

    category_path: bpy.props.StringProperty(default="")
    has_subcategories: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        if self.has_subcategories:
            library_index.toggle_category(self.category_path)
        library_index.select_category(self.category_path)
        _redraw_panels(context)
        return {"FINISHED"}


class IFCLIB_OT_SelectProduct(bpy.types.Operator):
    """Select a product to display its details and enable the Insert button."""
    bl_idname = "ifclib.select_product"
    bl_label = "Select Product"
    bl_options = {"INTERNAL"}

    product_slug: bpy.props.StringProperty(default="")

    def execute(self, context):
        library_index.select_product(self.product_slug)
        _redraw_panels(context)
        return {"FINISHED"}


class IFCLIB_OT_RefreshLibrary(bpy.types.Operator):
    """Reload every product.json from the library folder."""
    bl_idname = "ifclib.refresh_library"
    bl_label = "Refresh Library"
    bl_description = "Reload all products from the library folder on disk"

    def execute(self, context):
        addon_prefs = context.preferences.addons.get(_ADDON_ID)
        if not addon_prefs:
            self.report({"ERROR"}, "Could not find addon preferences")
            return {"CANCELLED"}

        lib_path = addon_prefs.preferences.library_path
        if not lib_path:
            self.report({"WARNING"}, "No library path set — open Addon Preferences")
            return {"CANCELLED"}

        library_index.load_library(lib_path)

        # Clear span table cache so stale data is not shown after a reload
        from ..core import span_tables as _st
        _st.invalidate_cache()

        index = library_index.get_index()
        if index["error"]:
            self.report({"ERROR"}, index["error"])
            return {"CANCELLED"}

        count = len(index["products"])
        self.report({"INFO"}, f"Library reloaded — {count} product{'s' if count != 1 else ''}")
        _redraw_panels(context)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _redraw_panels(context) -> None:
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()
