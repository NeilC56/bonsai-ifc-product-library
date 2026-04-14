# IFC Product Library — Foundation Specification

**Version:** 0.1 Draft
**Date:** April 2026
**Author:** Neil (with Claude)
**Purpose:** Define the data architecture for a self-hosted, open-source IFC product library designed for use with Blender Bonsai, searchable via MCP and a Blender sidebar UI.

---

## 1. Design Principles

The library must be:

- **Plain files on disk** — no database, no server required. A folder you can browse in a file manager, back up with rsync, and version with Git.
- **Human-readable metadata** — JSON sidecars alongside IFC files, editable in any text editor.
- **Organised by what architects think** — product categories, not IFC class hierarchies. Nobody browses for "IfcSanitaryTerminal with PredefinedType WASHHANDBASIN"; they look for "Basins → Wall-hung".
- **Extensible without breakage** — new fields can be added to the metadata schema without invalidating existing entries. Unknown fields are ignored.
- **Git-friendly** — small files, no binaries that change frequently, meaningful diffs on metadata changes.

---

## 2. Folder Structure

```
ifc-product-library/
│
├── library.json                    # Library-level metadata (name, version, author)
│
├── sanitaryware/
│   ├── basins/
│   │   ├── wall-hung/
│   │   │   ├── contour-21-500mm/
│   │   │   │   ├── product.ifc         # The IFC object file
│   │   │   │   ├── product.json        # Metadata sidecar
│   │   │   │   ├── thumbnail.png       # 256×256 preview render (optional)
│   │   │   │   └── source/             # Original source geometry (optional)
│   │   │   │       ├── original.step   #   Kept for re-conversion if needed
│   │   │   │       └── source.json     #   Where it came from, licence, date
│   │   │   │
│   │   │   └── another-basin/
│   │   │       ├── product.ifc
│   │   │       └── product.json
│   │   │
│   │   ├── pedestal/
│   │   ├── countertop/
│   │   └── semi-recessed/
│   │
│   ├── wc-pans/
│   │   ├── close-coupled/
│   │   ├── back-to-wall/
│   │   └── wall-hung/
│   │
│   ├── baths/
│   ├── shower-trays/
│   ├── urinals/
│   └── cisterns/
│
├── ironmongery/
│   ├── door-handles/
│   ├── hinges/
│   ├── locks/
│   └── closers/
│
├── doors/
│   ├── internal/
│   ├── external/
│   └── fire-rated/
│
├── windows/
│   ├── casement/
│   ├── sash/
│   └── rooflights/
│
├── insulation/
│   ├── rigid-board/
│   ├── mineral-wool/
│   └── natural/
│
├── furniture/
│   ├── kitchen/
│   ├── office/
│   └── loose/
│
├── accessibility/            # Cross-cutting category for Doc M, Part M items
│   ├── doc-m-packs/
│   ├── grab-rails/
│   └── accessible-wc/
│
└── _templates/               # Template metadata files for each category
    ├── sanitaryware.json
    ├── ironmongery.json
    └── generic.json
```

### Naming conventions

- **Folder names:** lowercase, hyphen-separated, descriptive. `contour-21-500mm` not `S0439` or `product_001`.
- **Fixed filenames:** Every product folder contains `product.ifc` and `product.json`. No variation — this makes programmatic discovery trivial.
- **Thumbnails:** `thumbnail.png`, 256×256px, transparent or white background, rendered from a consistent 3/4 perspective view.
- **Source folder:** Optional. Preserves the original geometry file before conversion, so you can re-process if the IFC authoring pipeline improves.

---

## 3. Metadata Schema (product.json)

```json
{
  "$schema": "https://example.com/ifc-product-library/v0.1/product.schema.json",
  "schema_version": "0.1",

  "identity": {
    "name": "Contour 21 Wall-Hung Basin 500mm",
    "slug": "contour-21-500mm",
    "description": "Wall-hung washbasin with overflow, suitable for commercial and accessible applications.",
    "manufacturer": "Armitage Shanks",
    "model_number": "S0439",
    "product_url": "https://www.idealspec.co.uk/..."
  },

  "category": {
    "path": "sanitaryware/basins/wall-hung",
    "tags": ["accessible", "commercial", "doc-m", "healthcare"]
  },

  "ifc": {
    "class": "IfcSanitaryTerminal",
    "predefined_type": "WASHHANDBASIN",
    "ifc_version": "IFC4"
  },

  "classification": {
    "uniclass_2015": {
      "code": "Pr_40_20_96_95",
      "description": "Washbasins"
    },
    "omniclass": {
      "code": "23-31 19 11",
      "description": "Lavatories"
    }
  },

  "dimensions": {
    "width_mm": 500,
    "depth_mm": 410,
    "height_mm": 185,
    "weight_kg": 12.5,
    "unit_system": "metric"
  },

  "properties": {
    "material": "Vitreous china",
    "colour": "White",
    "mounting": "Wall-hung",
    "tap_holes": 1,
    "overflow": true,
    "outlet_diameter_mm": 32
  },

  "compliance": {
    "doc_m": true,
    "building_regs": ["Approved Document M"],
    "standards": ["BS 5506", "EN 14688"]
  },

  "provenance": {
    "created_date": "2026-04-12",
    "created_by": "Neil",
    "geometry_source": "TraceParts STEP download",
    "geometry_licence": "TraceParts free download terms",
    "ifc_authored_in": "Blender Bonsai 0.8.4",
    "last_modified": "2026-04-12",
    "library_version": "0.1"
  }
}
```

### Schema notes

- **`identity`** — what the product is, in human terms. The `slug` matches the folder name.
- **`category.path`** — matches the folder path relative to the library root. Redundant with the filesystem, but allows the JSON to be self-describing if the file is moved or shared.
- **`category.tags`** — freeform labels for cross-cutting concerns. An accessible basin lives in `sanitaryware/basins/wall-hung/` but is also tagged `accessible` and `doc-m` so it appears in accessibility searches.
- **`ifc`** — the IFC classification that will be assigned when inserting. This drives the Bonsai/IfcOpenShell assignment.
- **`classification`** — industry classification systems. Uniclass 2015 is essential for UK practice; Omniclass for international.
- **`dimensions`** — key bounding dimensions for quick filtering ("show me all basins under 450mm wide"). Not a substitute for the geometry in the IFC file.
- **`properties`** — product-specific data. This section is intentionally flexible — different product categories will have different relevant properties. The `_templates/` folder provides starting-point schemas for each category.
- **`compliance`** — regulatory and standards compliance. Critical for specification work.
- **`provenance`** — where the geometry came from, what licence applies, who authored it, when. Essential for an open-source library where trust and attribution matter.

---

## 4. Library Index (library.json)

```json
{
  "name": "Neil's Practice Library",
  "version": "0.1",
  "description": "IFC product library for residential and accessible commercial projects",
  "author": "Neil",
  "licence": "CC BY 4.0",
  "ifc_version_default": "IFC4",
  "classification_system_default": "Uniclass 2015",
  "created": "2026-04-12",
  "categories": [
    {
      "path": "sanitaryware",
      "label": "Sanitaryware",
      "icon": "shower",
      "subcategories": [
        { "path": "sanitaryware/basins", "label": "Basins" },
        { "path": "sanitaryware/wc-pans", "label": "WC Pans" },
        { "path": "sanitaryware/baths", "label": "Baths" },
        { "path": "sanitaryware/shower-trays", "label": "Shower Trays" },
        { "path": "sanitaryware/urinals", "label": "Urinals" },
        { "path": "sanitaryware/cisterns", "label": "Cisterns" }
      ]
    },
    {
      "path": "ironmongery",
      "label": "Ironmongery",
      "icon": "key"
    },
    {
      "path": "doors",
      "label": "Doors",
      "icon": "door-open"
    },
    {
      "path": "windows",
      "label": "Windows",
      "icon": "grid-2x2"
    },
    {
      "path": "insulation",
      "label": "Insulation",
      "icon": "layers"
    },
    {
      "path": "furniture",
      "label": "Furniture",
      "icon": "armchair"
    },
    {
      "path": "accessibility",
      "label": "Accessibility",
      "icon": "accessibility"
    }
  ]
}
```

---

## 5. Source Provenance (source/source.json)

When a product's geometry originates from an external source, the `source/` subfolder preserves the original file and records where it came from.

```json
{
  "original_filename": "AS_Contour21_S0439.step",
  "source_platform": "TraceParts",
  "source_url": "https://www.traceparts.com/...",
  "download_date": "2026-04-10",
  "licence": "TraceParts free download — personal/professional use",
  "format": "STEP AP214",
  "conversion_tool": "Mayo 0.9 → glTF → Blender 4.2",
  "conversion_notes": "Removed 37 fastener sub-components. Simplified tap hole geometry to cylinder. Merged basin body shells into single mesh.",
  "original_part_count": 42,
  "final_part_count": 1
}
```

---

## 6. Product IFC File Conventions

Each `product.ifc` file should be a self-contained IFC file with the following structure:

- **IFC version:** IFC4 (IFC4 ADD2 TC1 preferred)
- **Contains:** A single product type (e.g. one `IfcSanitaryTerminalType`) with one occurrence instance
- **Spatial structure:** Minimal — just `IfcProject` → `IfcSite`. No building or storey (these get assigned on insertion into a real project)
- **Geometry representation:** `IfcTriangulatedFaceSet` (IFC4) or `IfcFacetedBrep` (IFC2x3) for product objects. Swept solids for simpler shapes where appropriate
- **Origin:** Object origin at a sensible insertion point — centre of back face for wall-mounted items, centre of base for floor-standing items
- **Orientation:** Front face towards positive Y axis (facing the user in Blender's default front view)
- **Units:** Millimetres
- **Property sets:** Include at minimum `Pset_ManufacturerTypeInformation` and any applicable standard psets for the IFC class. Custom psets prefixed with `CPset_` for practice-specific properties
- **Materials:** Basic `IfcSurfaceStyleRendering` with colour. No textures required but colour should be representative (white for sanitaryware, metallic for ironmongery, etc.)

### Insertion behaviour

When the Blender addon inserts a product from the library into an active project, it should:

1. Read the `product.ifc` file using IfcOpenShell
2. Extract the product type and occurrence
3. Create corresponding type and occurrence in the active project's IFC file
4. Assign the occurrence to the active storey (`IfcBuildingStorey`)
5. Place at the 3D cursor position with the object's origin as the insertion point
6. Copy all property sets from the library object to the project object
7. Assign classifications from the metadata if not already in the IFC file

---

## 7. Category Templates (_templates/)

Each template provides a starting-point `properties` section tailored to the product category. When a user creates a new product via the import wizard, the UI pre-populates fields from the relevant template.

Example: `_templates/sanitaryware.json`

```json
{
  "template_for": "sanitaryware",
  "ifc_defaults": {
    "class": "IfcSanitaryTerminal",
    "predefined_types": [
      "BATH", "BIDET", "CISTERN", "SHOWER", "SINK",
      "SANITARYFOUNTAIN", "TOILETPAN", "URINAL",
      "WASHHANDBASIN", "WCSEAT"
    ]
  },
  "property_fields": [
    { "key": "material", "label": "Material", "type": "select",
      "options": ["Vitreous china", "Fireclay", "Ceramic", "Stainless steel", "Solid surface", "Acrylic"] },
    { "key": "colour", "label": "Colour", "type": "text", "default": "White" },
    { "key": "mounting", "label": "Mounting Type", "type": "select",
      "options": ["Wall-hung", "Pedestal", "Semi-pedestal", "Countertop", "Semi-recessed", "Inset", "Floor-standing"] },
    { "key": "tap_holes", "label": "Tap Holes", "type": "integer", "default": 1 },
    { "key": "overflow", "label": "Has Overflow", "type": "boolean", "default": true },
    { "key": "outlet_diameter_mm", "label": "Waste Outlet Diameter (mm)", "type": "integer", "default": 32 },
    { "key": "trap_type", "label": "Trap Type", "type": "select",
      "options": ["Bottle", "P-trap", "S-trap", "Integral", "None supplied"] },
    { "key": "water_supply", "label": "Water Supply", "type": "select",
      "options": ["Mixer tap", "Pillar taps", "Sensor tap", "None supplied"] }
  ],
  "dimension_fields": [
    { "key": "width_mm", "label": "Width (mm)", "required": true },
    { "key": "depth_mm", "label": "Depth / Projection (mm)", "required": true },
    { "key": "height_mm", "label": "Height (mm)", "required": true },
    { "key": "weight_kg", "label": "Weight (kg)", "required": false }
  ],
  "compliance_fields": [
    { "key": "doc_m", "label": "Doc M Compliant", "type": "boolean" },
    { "key": "wras_approved", "label": "WRAS Approved", "type": "boolean" },
    { "key": "standards", "label": "Standards", "type": "text_list",
      "suggestions": ["BS 5506", "EN 14688", "EN 997", "EN 31", "EN 111"] }
  ]
}
```

---

## 8. Discovery and Search

The MCP server and Blender addon both need to discover and search the library. The approach is deliberately simple:

### Discovery
On startup (or when the library path changes), walk the folder tree and read every `product.json` file. Build an in-memory index. For a library of a few hundred products this takes milliseconds — no database needed.

### Search
The in-memory index supports:

- **Browse by category:** Follow the `categories` tree from `library.json`
- **Text search:** Fuzzy match across `identity.name`, `identity.manufacturer`, `identity.description`, `category.tags`
- **Filter by dimension:** "basins under 450mm wide" → filter on `dimensions.width_mm < 450`
- **Filter by tag:** "doc-m" → filter on `category.tags` contains "doc-m"
- **Filter by classification:** "Uniclass Pr_40_20_96_95" → match on `classification.uniclass_2015.code`

### MCP Tools

The MCP server exposes:

- `search_product_library(query, category?, tags?, max_width?, max_depth?)` — returns matching products with metadata
- `get_product_details(slug)` — returns full metadata for a specific product
- `list_categories()` — returns the category tree for browsing
- `insert_product(slug, x, y, z, rotation?)` — inserts product into active Bonsai project (calls IfcOpenShell via Bonsai MCP)

---

## 9. Starter Products — Recommended First Batch

To make the library immediately useful in practice, the following products represent the core items most frequently placed in residential and small commercial projects:

### Sanitaryware (priority — most complex geometry, most frequently specified)
- Wall-hung basin 500mm (accessible / Doc M)
- Wall-hung basin 450mm (standard cloakroom)
- Close-coupled WC pan
- Back-to-wall WC pan
- Concealed cistern
- Shower tray 900×900mm quadrant

### Accessibility
- Doc M pack (basin + WC + grab rails as a grouped set)
- Grab rail 600mm straight
- Grab rail 450mm cranked/angled

### Ironmongery (simple geometry, high reuse)
- Lever handle on rose (generic)
- Pull handle (generic)
- Door closer (generic overhead)
- Barrel bolt

### Furniture (for kitchen and FF&E layouts)
- Generic base unit 600mm
- Generic wall unit 600mm
- Generic tall unit 600mm
- Desk 1600×800mm

---

## 10. Versioning and Collaboration

### Git workflow
The library root is a Git repository. Each product addition or modification is a commit. The `.gitignore` excludes `source/original.*` files over a configurable size limit (STEP files can be large) — these can be stored in Git LFS or excluded entirely if the licence doesn't permit redistribution.

### Contributing
A `CONTRIBUTING.md` at the library root explains:
- How to add a new product (folder structure, required files)
- Metadata conventions (naming, tagging)
- Geometry conventions (origin, orientation, units, LOD)
- Quality checklist (does it open in Bonsai? Are property sets populated? Is the thumbnail rendered?)

### Licensing
- **Library structure and tooling:** MIT licence
- **Product IFC files authored from scratch:** CC BY 4.0 (attribution required)
- **Product IFC files derived from manufacturer geometry:** As per source licence (recorded in `source/source.json`). Products with incompatible licences are marked in metadata and excluded from public distribution

---

## 11. Future Considerations

- **Parametric products:** Some products (kitchen units, generic windows) could be parametrically generated rather than stored as fixed geometry. IfcOpenShell's Python API supports this natively
- **LOD variants:** Multiple geometry representations per product (schematic, design, detailed) stored as separate `IfcShapeRepresentation` entries within the same IFC file
- **Thumbnail auto-generation:** A Blender script that opens each `product.ifc`, sets up a standard camera/lighting rig, renders a 256×256 thumbnail, and saves it as `thumbnail.png`
- **Online registry:** A simple static website (Hugo or similar) that indexes the library and displays products with thumbnails, filterable by category — making it discoverable without cloning the repo
- **IDS validation:** Using IfcOpenShell's `ifctester` to validate that each product meets a defined Information Delivery Specification before it's accepted into the library
