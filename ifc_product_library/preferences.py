"""Addon preferences — single setting: the library path."""

import os
import bpy

# Compute a sensible default relative to the addon's own location.
# When the addon lives at  <project>/ifc_product_library/
# the library lives at     <project>/ifc-product-library/
_DEFAULT_LIBRARY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "ifc-product-library",
)


def _on_library_path_changed(self, context):
    """Called whenever the library_path preference is edited.

    Note: Blender's file-picker for DIR_PATH properties does not always
    trigger this callback — it fires reliably when the user types in the
    field but may not fire after using the folder-browser button.  The
    panel's draw() method has a lazy-load fallback for that case.
    """
    print(f"IFC Product Library: library_path update callback fired")
    print(f"  new value: {self.library_path!r}")
    from .core import library_index
    library_index.load_library(self.library_path)


class IFCProductLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    library_path: bpy.props.StringProperty(
        name="Library Path",
        description=(
            "Root folder of the IFC product library. "
            "Must contain a library.json file and product sub-folders."
        ),
        default=_DEFAULT_LIBRARY_PATH,
        subtype="DIR_PATH",
        update=_on_library_path_changed,
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Library Location:")
        row = layout.row(align=True)
        row.prop(self, "library_path", text="")
        row.operator("ifclib.refresh_library", text="", icon="FILE_REFRESH")

        from .core import library_index
        index = library_index.get_index()

        if index["loaded"]:
            count = len(index["products"])
            layout.label(
                text=f"  {count} product{'s' if count != 1 else ''} loaded",
                icon="CHECKMARK",
            )
        elif index["error"]:
            layout.label(text=f"  {index['error']}", icon="ERROR")
        else:
            layout.label(text="  Library not yet loaded.", icon="INFO")
