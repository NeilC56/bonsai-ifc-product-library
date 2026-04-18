"""Scene-level property groups.

IFCProductLibraryState  — Phase 1 search bar (already existed)
IFCLibMetaFormProps     — Phase 2 Step 4 metadata form float/bool fields

In Blender 5.x, writing to ID class properties (scene["key"]) from a panel
draw function raises a RuntimeError.  Using a registered PropertyGroup avoids
this: the properties live on the group object rather than as ad-hoc custom
properties, and the panel draw only calls row.prop() on them (read path),
writing zero bytes to any ID class.

Text and enum template fields are handled by operator dialogs and never touch
the PropertyGroup at all.
"""

import bpy


# ---------------------------------------------------------------------------
# Phase 1 — search bar
# ---------------------------------------------------------------------------

class IFCProductLibraryState(bpy.types.PropertyGroup):
    search_query: bpy.props.StringProperty(
        name="Search",
        description="Filter products by name, manufacturer, description, or tag",
        default="",
        options={"TEXTEDIT_UPDATE"},
    )


# ---------------------------------------------------------------------------
# Phase 2 — Step 4 metadata form (float / bool fields)
# ---------------------------------------------------------------------------
# Property naming convention
#   dim_{key}  — product dimensions (width_mm, depth_mm, height_mm, weight_kg)
#   comp_{key} — top-level compliance booleans (doc_m)
#   tp_{key}   — template-specific properties, keyed by templates.py field key
# ---------------------------------------------------------------------------

class IFCLibMetaFormProps(bpy.types.PropertyGroup):
    """Float/bool backing store for the Step 4 metadata form.

    Loaded once (via load_meta_to_pg) when the wizard transitions to step 4.
    The panel draw helpers read these properties via row.prop() and
    simultaneously sync the values back into the wizard_state Python dict —
    writing to a plain Python dict from a draw function is allowed.
    """

    # ── Dimensions ──────────────────────────────────────────────────────────
    dim_width_mm:  bpy.props.FloatProperty(name="Width (mm)",       min=0, precision=1)
    dim_depth_mm:  bpy.props.FloatProperty(name="Depth (mm)",       min=0, precision=1)
    dim_height_mm: bpy.props.FloatProperty(name="Height (mm)",      min=0, precision=1)
    dim_weight_kg: bpy.props.FloatProperty(name="Weight (kg)",      min=0, precision=2)

    # ── Compliance ──────────────────────────────────────────────────────────
    comp_doc_m: bpy.props.BoolProperty(name="Doc M Compliant")

    # ── Template property floats ─────────────────────────────────────────────
    # Sanitaryware
    tp_tap_holes:           bpy.props.FloatProperty(name="Tap Holes",             min=0, precision=0, step=100)
    tp_outlet_diameter_mm:  bpy.props.FloatProperty(name="Outlet Ø (mm)",         min=0, precision=1)
    tp_waste_dia_mm:        bpy.props.FloatProperty(name="Waste Ø (mm)",          min=0, precision=1)
    tp_flush_litres:        bpy.props.FloatProperty(name="Flush Volume (L)",      min=0, precision=1)
    tp_capacity_litres:     bpy.props.FloatProperty(name="Capacity (L)",          min=0, precision=1)
    # Doors
    tp_acoustic_rating_db:  bpy.props.FloatProperty(name="Acoustic (dB)",         min=0, precision=1)
    # Ironmongery
    tp_backset_mm:          bpy.props.FloatProperty(name="Backset (mm)",          min=0, precision=1)
    # Windows / doors
    tp_u_value:             bpy.props.FloatProperty(name="U-value (W/m²K)",       min=0, precision=2)
    tp_opening_lights:      bpy.props.FloatProperty(name="Opening Lights",        min=0, precision=0, step=100)
    # Insulation
    tp_lambda_value:        bpy.props.FloatProperty(name="λ (W/mK)",             min=0, precision=3)
    tp_density_kgm3:        bpy.props.FloatProperty(name="Density (kg/m³)",       min=0, precision=1)
    # Accessibility
    tp_diameter_mm:         bpy.props.FloatProperty(name="Rail Ø (mm)",           min=0, precision=1)
    tp_load_rating_kg:      bpy.props.FloatProperty(name="Load Rating (kg)",      min=0, precision=1)
    # Structural steel
    tp_section_weight_kgm:  bpy.props.FloatProperty(name="Section Weight (kg/m)", min=0, precision=2)
    tp_depth_mm:            bpy.props.FloatProperty(name="Depth (mm)",            min=0, precision=1)
    tp_flange_width_mm:     bpy.props.FloatProperty(name="Flange Width (mm)",     min=0, precision=1)
    tp_web_thickness_mm:    bpy.props.FloatProperty(name="Web Thickness (mm)",    min=0, precision=2)
    # Joists (metal-web, solid timber, i-joists)
    tp_span_max_mm:         bpy.props.FloatProperty(name="Max Clear Span (mm)",   min=0, precision=0, step=1000)
    tp_spacing_mm:          bpy.props.FloatProperty(name="Centres (mm)",          min=0, precision=0, step=100)
    tp_fire_rating_minutes: bpy.props.FloatProperty(name="Fire Rating (min)",     min=0, precision=0, step=3000)
    tp_load_capacity_kn_m:  bpy.props.FloatProperty(name="Load Capacity (kN/m)", min=0, precision=2)

    # ── Template property bools ──────────────────────────────────────────────
    # Sanitaryware
    tp_overflow:         bpy.props.BoolProperty(name="Overflow")
    tp_dual_flush:       bpy.props.BoolProperty(name="Dual Flush")
    tp_frame_required:   bpy.props.BoolProperty(name="Frame Required")
    tp_low_profile:      bpy.props.BoolProperty(name="Low Profile")
    tp_jets:             bpy.props.BoolProperty(name="Whirlpool Jets")
    # Ironmongery
    tp_latch_included:   bpy.props.BoolProperty(name="Latch Included")
    tp_fire_rated:       bpy.props.BoolProperty(name="Fire Rated")
    tp_hold_open:        bpy.props.BoolProperty(name="Hold Open")
    # Doors
    tp_rebated:          bpy.props.BoolProperty(name="Rebated")
    tp_self_closing:     bpy.props.BoolProperty(name="Self-Closing")
    tp_intumescent_seal: bpy.props.BoolProperty(name="Intumescent Seal")
    # Windows
    tp_opening:          bpy.props.BoolProperty(name="Opening")
    # Insulation
    tp_faced:            bpy.props.BoolProperty(name="Faced")
    # Furniture
    tp_adjustable:       bpy.props.BoolProperty(name="Adjustable")
    # Accessibility
    tp_fold_down:        bpy.props.BoolProperty(name="Fold Down")
    tp_doc_m:            bpy.props.BoolProperty(name="Doc M")
    tp_ambulant:         bpy.props.BoolProperty(name="Ambulant")
    tp_raised_height:    bpy.props.BoolProperty(name="Raised Height")


# ---------------------------------------------------------------------------
# Flat key lists for load_meta_to_pg — stripped of the "tp_" prefix these
# are exactly the keys used in meta["properties"].
# ---------------------------------------------------------------------------

_TP_FLOAT_ATTRS = (
    "tp_tap_holes", "tp_outlet_diameter_mm", "tp_waste_dia_mm",
    "tp_flush_litres", "tp_capacity_litres", "tp_acoustic_rating_db",
    "tp_backset_mm", "tp_u_value", "tp_opening_lights",
    "tp_lambda_value", "tp_density_kgm3",
    "tp_diameter_mm", "tp_load_rating_kg",
    "tp_section_weight_kgm", "tp_depth_mm", "tp_flange_width_mm", "tp_web_thickness_mm",
    "tp_span_max_mm", "tp_spacing_mm", "tp_fire_rating_minutes", "tp_load_capacity_kn_m",
)

_TP_BOOL_ATTRS = (
    "tp_overflow", "tp_dual_flush", "tp_frame_required", "tp_low_profile", "tp_jets",
    "tp_latch_included", "tp_fire_rated", "tp_hold_open",
    "tp_rebated", "tp_self_closing", "tp_intumescent_seal",
    "tp_opening", "tp_faced", "tp_adjustable",
    "tp_fold_down", "tp_doc_m", "tp_ambulant", "tp_raised_height",
)


# ---------------------------------------------------------------------------
# Phase 3 — Array Insert property group
# ---------------------------------------------------------------------------

def _load_case_items(self, context):
    """Enum callback that returns load case items from the active span table.

    Always returns at least one sentinel item to prevent Blender from
    crashing on an empty enum.
    """
    try:
        from .core import span_tables, library_index
        pg = context.scene.ifclib_array_insert
        lib_path = library_index.get_index().get("library_path", "")
        tbl = span_tables.load_span_table(lib_path, pg.active_span_table)
        if tbl:
            cases = tbl.get("load_cases", [])
            if cases:
                return [(lc["key"], lc["name"], lc.get("description", "")) for lc in cases]
    except Exception:
        pass
    return [("none", "—", "")]


class IFCArrayInsertProps(bpy.types.PropertyGroup):
    """Parameters for the Array Insert mode (beam/joist products only).

    Registered as ``bpy.types.Scene.ifclib_array_insert``.
    All mutable state is written only from operator execute() methods —
    never from panel draw functions (Blender 5.x constraint).
    """

    placement_mode: bpy.props.EnumProperty(
        name="Placement Mode",
        items=[
            ("SINGLE", "Single", "Insert one instance at the 3D cursor"),
            ("ARRAY",  "Array",  "Insert a row of joists at regular centres"),
        ],
        default="SINGLE",
    )

    beam_length_mm: bpy.props.FloatProperty(
        name="Beam Length (mm)",
        description=(
            "Length of each beam/joist (perpendicular to the array direction). "
            "Typically the clear span plus bearing at each end."
        ),
        default=6000.0,
        min=100.0,
        precision=0,
    )

    spacing_mm: bpy.props.FloatProperty(
        name="Spacing (mm)",
        description="Centre-to-centre spacing between joists in the array direction",
        default=600.0,
        min=50.0,
        precision=0,
    )

    span_length_mm: bpy.props.FloatProperty(
        name="Span Length (mm)",
        description="Total distance to fill in the array direction (e.g. room width)",
        default=4800.0,
        min=100.0,
        precision=0,
    )

    start_offset_mm: bpy.props.FloatProperty(
        name="Start Offset (mm)",
        description="Gap between the cursor/wall and the first joist (array direction)",
        default=20.0,
        min=0.0,
        precision=0,
    )

    end_offset_mm: bpy.props.FloatProperty(
        name="End Offset (mm)",
        description="Gap between the last joist and the far wall (array direction)",
        default=20.0,
        min=0.0,
        precision=0,
    )

    array_direction: bpy.props.EnumProperty(
        name="Array Direction",
        items=[
            ("X", "Along X", "Space joists along the X axis (joists run parallel to Y)"),
            ("Y", "Along Y", "Space joists along the Y axis (joists run parallel to X)"),
        ],
        default="X",
    )

    odd_at_start: bpy.props.BoolProperty(
        name="Odd gap at start",
        description="Place the uneven spacing gap at the start rather than the end",
        default=False,
    )

    show_span_advisory: bpy.props.BoolProperty(
        name="Span Advisory",
        description="Show the span advisory section",
        default=True,
    )

    active_span_table: bpy.props.StringProperty(
        name="Active Span Table",
        description="Filename of the active span table (e.g. mitek-posijoist.json)",
        default="",
    )

    load_case: bpy.props.EnumProperty(
        name="Load Case",
        description="Load case from the active span table",
        items=_load_case_items,
    )


# ---------------------------------------------------------------------------
# Phase 2 — Step 4 helpers
# ---------------------------------------------------------------------------

def load_meta_to_pg(context, meta: dict) -> None:
    """Copy wizard metadata float/bool values into IFCLibMetaFormProps.

    MUST be called from an operator execute() — never from a draw function.
    After this call the panel can read properties via row.prop() without any
    further writes to the PropertyGroup.
    """
    pg = context.scene.ifclib_meta_form

    # Dimensions
    dims = meta.get("dimensions", {})
    pg.dim_width_mm  = float(dims.get("width_mm",  0.0))
    pg.dim_depth_mm  = float(dims.get("depth_mm",  0.0))
    pg.dim_height_mm = float(dims.get("height_mm", 0.0))
    pg.dim_weight_kg = float(dims.get("weight_kg", 0.0))

    # Compliance
    comp = meta.get("compliance", {})
    pg.comp_doc_m = bool(comp.get("doc_m", False))

    # Template properties
    props_dict = meta.get("properties", {})
    for pg_attr in _TP_FLOAT_ATTRS:
        meta_key = pg_attr[3:]          # strip "tp_" prefix
        val = props_dict.get(meta_key)
        if val is not None:
            try:
                setattr(pg, pg_attr, float(val))
            except (TypeError, ValueError, AttributeError):
                pass

    for pg_attr in _TP_BOOL_ATTRS:
        meta_key = pg_attr[3:]
        val = props_dict.get(meta_key)
        if val is not None:
            try:
                setattr(pg, pg_attr, bool(val))
            except (TypeError, ValueError, AttributeError):
                pass
