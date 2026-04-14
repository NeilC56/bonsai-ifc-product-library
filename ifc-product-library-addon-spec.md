# IFC Product Library — Blender Addon Specification

**Version:** 0.1 Draft
**Date:** April 2026
**Author:** Neil (with Claude)
**Addon name:** `ifc_product_library` (working title: "Product Library for Bonsai")
**Depends on:** Bonsai (IfcOpenShell), Blender 4.2+

---

## 1. Overview

A Blender sidebar addon that provides three core functions:

1. **Browse & Insert** — navigate a local IFC product library and insert objects into the active Bonsai project with one click
2. **Import & Convert** — take any supported 3D geometry file, clean it up, assign IFC classification and properties, and save it to the library
3. **Search** — find products by name, category, tag, dimension, or classification — locally and optionally via MCP/AI

---

## 2. Supported Import Formats

Blender natively imports all of these — no external tools required:

| Format | Extension(s) | Typical source | Notes |
|--------|-------------|----------------|-------|
| Wavefront OBJ | `.obj` | GrabCAD, free 3D libraries | No animation, preserves quads. Most common free format |
| STL | `.stl` | 3D printing sites, manufacturer CAD | Geometry only, no colour/material. Triangulated |
| glTF / GLB | `.gltf`, `.glb` | Web 3D, converted from STEP via Mayo | Modern, efficient. Recommended intermediate from STEP |
| FBX | `.fbx` | Game assets, some manufacturers | Autodesk format, good material support |
| Collada | `.dae` | Legacy exchange format | Being deprecated in Blender, but still works |
| PLY | `.ply` | 3D scans, point clouds | Good for scanned objects |
| 3DS | `.3ds` | Older 3D models | Legacy format, limited |
| X3D | `.x3d`, `.wrl` | Web 3D, VRML legacy | ISO standard |
| USD | `.usd`, `.usda`, `.usdc` | Pixar/film pipeline | Growing support |
| DXF | `.dxf` | AutoCAD 2D/3D | Via addon, limited 3D support |
| IFC | `.ifc` | Manufacturer BIM downloads, Bonsai | Direct — no conversion needed, just validate and catalogue |
| Blender | `.blend` | Other Blender users | Append objects from .blend files |

### STEP files (requires external conversion)

STEP (`.step`, `.stp`) is the most important CAD interchange format but Blender cannot import it natively. The addon should detect STEP files and guide the user through conversion:

- **Recommended route:** Mayo (open source) → export as glTF → import to Blender
- **Alternative:** FreeCAD → export as OBJ or STL → import to Blender
- **Future:** If a Blender STEP import addon becomes available, integrate directly

The addon UI should show a helpful message when a STEP file is selected: *"STEP files need conversion before import. Would you like to open this file in Mayo for conversion to glTF?"* with a button to launch Mayo if installed, or a link to download it.

---

## 3. Addon Architecture

```
ifc_product_library/
│
├── __init__.py                  # Addon registration, preferences, panel registration
├── preferences.py               # Addon preferences (library path, Mayo path, MCP settings)
│
├── panels/
│   ├── library_browser.py       # Main sidebar panel — browse & insert
│   ├── import_wizard.py         # Import new product wizard panels
│   └── search_panel.py          # Search bar and results
│
├── operators/
│   ├── browse_ops.py            # Navigate categories, expand/collapse
│   ├── insert_ops.py            # Insert product into active IFC project
│   ├── import_ops.py            # Import geometry file, run cleanup
│   ├── convert_ops.py           # Assign IFC class, populate properties, save to library
│   ├── search_ops.py            # Search library index
│   ├── thumbnail_ops.py         # Generate thumbnail renders
│   └── validate_ops.py          # Validate IFC file before cataloguing
│
├── core/
│   ├── library_index.py         # Walk folder tree, read product.json files, build index
│   ├── metadata.py              # Read/write product.json, validate against schema
│   ├── templates.py             # Load category templates for property forms
│   ├── ifc_utils.py             # IfcOpenShell helpers — extract type, merge into project
│   └── format_detect.py         # Detect file format, route to appropriate importer
│
├── mcp/
│   ├── server.py                # MCP server exposing library tools to Claude
│   └── tools.py                 # MCP tool definitions (search, insert, list_categories)
│
└── resources/
    ├── icons/                   # Category icons for the sidebar
    └── default_templates/       # Shipped category templates (sanitaryware, ironmongery etc.)
```

---

## 4. UI Design — Library Browser Panel

Located in the **3D Viewport sidebar** (N-panel), under a tab called **"Product Library"**.

### 4.1 Panel layout (top to bottom)

```
┌─────────────────────────────────┐
│ 🔍 [Search products...        ] │  ← Text search field
├─────────────────────────────────┤
│ 📁 Library: Neil's Practice     │  ← Current library name
│    Products: 47                 │  ← Total product count
├─────────────────────────────────┤
│ ▶ Sanitaryware (12)            │  ← Expandable category
│ ▼ Ironmongery (8)              │  ← Expanded category
│   ├ Door Handles (3)           │
│   ├ Hinges (2)                 │
│   ├ Closers (2)                │
│   └ Locks (1)                  │
│ ▶ Doors (6)                    │
│ ▶ Windows (4)                  │
│ ▶ Insulation (5)               │
│ ▶ Furniture (7)                │
│ ▶ Accessibility (5)            │
├─────────────────────────────────┤
│ ┌─────────────┐                │
│ │  [thumbnail] │ Contour 21    │  ← Selected product
│ │             │ Armitage Shanks │
│ └─────────────┘ 500×410×185mm  │
│                                 │
│ IFC: IfcSanitaryTerminal       │
│ Uniclass: Pr_40_20_96_95      │
│ Tags: accessible, doc-m        │
│                                 │
│ [ INSERT INTO MODEL ]          │  ← Primary action button
│ [ View Details ] [ Edit ]      │  ← Secondary actions
├─────────────────────────────────┤
│ [ + Add New Product ]          │  ← Opens import wizard
│ [ ⚙ Library Settings ]        │
└─────────────────────────────────┘
```

### 4.2 Interaction behaviour

- **Category tree:** Click to expand/collapse. Shows product count per category. Populated from `library.json`.
- **Product list:** When a category leaf is selected, shows all products in that folder. Each product shows name and manufacturer.
- **Product detail:** Clicking a product populates the detail area with thumbnail, dimensions, IFC class, classification, and tags.
- **Insert button:** Places the product at the 3D cursor position in the active Bonsai IFC project. Assigned to the active storey. If no IFC project is active, shows a warning.
- **Search:** Typing in the search field filters the product list in real time across name, manufacturer, description, and tags.

---

## 5. UI Design — Import Wizard

Triggered by the **"+ Add New Product"** button. Presented as a sequence of sub-panels in the sidebar, or optionally as a popup dialog.

### Step 1: Select geometry source

```
┌─────────────────────────────────┐
│ IMPORT NEW PRODUCT — Step 1/4  │
│ Select Geometry Source          │
├─────────────────────────────────┤
│                                 │
│ ( ) Import from file            │
│     [Browse...] no file selected│
│                                 │
│ ( ) Use selected Blender object │
│     (select an object in the    │
│      viewport first)            │
│                                 │
│ ( ) Import existing IFC file    │
│     [Browse...] no file selected│
│     (skips to Step 4 — just     │
│      add metadata)              │
│                                 │
│ Detected format: —              │
│                                 │
│          [ Next → ]             │
└─────────────────────────────────┘
```

**Format detection:** When a file is selected, `format_detect.py` identifies the format from the extension and shows it. If it's a STEP file, shows the Mayo conversion guidance. If it's an IFC file, skips directly to metadata entry (Step 4).

**"Use selected Blender object"** allows the user to model something directly in Blender's standard modelling tools, then feed it into the library pipeline. This is the route for hand-authored objects.

### Step 2: Geometry cleanup

```
┌─────────────────────────────────┐
│ IMPORT NEW PRODUCT — Step 2/4  │
│ Clean Up Geometry               │
├─────────────────────────────────┤
│                                 │
│ Imported objects: 42            │
│ Total vertices: 128,450        │
│                                 │
│ ☑ Remove small parts           │
│   Threshold: [5] mm            │
│   (removes screws, bolts etc.) │
│                                 │
│ ☑ Merge into single object     │
│   (combine all parts into one  │
│    mesh for simpler IFC object)│
│                                 │
│ ☐ Simplify (decimate)          │
│   Target: [10000] faces        │
│   (reduce polygon count for    │
│    lighter BIM models)          │
│                                 │
│ ☑ Convert to mesh              │
│   (apply modifiers, resolve    │
│    instances — required for     │
│    IFC assignment)              │
│                                 │
│ ☑ Set origin to base centre    │
│   ( ) Base centre (floor items)│
│   ( ) Back centre (wall items) │
│   ( ) Geometric centre         │
│                                 │
│ Preview: [viewport shows the   │
│  imported geometry with small   │
│  parts highlighted in red]      │
│                                 │
│   [ ← Back ] [ Next → ]       │
└─────────────────────────────────┘
```

**Key operations (all non-destructive until confirmed):**
- **Remove small parts:** Uses bounding box dimensions to identify and delete objects below threshold. Highlighted in red in viewport before deletion.
- **Merge:** Joins all remaining objects into a single mesh. Essential for product objects that should be a single IFC entity.
- **Simplify:** Applies a Decimate modifier to reduce polygon count. Preview in viewport.
- **Convert to mesh:** Applies all modifiers, makes instances real. Required before Bonsai can assign an IFC class.
- **Set origin:** Moves the object origin to a sensible insertion point. Wall-mounted items default to back-centre; floor items to base-centre.

### Step 3: IFC Classification

```
┌─────────────────────────────────┐
│ IMPORT NEW PRODUCT — Step 3/4  │
│ IFC Classification              │
├─────────────────────────────────┤
│                                 │
│ Category: [Sanitaryware    ▼]  │
│ Subcategory: [Basins       ▼]  │
│ Sub-sub: [Wall-hung        ▼]  │
│                                 │
│ ─── Auto-filled from category ──│
│                                 │
│ IFC Class: IfcSanitaryTerminal │
│ Predefined Type: WASHHANDBASIN │
│                                 │
│ (These are set automatically   │
│  from the category template.   │
│  Override if needed.)           │
│                                 │
│ IFC Version: [IFC4         ▼]  │
│                                 │
│   [ ← Back ] [ Next → ]       │
└─────────────────────────────────┘
```

**Category selection drives everything:** When the user picks "Sanitaryware → Basins → Wall-hung", the template auto-fills the IFC class, predefined type, and determines which property fields appear in Step 4.

### Step 4: Product Metadata

```
┌─────────────────────────────────┐
│ IMPORT NEW PRODUCT — Step 4/4  │
│ Product Information             │
├─────────────────────────────────┤
│                                 │
│ ─── Identity ──────────────── │
│ Name: [Contour 21 Basin 500mm ]│
│ Manufacturer: [Armitage Shanks ]│
│ Model Number: [S0439          ]│
│ Product URL: [https://...     ]│
│ Description: [Wall-hung basin  │
│  with overflow, suitable for...]│
│                                 │
│ ─── Dimensions ────────────── │
│ Width:  [500 ] mm              │
│ Depth:  [410 ] mm              │
│ Height: [185 ] mm              │
│ Weight: [12.5] kg              │
│                                 │
│ ─── Properties (Sanitaryware) ─│
│ Material: [Vitreous china  ▼]  │
│ Colour: [White              ]  │
│ Mounting: [Wall-hung       ▼]  │
│ Tap Holes: [1               ]  │
│ Overflow: [☑]                  │
│ Outlet Ø: [32] mm             │
│                                 │
│ ─── Classification ──────────  │
│ Uniclass: [Pr_40_20_96_95   ] │
│ OmniClass: [23-31 19 11     ] │
│                                 │
│ ─── Compliance ──────────────  │
│ Doc M: [☑]                     │
│ Standards: [BS 5506, EN 14688 ]│
│                                 │
│ ─── Tags ────────────────────  │
│ [accessible] [doc-m]           │
│ [commercial] [healthcare]      │
│ [+ Add tag]                    │
│                                 │
│ ─── Provenance ──────────────  │
│ Geometry source: [TraceParts  ]│
│ Source licence: [Free download ]│
│                                 │
│ [ ← Back ]                     │
│ [ 💾 SAVE TO LIBRARY ]         │
│ [ 💾 Save & Insert into Model ]│
└─────────────────────────────────┘
```

**Save actions:**
- **Save to Library:** Creates the folder, writes `product.ifc` (via IfcOpenShell — creates IFC project wrapper, assigns class, writes geometry and property sets), writes `product.json`, generates `thumbnail.png` (automated viewport render), optionally copies source file to `source/`.
- **Save & Insert:** Does the above, then immediately inserts the product into the active Bonsai project.

---

## 6. Insert Operation — Technical Detail

When the user clicks "INSERT INTO MODEL", the addon performs these steps:

```python
# Pseudocode for insert operation

def insert_product(library_path, product_slug, location, rotation=0):
    """Insert a product from the library into the active Bonsai IFC project."""

    # 1. Read the library product's IFC file
    product_ifc_path = os.path.join(library_path, product_slug, "product.ifc")
    product_model = ifcopenshell.open(product_ifc_path)

    # 2. Get the active project's IFC file (via Bonsai)
    from bonsai.bim.ifc import IfcStore
    project_model = IfcStore.get_file()

    # 3. Extract the product type and occurrence from the library file
    # (Each library product.ifc contains one type + one occurrence)
    product_types = product_model.by_type("IfcTypeProduct")
    product_occurrences = product_model.by_type("IfcProduct")

    # 4. Copy the type definition into the project (if not already present)
    #    This uses IfcOpenShell's object copying utilities
    copied_type = ifcopenshell.api.run("project.append_asset",
        project_model,
        library=product_model,
        element=product_types[0])

    # 5. Create an occurrence instance in the project
    occurrence = ifcopenshell.api.run("root.create_entity",
        project_model,
        ifc_class=product_occurrences[0].is_a())

    # 6. Assign to the active storey
    active_storey = get_active_storey(project_model)  # from Bonsai context
    ifcopenshell.api.run("spatial.assign_container",
        project_model,
        relating_structure=active_storey,
        products=[occurrence])

    # 7. Set placement at 3D cursor location
    matrix = calculate_placement_matrix(location, rotation)
    ifcopenshell.api.run("geometry.edit_object_placement",
        project_model,
        product=occurrence,
        matrix=matrix)

    # 8. Copy property sets from library object to project object
    copy_psets(product_model, product_occurrences[0],
               project_model, occurrence)

    # 9. Assign type relationship
    ifcopenshell.api.run("type.assign_type",
        project_model,
        related_objects=[occurrence],
        relating_type=copied_type)

    # 10. Refresh Bonsai viewport
    IfcStore.reload_file()

    return occurrence
```

---

## 7. MCP Server Integration

The MCP server runs alongside the Blender addon and exposes the library to Claude or other LLM clients. It communicates with Blender via the same TCP socket mechanism used by the existing Bonsai MCP.

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_product_library` | `query`, `category?`, `tags?`, `max_width_mm?`, `max_depth_mm?`, `manufacturer?` | Fuzzy search across library metadata. Returns list of matching products with key details |
| `get_product_details` | `slug` | Returns full product.json metadata for a specific product |
| `list_categories` | — | Returns the category tree from library.json |
| `list_products_in_category` | `category_path` | Returns all products in a category |
| `insert_product` | `slug`, `x`, `y`, `z`, `rotation_degrees?` | Inserts product into active Bonsai project at specified coordinates |
| `get_library_stats` | — | Returns total products, categories, last modified date |

### Example MCP conversation

```
User: "I need a Doc M compliant wall-hung basin for the accessible WC on the ground floor"

Claude: [calls search_product_library(query="basin wall-hung", tags=["doc-m"])]
  → Returns: Contour 21 Basin 500mm (Armitage Shanks)

Claude: "I found the Armitage Shanks Contour 21 500mm wall-hung basin in your library.
         It's Doc M compliant, 500×410×185mm. Shall I insert it?"

User: "Yes, place it on the back wall at x=2.5, y=0.1, z=0.85"

Claude: [calls insert_product(slug="contour-21-500mm", x=2500, y=100, z=850)]
  → Product inserted into active storey
```

---

## 8. Thumbnail Auto-Generation

When a product is saved to the library, the addon automatically renders a thumbnail:

1. Position camera at a standard 3/4 view (front-right, slightly above)
2. Set up simple three-point studio lighting
3. White or transparent background
4. Render at 256×256px using Eevee (fast)
5. Save as `thumbnail.png` in the product folder

This can also be run as a batch operation across the entire library via an operator: **"Regenerate All Thumbnails"** in Library Settings.

---

## 9. Addon Preferences

Accessible via Edit → Preferences → Add-ons → IFC Product Library:

| Setting | Default | Description |
|---------|---------|-------------|
| Library Path | `~/ifc-product-library/` | Root folder of the product library |
| Mayo Path | (auto-detect) | Path to Mayo executable for STEP conversion |
| Default IFC Version | IFC4 | IFC version for new products |
| Default Classification | Uniclass 2015 | Primary classification system |
| Thumbnail on Save | ✓ | Auto-generate thumbnail when saving product |
| MCP Server Enabled | ✗ | Enable MCP server for AI integration |
| MCP Server Port | 9877 | TCP port for MCP server (avoids conflict with Bonsai MCP on 9876) |
| Small Part Threshold | 5mm | Default threshold for "remove small parts" cleanup |
| Default Origin Mode | Back centre | Default origin placement for new products |

---

## 10. Development Phases

### Phase 1 — Browse & Insert (MVP)
- Library index builder (walk folders, read product.json)
- Sidebar panel with category tree
- Product detail display (no thumbnails yet — just text)
- Insert operator using IfcOpenShell
- Works with manually-created library entries

### Phase 2 — Import Wizard
- File browser with format detection
- Geometry cleanup operators (remove small parts, merge, decimate, set origin)
- IFC classification panel with category templates
- Property metadata form
- Save to library operator (writes product.ifc and product.json)
- STEP file handling guidance (Mayo integration)

### Phase 3 — Polish & Thumbnails
- Thumbnail auto-generation on save
- Thumbnail display in product list and detail panel
- Batch thumbnail regeneration
- Search with real-time filtering
- Library validation tool (check all products for completeness)

### Phase 4 — MCP Integration
- MCP server exposing library tools
- Claude integration for natural language search and insertion
- AI-assisted metadata population (Claude suggests IFC class, Uniclass code, properties from product name/description)

### Phase 5 — Community & Sharing
- Git integration for library versioning
- Import/export library subsets
- Online registry browser (Hugo static site displaying library contents)
- Contribution workflow documentation

---

## 11. Key Design Decisions

**Why a sidebar panel, not a popup?**
Sidebar panels persist — you can browse the library while working on your model, switch between products, and keep the context visible. Popups are modal and block workflow.

**Why not integrate into Bonsai's existing panels?**
Bonsai's panels are already dense with IFC data management. A separate tab keeps the library browsable without cluttering the BIM authoring workspace. It also allows the addon to be developed and released independently of Bonsai's release cycle.

**Why store products as individual IFC files, not a single library IFC?**
Individual files are simpler to manage, version, share, and validate. A single library file would be fragile (corruption affects everything) and harder to update incrementally. IfcOpenShell's `project.append_asset` handles the merge-on-insert cleanly.

**Why JSON sidecars, not embedded IFC properties only?**
The JSON sidecar provides fast indexing without parsing IFC files, human-readable metadata, fields that don't map to IFC (like provenance, source licence, tags), and a schema that's easier to validate and extend than IFC property sets.

**Why support so many import formats?**
Because the geometry sources are diverse — OBJ from GrabCAD, STEP from TraceParts, STL from 3D printing sites, glTF from web sources, IFC from manufacturer portals, FBX from game asset libraries. The more formats we accept, the more products can enter the library without friction.
