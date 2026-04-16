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

    mayo_path: bpy.props.StringProperty(
        name="Mayo Path",
        description=(
            "Path to the Mayo executable for converting STEP files to glTF. "
            "Leave blank if Mayo is not installed."
        ),
        default="",
        subtype="FILE_PATH",
    )

    small_part_threshold_mm: bpy.props.FloatProperty(
        name="Small Part Threshold (mm)",
        description=(
            "Default threshold for 'Remove Small Parts' in the Import Wizard. "
            "Objects with all dimensions below this are removed."
        ),
        default=5.0,
        min=0.1,
        max=500.0,
        step=10,
        precision=1,
    )

    bim_face_target: bpy.props.IntProperty(
        name="Optimise Target Faces",
        description=(
            "Target face count when using 'Optimise for BIM'. "
            "Lower = faster model, less geometric detail."
        ),
        default=4000,
        min=500,
        max=20000,
    )

    max_face_count: bpy.props.IntProperty(
        name="Maximum Face Count",
        description=(
            "Hard limit on faces per product. Products exceeding this cannot "
            "be saved to the library."
        ),
        default=50000,
        min=1000,
        max=500000,
    )

    def draw(self, context):
        layout = self.layout

        # ── Library location ─────────────────────────────────────────────
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

        layout.separator()

        # ── STEP conversion ───────────────────────────────────────────────
        layout.label(text="STEP Conversion (Mayo):")
        layout.prop(self, "mayo_path", text="Mayo Executable")

        layout.separator()

        # ── Import Wizard thresholds ──────────────────────────────────────
        layout.label(text="Import Wizard:")
        col = layout.column(align=True)
        col.prop(self, "small_part_threshold_mm", text="Small Part Threshold (mm)")
        col.prop(self, "bim_face_target",         text="Optimise Target Faces")
        col.prop(self, "max_face_count",           text="Maximum Face Count")
