# Changelog

All notable changes to IFC Product Library for Bonsai are documented here.

---

## Phase 3 — Array Insert + Span Advisory

**Array Insert**
- New `ARRAY` placement mode for beam and joist products (structural steel, metal web joists, solid timber joists, engineered I-joists)
- Enter beam length, centre-to-centre spacing, span length, and start/end wall offsets
- Live preview in the panel: joist count, spacing, odd-gap size and side — before inserting
- `INSERT ARRAY` button places a full row of separate IFC entities in one click, each with its own `GlobalId`, placement matrix, and mesh representation
- Geometry is scaled to the requested beam length along the long axis and rotated to run perpendicular to the array direction
- Preset buttons for common spacings (400 / 450 / 600 mm) and wall bearing offsets (masonry 20 mm, timber 10 mm)
- Odd-gap side toggle: choose whether the remainder gap sits at the start or end of the run

**Span Advisory**
- Collapsible section within Array Insert that cross-references the current span/spacing against a manufacturer span table
- Span tables are JSON files stored in `<library>/span-tables/`; multiple tables can be present and selected by button
- Load case selector populated from the active table (e.g. domestic floor, light commercial)
- Results table shows each section depth, top chord size, maximum clear span, and a status indicator (Short / OK / Generous)
- Prominent disclaimer text is always visible when the advisory is expanded — output is for preliminary guidance only
- Module-level cache avoids re-parsing JSON on every panel redraw; invalidated when the library folder changes

**New files:** `ifc_product_library/operators/array_insert_ops.py`, `ifc_product_library/core/span_tables.py`

**Modified files:** `ifc_product_library/__init__.py`, `ifc_product_library/props.py`, `ifc_product_library/panels/library_browser.py`

---

## Phase 2 — Import Wizard

- Four-step import wizard accessible from **+ Add New Product** in the panel
- Step 1 — Geometry source: import from file (OBJ, STL, glTF, FBX, DAE, PLY, IFC, and others), use already-selected Blender objects, or follow the STEP → Mayo → glTF conversion path
- Step 2 — Geometry cleanup: automatic scale detection and one-click mm→m correction, face count traffic light (green / amber / red), BIM decimation with preview and revert, merge, apply modifiers, set origin to base-centre or back-centre
- Step 3 — IFC classification: category picker auto-fills IFC class, predefined type, and the relevant property field set
- Step 4 — Metadata form: name, manufacturer, model number, pre-filled dimensions from bounding box, category-specific property fields, Uniclass classification, compliance flags
- **Save to Library** writes `product.ifc` and `product.json`; **Save & Insert** also places the object at the 3D cursor
- Unit detection: bounding box heuristic warns when imported geometry appears to be in mm rather than metres
- Face count protection: decimate is offered but never applied silently

**New files:** `ifc_product_library/operators/import_ops.py`, `ifc_product_library/operators/convert_ops.py`, `ifc_product_library/panels/import_wizard.py`, `ifc_product_library/core/wizard_state.py`, `ifc_product_library/core/format_detect.py`, `ifc_product_library/core/metadata.py`, `ifc_product_library/core/ifc_writer.py`, `ifc_product_library/core/templates.py`

---

## Phase 1 — Browse & Insert

- Sidebar panel in the 3D Viewport N-panel (tab: **Product Library**)
- Expandable category tree populated from `library.json`: Sanitaryware, Ironmongery, Doors, Windows, Insulation, Furniture, Accessibility, Structural
- Empty categories are hidden automatically
- Real-time text search across product name, manufacturer, description, and tags (results capped at 30)
- Product detail box: identity, dimensions, IFC class and predefined type, Uniclass code, tags, key properties, Doc M flag
- **INSERT INTO MODEL** button: tessellates the product IFC geometry, creates an `IfcElement` occurrence with the correct class and predefined type, assigns a mesh representation, places it at the 3D cursor, and assigns it to the active storey
- Draw-time lazy-load: if the library path is set in preferences but the library hasn't loaded yet, the panel loads it on first draw
- Refresh button reloads `library.json` and all `product.json` files without restarting Blender

**New files:** all files in `ifc_product_library/` (initial project)
