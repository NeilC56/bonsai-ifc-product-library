"""
IFC Product Library — Category Templates

Provides IFC class / predefined type mappings and property field definitions
for each product category. Templates are hardcoded here matching the library.json
category structure; they can be extended to load from external JSON in future.

Usage:
    from .core import templates
    tree = templates.get_category_tree()
    tmpl = templates.get_template_for_category("sanitaryware/basins/wall-hung")
"""

# ---------------------------------------------------------------------------
# Category → IFC mapping
# Each entry: (ifc_class, predefined_type, [property_field_defs])
#
# property_field_defs: list of dicts with keys:
#   key, label, type ('str'|'int'|'float'|'bool'|'enum'), options (for enum),
#   default, unit (optional, for display)
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict] = {

    # ── Sanitaryware ─────────────────────────────────────────────────────────

    "sanitaryware/basins/wall-hung": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "WASHHANDBASIN",
        "properties": [
            {"key": "material",           "label": "Material",      "type": "enum",
             "options": ["Vitreous china", "Stainless steel", "Ceramic", "Resin", "Other"],
             "default": "Vitreous china"},
            {"key": "colour",             "label": "Colour",        "type": "str",  "default": "White"},
            {"key": "tap_holes",          "label": "Tap Holes",     "type": "int",  "default": 1},
            {"key": "overflow",           "label": "Overflow",      "type": "bool", "default": True},
            {"key": "outlet_diameter_mm", "label": "Outlet Ø",     "type": "float","default": 32, "unit": "mm"},
        ],
        "uniclass_hint": "Pr_40_20_96_96",
    },

    "sanitaryware/basins/pedestal": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "WASHHANDBASIN",
        "properties": [
            {"key": "material",           "label": "Material",      "type": "enum",
             "options": ["Vitreous china", "Ceramic", "Resin", "Other"],
             "default": "Vitreous china"},
            {"key": "colour",             "label": "Colour",        "type": "str",  "default": "White"},
            {"key": "tap_holes",          "label": "Tap Holes",     "type": "int",  "default": 2},
            {"key": "overflow",           "label": "Overflow",      "type": "bool", "default": True},
            {"key": "outlet_diameter_mm", "label": "Outlet Ø",     "type": "float","default": 32, "unit": "mm"},
        ],
        "uniclass_hint": "Pr_40_20_96_96",
    },

    "sanitaryware/basins/countertop": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "WASHHANDBASIN",
        "properties": [
            {"key": "material",           "label": "Material",      "type": "enum",
             "options": ["Vitreous china", "Ceramic", "Resin", "Stone", "Other"],
             "default": "Vitreous china"},
            {"key": "colour",             "label": "Colour",        "type": "str",  "default": "White"},
            {"key": "tap_holes",          "label": "Tap Holes",     "type": "int",  "default": 1},
            {"key": "overflow",           "label": "Overflow",      "type": "bool", "default": False},
        ],
        "uniclass_hint": "Pr_40_20_96_96",
    },

    "sanitaryware/basins/semi-recessed": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "WASHHANDBASIN",
        "properties": [
            {"key": "material",           "label": "Material",      "type": "enum",
             "options": ["Vitreous china", "Ceramic", "Resin", "Other"],
             "default": "Vitreous china"},
            {"key": "colour",             "label": "Colour",        "type": "str",  "default": "White"},
            {"key": "tap_holes",          "label": "Tap Holes",     "type": "int",  "default": 1},
            {"key": "overflow",           "label": "Overflow",      "type": "bool", "default": True},
        ],
        "uniclass_hint": "Pr_40_20_96_96",
    },

    "sanitaryware/wc-pans/close-coupled": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "TOILETPAN",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Vitreous china", "Ceramic"], "default": "Vitreous china"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "pan_type",    "label": "Pan Type",     "type": "enum",
             "options": ["Close-coupled", "Back-to-wall", "Wall-hung"], "default": "Close-coupled"},
            {"key": "flush_litres","label": "Flush Volume", "type": "float", "default": 6.0, "unit": "L"},
            {"key": "dual_flush",  "label": "Dual Flush",   "type": "bool", "default": True},
        ],
        "uniclass_hint": "Pr_40_20_96_29",
    },

    "sanitaryware/wc-pans/back-to-wall": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "TOILETPAN",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Vitreous china", "Ceramic"], "default": "Vitreous china"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "flush_litres","label": "Flush Volume", "type": "float", "default": 6.0, "unit": "L"},
            {"key": "dual_flush",  "label": "Dual Flush",   "type": "bool", "default": True},
        ],
        "uniclass_hint": "Pr_40_20_96_29",
    },

    "sanitaryware/wc-pans/wall-hung": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "TOILETPAN",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Vitreous china", "Ceramic"], "default": "Vitreous china"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "flush_litres","label": "Flush Volume", "type": "float", "default": 6.0, "unit": "L"},
            {"key": "dual_flush",  "label": "Dual Flush",   "type": "bool", "default": True},
            {"key": "frame_required", "label": "Frame Required", "type": "bool", "default": True},
        ],
        "uniclass_hint": "Pr_40_20_96_29",
    },

    "sanitaryware/baths": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "BATH",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Acrylic", "Steel", "Cast iron", "Stone resin", "Other"],
             "default": "Acrylic"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "tap_holes",   "label": "Tap Holes",    "type": "int", "default": 2},
            {"key": "overflow",    "label": "Overflow",     "type": "bool", "default": True},
            {"key": "jets",        "label": "Whirlpool Jets","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_20_96_14",
    },

    "sanitaryware/shower-trays": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "SHOWER",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Acrylic", "Stone resin", "Ceramic", "Other"],
             "default": "Acrylic"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "waste_dia_mm","label": "Waste Ø",     "type": "float","default": 90, "unit": "mm"},
            {"key": "low_profile", "label": "Low Profile",  "type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_20_96_79",
    },

    "sanitaryware/urinals": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "URINAL",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Vitreous china", "Stainless steel", "Other"],
             "default": "Vitreous china"},
            {"key": "colour",      "label": "Colour",       "type": "str", "default": "White"},
            {"key": "flush_litres","label": "Flush Volume", "type": "float","default": 1.0, "unit": "L"},
        ],
        "uniclass_hint": "Pr_40_20_96_93",
    },

    "sanitaryware/cisterns": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "CISTERN",
        "properties": [
            {"key": "material",    "label": "Material",     "type": "enum",
             "options": ["Vitreous china", "Plastic", "Other"],
             "default": "Vitreous china"},
            {"key": "capacity_litres","label": "Capacity",  "type": "float","default": 9.0, "unit": "L"},
            {"key": "dual_flush",  "label": "Dual Flush",   "type": "bool","default": True},
        ],
        "uniclass_hint": "Pr_40_20_96_20",
    },

    # ── Ironmongery ──────────────────────────────────────────────────────────

    "ironmongery/door-handles": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",     "label": "Material",   "type": "enum",
             "options": ["Stainless steel", "Brass", "Chrome", "Satin chrome",
                         "Aluminium", "Bronze", "Other"],
             "default": "Stainless steel"},
            {"key": "finish",       "label": "Finish",     "type": "str", "default": "Satin"},
            {"key": "backset_mm",   "label": "Backset",    "type": "float","default": 57.5, "unit": "mm"},
            {"key": "lever_or_knob","label": "Type",       "type": "enum",
             "options": ["Lever", "Knob", "Pull"], "default": "Lever"},
            {"key": "latch_included","label": "Latch Included","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_50_36_32",
    },

    "ironmongery/hinges": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",  "label": "Material",  "type": "enum",
             "options": ["Stainless steel", "Steel", "Brass", "Other"],
             "default": "Stainless steel"},
            {"key": "finish",    "label": "Finish",    "type": "str", "default": "Satin"},
            {"key": "hinge_type","label": "Type",      "type": "enum",
             "options": ["Butt", "Parliament", "Continuous", "Concealed", "Pivot"],
             "default": "Butt"},
            {"key": "fire_rated","label": "Fire Rated","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_50_36_36",
    },

    "ironmongery/locks": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",    "label": "Material",  "type": "enum",
             "options": ["Stainless steel", "Brass", "Other"],
             "default": "Stainless steel"},
            {"key": "lock_type",   "label": "Type",      "type": "enum",
             "options": ["Mortice deadlock", "Mortice sashlock", "Rim lock",
                         "Padlock", "Cylinder lock", "Other"],
             "default": "Mortice deadlock"},
            {"key": "backset_mm",  "label": "Backset",   "type": "float","default": 57.5, "unit": "mm"},
            {"key": "fire_rated",  "label": "Fire Rated","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_50_36_47",
    },

    "ironmongery/closers": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",    "label": "Material",  "type": "str", "default": "Aluminium"},
            {"key": "closer_type", "label": "Type",      "type": "enum",
             "options": ["Surface mounted", "Overhead concealed", "Floor spring", "Cam action"],
             "default": "Surface mounted"},
            {"key": "door_size",   "label": "Door Size", "type": "enum",
             "options": ["1 (up to 750mm)", "2 (up to 850mm)", "3 (up to 950mm)",
                         "4 (up to 1100mm)", "5 (up to 1400mm)"],
             "default": "3 (up to 950mm)"},
            {"key": "hold_open",   "label": "Hold Open", "type": "bool","default": False},
            {"key": "fire_rated",  "label": "Fire Rated","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_40_50_36_18",
    },

    # ── Doors ─────────────────────────────────────────────────────────────

    "doors/internal": {
        "ifc_class": "IfcDoor",
        "predefined_type": "DOOR",
        "properties": [
            {"key": "material",       "label": "Material",    "type": "enum",
             "options": ["Timber", "Glass", "Composite", "Other"],
             "default": "Timber"},
            {"key": "finish",         "label": "Finish",      "type": "str", "default": "Painted white"},
            {"key": "fire_rating",    "label": "Fire Rating", "type": "enum",
             "options": ["None", "FD20", "FD30", "FD60", "FD90"],
             "default": "None"},
            {"key": "acoustic_rating_db","label": "Acoustic dB","type": "float","default": 0},
            {"key": "rebated",        "label": "Rebated",     "type": "bool", "default": True},
        ],
        "uniclass_hint": "Pr_25_50_08_14",
    },

    "doors/external": {
        "ifc_class": "IfcDoor",
        "predefined_type": "DOOR",
        "properties": [
            {"key": "material",       "label": "Material",    "type": "enum",
             "options": ["Timber", "uPVC", "Aluminium", "Composite", "Steel", "Other"],
             "default": "Timber"},
            {"key": "finish",         "label": "Finish",      "type": "str", "default": ""},
            {"key": "glazing",        "label": "Glazing",     "type": "enum",
             "options": ["None", "Single", "Double", "Triple"],
             "default": "Double"},
            {"key": "u_value",        "label": "U-value",     "type": "float","default": 1.4, "unit": "W/m²K"},
            {"key": "security_rating","label": "Security",    "type": "enum",
             "options": ["None", "PAS 24", "SBD", "RC2", "RC3"],
             "default": "PAS 24"},
        ],
        "uniclass_hint": "Pr_25_50_08_05",
    },

    "doors/fire-rated": {
        "ifc_class": "IfcDoor",
        "predefined_type": "DOOR",
        "properties": [
            {"key": "material",       "label": "Material",    "type": "enum",
             "options": ["Timber", "Steel", "Composite", "Other"],
             "default": "Timber"},
            {"key": "fire_rating",    "label": "Fire Rating", "type": "enum",
             "options": ["FD20", "FD30", "FD60", "FD90", "FD120"],
             "default": "FD30"},
            {"key": "self_closing",   "label": "Self-Closing","type": "bool","default": True},
            {"key": "intumescent_seal","label": "Intumescent Seal","type": "bool","default": True},
        ],
        "uniclass_hint": "Pr_25_50_08_14",
    },

    # ── Windows ───────────────────────────────────────────────────────────

    "windows/casement": {
        "ifc_class": "IfcWindow",
        "predefined_type": "WINDOW",
        "properties": [
            {"key": "frame_material", "label": "Frame Material", "type": "enum",
             "options": ["Timber", "uPVC", "Aluminium", "Composite", "Other"],
             "default": "Timber"},
            {"key": "glazing",        "label": "Glazing",       "type": "enum",
             "options": ["Single", "Double", "Triple"],
             "default": "Double"},
            {"key": "u_value",        "label": "U-value",       "type": "float","default": 1.4, "unit": "W/m²K"},
            {"key": "opening_lights", "label": "Opening Lights","type": "int",  "default": 1},
        ],
        "uniclass_hint": "Pr_25_70_97_14",
    },

    "windows/sash": {
        "ifc_class": "IfcWindow",
        "predefined_type": "WINDOW",
        "properties": [
            {"key": "frame_material", "label": "Frame Material", "type": "enum",
             "options": ["Timber", "uPVC", "Aluminium", "Other"],
             "default": "Timber"},
            {"key": "glazing",        "label": "Glazing",       "type": "enum",
             "options": ["Single", "Double", "Triple"],
             "default": "Double"},
            {"key": "u_value",        "label": "U-value",       "type": "float","default": 1.4, "unit": "W/m²K"},
        ],
        "uniclass_hint": "Pr_25_70_97_14",
    },

    "windows/rooflights": {
        "ifc_class": "IfcWindow",
        "predefined_type": "SKYLIGHT",
        "properties": [
            {"key": "frame_material", "label": "Frame Material", "type": "enum",
             "options": ["Aluminium", "uPVC", "Timber", "Other"],
             "default": "Aluminium"},
            {"key": "glazing",        "label": "Glazing",       "type": "enum",
             "options": ["Double", "Triple"],
             "default": "Double"},
            {"key": "u_value",        "label": "U-value",       "type": "float","default": 1.4, "unit": "W/m²K"},
            {"key": "opening",        "label": "Opening",       "type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_25_70_72",
    },

    # ── Insulation ────────────────────────────────────────────────────────

    "insulation/rigid-board": {
        "ifc_class": "IfcBuildingElementPart",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",       "label": "Material",    "type": "enum",
             "options": ["PIR", "PUR", "EPS", "XPS", "Phenolic", "Other"],
             "default": "PIR"},
            {"key": "lambda_value",   "label": "λ (W/mK)",   "type": "float","default": 0.022},
            {"key": "compressive_str","label": "Compressive Strength","type": "str","default": ""},
            {"key": "faced",          "label": "Faced",       "type": "bool","default": True},
        ],
        "uniclass_hint": "Pr_15_50_08_63",
    },

    "insulation/mineral-wool": {
        "ifc_class": "IfcBuildingElementPart",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",       "label": "Material",    "type": "enum",
             "options": ["Glass wool", "Rock wool", "Stone wool"],
             "default": "Rock wool"},
            {"key": "lambda_value",   "label": "λ (W/mK)",   "type": "float","default": 0.035},
            {"key": "density_kgm3",   "label": "Density",     "type": "float","default": 45, "unit": "kg/m³"},
            {"key": "fire_rating",    "label": "Fire Rating", "type": "str", "default": "A1"},
        ],
        "uniclass_hint": "Pr_15_50_08_63",
    },

    # ── Furniture ─────────────────────────────────────────────────────────

    "furniture/kitchen": {
        "ifc_class": "IfcFurniture",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",  "label": "Material",  "type": "str", "default": ""},
            {"key": "finish",    "label": "Finish",    "type": "str", "default": ""},
            {"key": "colour",    "label": "Colour",    "type": "str", "default": ""},
        ],
        "uniclass_hint": "Pr_70_70_33",
    },

    "furniture/office": {
        "ifc_class": "IfcFurniture",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",  "label": "Material",  "type": "str", "default": ""},
            {"key": "colour",    "label": "Colour",    "type": "str", "default": ""},
            {"key": "adjustable","label": "Adjustable","type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_70_70_31",
    },

    "furniture/loose": {
        "ifc_class": "IfcFurniture",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",  "label": "Material",  "type": "str", "default": ""},
            {"key": "colour",    "label": "Colour",    "type": "str", "default": ""},
        ],
        "uniclass_hint": "Pr_70_70",
    },

    # ── Accessibility ─────────────────────────────────────────────────────

    "accessibility/grab-rails": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",    "label": "Material",    "type": "enum",
             "options": ["Stainless steel", "Nylon-coated", "Chrome", "Other"],
             "default": "Stainless steel"},
            {"key": "finish",      "label": "Finish",      "type": "str", "default": "Satin"},
            {"key": "diameter_mm", "label": "Rail Ø",     "type": "float","default": 35, "unit": "mm"},
            {"key": "fold_down",   "label": "Fold Down",   "type": "bool","default": False},
            {"key": "doc_m",       "label": "Doc M",       "type": "bool","default": True},
            {"key": "load_rating_kg","label": "Load Rating","type": "float","default": 150, "unit": "kg"},
        ],
        "uniclass_hint": "Pr_70_70_16_35",
    },

    "accessibility/doc-m-packs": {
        "ifc_class": "IfcFurnishingElement",
        "predefined_type": "NOTDEFINED",
        "properties": [
            {"key": "material",    "label": "Material",    "type": "enum",
             "options": ["Stainless steel", "Nylon-coated", "Other"],
             "default": "Stainless steel"},
            {"key": "configuration","label": "Configuration","type": "enum",
             "options": ["Doc M WC", "Doc M shower", "Doc M basin", "Full suite"],
             "default": "Doc M WC"},
            {"key": "ambulant",    "label": "Ambulant",    "type": "bool","default": False},
        ],
        "uniclass_hint": "Pr_70_70_16_35",
    },

    # ── Structural ────────────────────────────────────────────────────────────

    "structural/steel/universal-beams": {
        "ifc_class": "IfcBeam",
        "predefined_type": "BEAM",
        "properties": [
            {"key": "steel_grade",        "label": "Steel Grade",          "type": "enum",
             "options": ["S235", "S275", "S355", "S420", "S460"],
             "default": "S355"},
            {"key": "section_size",       "label": "Section Size",         "type": "str",  "default": ""},
            {"key": "section_weight_kgm", "label": "Section Weight",       "type": "float","default": 0.0, "unit": "kg/m"},
            {"key": "depth_mm",           "label": "Depth",                "type": "float","default": 0.0, "unit": "mm"},
            {"key": "flange_width_mm",    "label": "Flange Width",         "type": "float","default": 0.0, "unit": "mm"},
            {"key": "web_thickness_mm",   "label": "Web Thickness",        "type": "float","default": 0.0, "unit": "mm"},
            {"key": "material",           "label": "Material",             "type": "str",  "default": "Steel - S355"},
        ],
        "uniclass_hint": "Pr_20_65_06_93",
    },

    "structural/steel/universal-columns": {
        "ifc_class": "IfcColumn",
        "predefined_type": "COLUMN",
        "properties": [
            {"key": "steel_grade",        "label": "Steel Grade",          "type": "enum",
             "options": ["S235", "S275", "S355", "S420", "S460"],
             "default": "S355"},
            {"key": "section_size",       "label": "Section Size",         "type": "str",  "default": ""},
            {"key": "section_weight_kgm", "label": "Section Weight",       "type": "float","default": 0.0, "unit": "kg/m"},
            {"key": "depth_mm",           "label": "Depth",                "type": "float","default": 0.0, "unit": "mm"},
            {"key": "flange_width_mm",    "label": "Flange Width",         "type": "float","default": 0.0, "unit": "mm"},
            {"key": "web_thickness_mm",   "label": "Web Thickness",        "type": "float","default": 0.0, "unit": "mm"},
            {"key": "material",           "label": "Material",             "type": "str",  "default": "Steel - S355"},
        ],
        "uniclass_hint": "Pr_20_65_06_93",
    },

    "structural/steel/channels": {
        "ifc_class": "IfcMember",
        "predefined_type": "MEMBER",
        "properties": [
            {"key": "steel_grade",        "label": "Steel Grade",          "type": "enum",
             "options": ["S235", "S275", "S355", "S420", "S460"],
             "default": "S355"},
            {"key": "section_size",       "label": "Section Size",         "type": "str",  "default": ""},
            {"key": "section_weight_kgm", "label": "Section Weight",       "type": "float","default": 0.0, "unit": "kg/m"},
            {"key": "depth_mm",           "label": "Depth",                "type": "float","default": 0.0, "unit": "mm"},
            {"key": "flange_width_mm",    "label": "Flange Width",         "type": "float","default": 0.0, "unit": "mm"},
            {"key": "web_thickness_mm",   "label": "Web Thickness",        "type": "float","default": 0.0, "unit": "mm"},
            {"key": "material",           "label": "Material",             "type": "str",  "default": "Steel - S355"},
        ],
        "uniclass_hint": "Pr_20_65_06_93",
    },

    "structural/steel/angles": {
        "ifc_class": "IfcMember",
        "predefined_type": "MEMBER",
        "properties": [
            {"key": "steel_grade",        "label": "Steel Grade",          "type": "enum",
             "options": ["S235", "S275", "S355", "S420", "S460"],
             "default": "S355"},
            {"key": "section_size",       "label": "Section Size",         "type": "str",  "default": ""},
            {"key": "section_weight_kgm", "label": "Section Weight",       "type": "float","default": 0.0, "unit": "kg/m"},
            {"key": "depth_mm",           "label": "Depth",                "type": "float","default": 0.0, "unit": "mm"},
            {"key": "flange_width_mm",    "label": "Flange Width",         "type": "float","default": 0.0, "unit": "mm"},
            {"key": "web_thickness_mm",   "label": "Web Thickness",        "type": "float","default": 0.0, "unit": "mm"},
            {"key": "material",           "label": "Material",             "type": "str",  "default": "Steel - S355"},
        ],
        "uniclass_hint": "Pr_20_65_06_93",
    },

    "structural/steel/hollow-sections": {
        "ifc_class": "IfcMember",
        "predefined_type": "MEMBER",
        "properties": [
            {"key": "steel_grade",        "label": "Steel Grade",          "type": "enum",
             "options": ["S235", "S275", "S355", "S420", "S460"],
             "default": "S355"},
            {"key": "section_size",       "label": "Section Size",         "type": "str",  "default": ""},
            {"key": "section_weight_kgm", "label": "Section Weight",       "type": "float","default": 0.0, "unit": "kg/m"},
            {"key": "depth_mm",           "label": "Depth",                "type": "float","default": 0.0, "unit": "mm"},
            {"key": "flange_width_mm",    "label": "Flange Width",         "type": "float","default": 0.0, "unit": "mm"},
            {"key": "web_thickness_mm",   "label": "Web Thickness",        "type": "float","default": 0.0, "unit": "mm"},
            {"key": "material",           "label": "Material",             "type": "str",  "default": "Steel - S355"},
        ],
        "uniclass_hint": "Pr_20_65_06_93",
    },

    "structural/timber": {
        "ifc_class": "IfcMember",
        "predefined_type": "MEMBER",
        "properties": [
            {"key": "timber_class",   "label": "Strength Class",  "type": "enum",
             "options": ["C16", "C24", "C27", "C35", "GL24h", "GL28h", "GL32h"],
             "default": "C24"},
            {"key": "species",        "label": "Species",          "type": "str",  "default": ""},
            {"key": "section_size",   "label": "Section Size",     "type": "str",  "default": ""},
            {"key": "treatment",      "label": "Treatment",        "type": "enum",
             "options": ["None", "Tanalised", "Fire retardant", "Other"],
             "default": "None"},
            {"key": "material",       "label": "Material",         "type": "str",  "default": "Timber"},
        ],
        "uniclass_hint": "Pr_20_65_06_87",
    },

    "structural/concrete/precast": {
        "ifc_class": "IfcMember",
        "predefined_type": "MEMBER",
        "properties": [
            {"key": "concrete_class", "label": "Concrete Class",   "type": "enum",
             "options": ["C20/25", "C25/30", "C28/35", "C30/37", "C32/40", "C35/45", "C40/50"],
             "default": "C32/40"},
            {"key": "section_size",   "label": "Section Size",     "type": "str",  "default": ""},
            {"key": "reinforcement",  "label": "Reinforcement",    "type": "str",  "default": ""},
            {"key": "finish",         "label": "Finish",           "type": "enum",
             "options": ["As-cast", "Fair-faced", "Painted", "Other"],
             "default": "As-cast"},
            {"key": "material",       "label": "Material",         "type": "str",  "default": "Concrete - Precast"},
        ],
        "uniclass_hint": "Pr_20_65_06_16",
    },

    "structural/concrete/lintels": {
        "ifc_class": "IfcBeam",
        "predefined_type": "LINTEL",
        "properties": [
            {"key": "concrete_class", "label": "Concrete Class",   "type": "enum",
             "options": ["C20/25", "C25/30", "C28/35", "C30/37", "C32/40"],
             "default": "C25/30"},
            {"key": "section_size",   "label": "Section Size",     "type": "str",  "default": ""},
            {"key": "reinforcement",  "label": "Reinforcement",    "type": "str",  "default": ""},
            {"key": "material",       "label": "Material",         "type": "str",  "default": "Concrete - Precast"},
        ],
        "uniclass_hint": "Pr_20_65_06_16",
    },

    "accessibility/accessible-wc": {
        "ifc_class": "IfcSanitaryTerminal",
        "predefined_type": "TOILETPAN",
        "properties": [
            {"key": "material",    "label": "Material",    "type": "enum",
             "options": ["Vitreous china", "Ceramic"],
             "default": "Vitreous china"},
            {"key": "doc_m",       "label": "Doc M",       "type": "bool","default": True},
            {"key": "raised_height","label": "Raised Height","type": "bool","default": True},
            {"key": "flush_litres","label": "Flush Volume","type": "float","default": 6.0, "unit": "L"},
        ],
        "uniclass_hint": "Pr_40_20_96_29",
    },
}

# Default template used when no specific match is found
_DEFAULT_TEMPLATE: dict = {
    "ifc_class": "IfcBuildingElementProxy",
    "predefined_type": "NOTDEFINED",
    "properties": [
        {"key": "material", "label": "Material", "type": "str", "default": ""},
        {"key": "colour",   "label": "Colour",   "type": "str", "default": ""},
    ],
    "uniclass_hint": "",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_category_tree() -> list:
    """Return the category tree from the loaded library index.

    Falls back to the static list embedded here if the library isn't loaded.
    Returns a list of top-level category dicts matching library.json structure.
    """
    try:
        from .library_index import get_index
        idx = get_index()
        meta = idx.get("library_meta", {})
        if meta and "categories" in meta:
            return meta["categories"]
    except Exception:
        pass
    return _STATIC_CATEGORY_TREE


def get_template_for_category(category_path: str) -> dict:
    """Return the template dict for a category path.

    Falls back to parent category if exact path not found, then to default.
    """
    # Exact match
    if category_path in _TEMPLATES:
        return _TEMPLATES[category_path]

    # Try progressively shorter paths (parent categories)
    parts = category_path.split("/")
    for depth in range(len(parts) - 1, 0, -1):
        parent = "/".join(parts[:depth])
        if parent in _TEMPLATES:
            return _TEMPLATES[parent]

    return _DEFAULT_TEMPLATE


def get_ifc_class(category_path: str) -> str:
    return get_template_for_category(category_path).get("ifc_class", "IfcBuildingElementProxy")


def get_predefined_type(category_path: str) -> str:
    return get_template_for_category(category_path).get("predefined_type", "NOTDEFINED")


def get_property_fields(category_path: str) -> list:
    return get_template_for_category(category_path).get("properties", [])


def get_uniclass_hint(category_path: str) -> str:
    return get_template_for_category(category_path).get("uniclass_hint", "")


# ---------------------------------------------------------------------------
# Enum helpers for UI dropdowns
# ---------------------------------------------------------------------------

def category_enum_items(include_blank: bool = True) -> list[tuple]:
    """Return (identifier, label, description) tuples for all leaf categories.

    Suitable for passing to bpy.props.EnumProperty(items=...).
    """
    items = []
    if include_blank:
        items.append(("", "— Select category —", ""))

    def _walk(cats, prefix=""):
        for cat in cats:
            path = cat["path"]
            label = cat["label"]
            subs = cat.get("subcategories", [])
            if subs:
                _walk(subs, prefix)
            else:
                items.append((path, label, ""))

    tree = get_category_tree()
    _walk(tree)
    return items


def category_path_label(path: str) -> str:
    """Return a human-readable label for a category path, e.g. 'Wall-Hung Basins'."""
    def _find(cats, target):
        for cat in cats:
            if cat["path"] == target:
                return cat["label"]
            result = _find(cat.get("subcategories", []), target)
            if result:
                return result
        return None

    label = _find(get_category_tree(), path)
    return label or path


# ---------------------------------------------------------------------------
# Static category tree fallback (mirrors library.json)
# ---------------------------------------------------------------------------

_STATIC_CATEGORY_TREE = [
    {"path": "sanitaryware", "label": "Sanitaryware", "subcategories": [
        {"path": "sanitaryware/basins", "label": "Basins", "subcategories": [
            {"path": "sanitaryware/basins/wall-hung",     "label": "Wall-Hung"},
            {"path": "sanitaryware/basins/pedestal",      "label": "Pedestal"},
            {"path": "sanitaryware/basins/countertop",    "label": "Countertop"},
            {"path": "sanitaryware/basins/semi-recessed", "label": "Semi-Recessed"},
        ]},
        {"path": "sanitaryware/wc-pans", "label": "WC Pans", "subcategories": [
            {"path": "sanitaryware/wc-pans/close-coupled", "label": "Close-Coupled"},
            {"path": "sanitaryware/wc-pans/back-to-wall",  "label": "Back-to-Wall"},
            {"path": "sanitaryware/wc-pans/wall-hung",     "label": "Wall-Hung"},
        ]},
        {"path": "sanitaryware/baths",        "label": "Baths"},
        {"path": "sanitaryware/shower-trays", "label": "Shower Trays"},
        {"path": "sanitaryware/urinals",      "label": "Urinals"},
        {"path": "sanitaryware/cisterns",     "label": "Cisterns"},
    ]},
    {"path": "ironmongery", "label": "Ironmongery", "subcategories": [
        {"path": "ironmongery/door-handles", "label": "Door Handles"},
        {"path": "ironmongery/hinges",       "label": "Hinges"},
        {"path": "ironmongery/locks",        "label": "Locks"},
        {"path": "ironmongery/closers",      "label": "Closers"},
    ]},
    {"path": "doors", "label": "Doors", "subcategories": [
        {"path": "doors/internal",   "label": "Internal"},
        {"path": "doors/external",   "label": "External"},
        {"path": "doors/fire-rated", "label": "Fire-Rated"},
    ]},
    {"path": "windows", "label": "Windows", "subcategories": [
        {"path": "windows/casement",   "label": "Casement"},
        {"path": "windows/sash",       "label": "Sash"},
        {"path": "windows/rooflights", "label": "Rooflights"},
    ]},
    {"path": "insulation", "label": "Insulation", "subcategories": [
        {"path": "insulation/rigid-board",  "label": "Rigid Board"},
        {"path": "insulation/mineral-wool", "label": "Mineral Wool"},
        {"path": "insulation/natural",      "label": "Natural"},
    ]},
    {"path": "furniture", "label": "Furniture", "subcategories": [
        {"path": "furniture/kitchen", "label": "Kitchen"},
        {"path": "furniture/office",  "label": "Office"},
        {"path": "furniture/loose",   "label": "Loose"},
    ]},
    {"path": "accessibility", "label": "Accessibility", "subcategories": [
        {"path": "accessibility/doc-m-packs",    "label": "Doc M Packs"},
        {"path": "accessibility/grab-rails",     "label": "Grab Rails"},
        {"path": "accessibility/accessible-wc",  "label": "Accessible WC"},
    ]},
    {"path": "structural", "label": "Structural", "subcategories": [
        {"path": "structural/steel", "label": "Steel", "subcategories": [
            {"path": "structural/steel/universal-beams",   "label": "Universal Beams"},
            {"path": "structural/steel/universal-columns", "label": "Universal Columns"},
            {"path": "structural/steel/channels",          "label": "Channels"},
            {"path": "structural/steel/angles",            "label": "Angles"},
            {"path": "structural/steel/hollow-sections",   "label": "Hollow Sections"},
        ]},
        {"path": "structural/timber", "label": "Timber"},
        {"path": "structural/concrete", "label": "Concrete", "subcategories": [
            {"path": "structural/concrete/precast",  "label": "Precast"},
            {"path": "structural/concrete/lintels",  "label": "Lintels"},
        ]},
    ]},
]
