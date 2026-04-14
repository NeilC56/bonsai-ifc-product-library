"""Insert operator — places a library product into the active Bonsai IFC project.

Cross-schema strategy
---------------------
Library products are IFC2X3 (BIMobject source); the target Bonsai project is
typically IFC4.  ifcopenshell's project.append_asset cannot copy entities
between schemas (it fails on attribute differences like IfcPerson.Identification).

Instead we:
  1. Tessellate the IFC2X3 geometry with ifcopenshell.geom.create_shape()
     → flat numpy arrays of vertices (metres) and triangle indices
  2. Create a brand-new IFC4 IfcSanitaryTerminal (or whatever class) in the
     target project using the correct class and predefined type from product.json
  3. Build a fresh IfcPolygonalFaceSet representation via
     geometry.add_mesh_representation — this handles IFC4 vs IFC2X3 and
     unit conversion (SI metres → project units) automatically
  4. Assign, place, and container-assign the new occurrence
  5. Build a Blender mesh from the same numpy arrays so the geometry appears
     immediately in the 3D viewport without requiring a Bonsai project reload
"""

import os
import bpy
from ..core import library_index


class IFCLIB_OT_InsertProduct(bpy.types.Operator):
    """Insert the selected library product into the active Bonsai IFC project
    at the 3D cursor position."""
    bl_idname = "ifclib.insert_product"
    bl_label = "Insert Product into Model"
    bl_description = (
        "Append the selected product into the active Bonsai IFC project "
        "and place an instance at the 3D cursor"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # ── Validate selection ─────────────────────────────────────────────
        state = library_index.get_ui_state()
        slug = state["selected_product_slug"]
        if not slug:
            self.report({"WARNING"}, "No product selected — click a product name first")
            return {"CANCELLED"}

        product = library_index.get_product(slug)
        if not product:
            self.report({"ERROR"}, f"Product '{slug}' not found in index")
            return {"CANCELLED"}

        # ── Require Bonsai ─────────────────────────────────────────────────
        try:
            from bonsai.bim.ifc import IfcStore
        except ImportError:
            self.report(
                {"ERROR"},
                "Bonsai (BlenderBIM) is not installed. "
                "Install Bonsai to insert products into IFC projects.",
            )
            return {"CANCELLED"}

        ifc_file = IfcStore.get_file()
        if ifc_file is None:
            self.report(
                {"ERROR"},
                "No active IFC project. Open or create a Bonsai project first.",
            )
            return {"CANCELLED"}

        # ── Locate product.ifc ─────────────────────────────────────────────
        folder = product.get("_folder_path", "")
        product_ifc_path = os.path.join(folder, "product.ifc")
        if not os.path.exists(product_ifc_path):
            self.report({"ERROR"}, f"product.ifc not found: {product_ifc_path}")
            return {"CANCELLED"}

        try:
            return self._insert(context, ifc_file, product_ifc_path, product)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.report({"ERROR"}, f"Insert failed: {exc}")
            return {"CANCELLED"}

    # -----------------------------------------------------------------------

    def _insert(self, context, ifc_file, product_ifc_path: str, product: dict):
        import ifcopenshell
        import ifcopenshell.api
        import numpy as np

        name = product.get("identity", {}).get("name", "Product")

        # ── 1. Tessellate the IFC2X3 source geometry ───────────────────────
        verts, faces = _extract_mesh(product_ifc_path)
        if verts is None or len(faces) == 0:
            self.report({"ERROR"}, "Could not tessellate geometry from product.ifc")
            return {"CANCELLED"}

        print(
            f"IFC Product Library: tessellated '{name}' — "
            f"{len(verts)} verts, {len(faces)} triangles"
        )

        # ── 2. Find the Body representation context in the target project ──
        body_context = _find_body_context(ifc_file)
        if body_context is None:
            self.report(
                {"ERROR"},
                "No Body representation context found in the IFC project. "
                "Make sure the project has a 3D Model context.",
            )
            return {"CANCELLED"}

        # ── 3. Build a fresh IFC4 mesh representation ──────────────────────
        # Vertices from the geom engine are in the source model's units.
        # BIMobject IFC2X3 files declare LENGTHUNIT = METRE, confirmed by
        # bounding-box values matching the product.json mm dimensions ÷ 1000.
        # add_mesh_representation with unit_scale=None treats vertices as SI
        # metres and converts to the target project's units automatically.
        try:
            representation = ifcopenshell.api.run(
                "geometry.add_mesh_representation",
                ifc_file,
                context=body_context,
                vertices=[verts.tolist()],   # one IfcRepresentationItem
                faces=[faces.tolist()],
                # unit_scale omitted → vertices treated as SI metres
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Could not create geometry representation: {exc}")
            return {"CANCELLED"}

        # ── 4. Create a new occurrence in the target project's schema ──────
        ifc_class = product.get("ifc", {}).get("class", "IfcBuildingElementProxy")
        occurrence = _create_occurrence(ifc_file, ifc_class, name)
        if occurrence is None:
            self.report({"ERROR"}, f"Could not create IFC occurrence (class: {ifc_class})")
            return {"CANCELLED"}

        # Apply predefined type from metadata (correct value, not NOTDEFINED)
        predefined_type = product.get("ifc", {}).get("predefined_type", "")
        if predefined_type and predefined_type not in ("NOTDEFINED", "USERDEFINED"):
            try:
                occurrence.PredefinedType = predefined_type
            except Exception:
                pass

        # ── 5. Assign the representation ───────────────────────────────────
        ifcopenshell.api.run(
            "geometry.assign_representation",
            ifc_file,
            product=occurrence,
            representation=representation,
        )

        # ── 6. Placement at 3D cursor ──────────────────────────────────────
        _set_placement(ifc_file, occurrence, context.scene.cursor.location)

        # ── 7. Assign to building storey ───────────────────────────────────
        storey = _get_active_storey(context, ifc_file)
        if storey:
            try:
                ifcopenshell.api.run(
                    "spatial.assign_container",
                    ifc_file,
                    relating_structure=storey,
                    products=[occurrence],
                )
            except Exception as exc:
                print(f"IFC Product Library: storey assignment error: {exc}")

        # ── 8. Create a Blender mesh object for immediate viewport display ─
        _create_blender_mesh_object(context, ifc_file, occurrence, product, verts, faces)

        self.report({"INFO"}, f"Inserted '{name}' at 3D cursor")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _extract_mesh(product_ifc_path: str):
    """Open an IFC file and return (verts, faces) as numpy arrays.

    verts  — shape (N, 3), float64, in the source model's length units
    faces  — shape (M, 3), int32, triangle vertex indices

    Returns (None, None) on failure.
    """
    import ifcopenshell
    import ifcopenshell.geom
    import numpy as np

    try:
        product_model = ifcopenshell.open(product_ifc_path)
    except Exception as exc:
        print(f"IFC Product Library: could not open product.ifc: {exc}")
        return None, None

    settings = ifcopenshell.geom.settings()
    settings.set("WELD_VERTICES", False)

    # Find the first occurrence that carries a geometric representation
    occurrence = None
    for cls in ("IfcFlowTerminal", "IfcSanitaryTerminal", "IfcFurnishingElement", "IfcProduct"):
        try:
            for el in product_model.by_type(cls):
                if el.Representation:
                    occurrence = el
                    break
        except RuntimeError:
            continue
        if occurrence:
            break

    if occurrence is None:
        print("IFC Product Library: no occurrence with geometry found in product.ifc")
        return None, None

    try:
        shape = ifcopenshell.geom.create_shape(settings, occurrence)
        geo   = shape.geometry
        verts = np.array(geo.verts, dtype=np.float64).reshape(-1, 3)
        faces = np.array(geo.faces, dtype=np.int32).reshape(-1, 3)
        return verts, faces
    except Exception as exc:
        print(f"IFC Product Library: tessellation error: {exc}")
        return None, None


def _find_body_context(ifc_file):
    """Return the Body/Model IfcGeometricRepresentationSubContext in *ifc_file*.

    Falls back to any 3D context if no subcontext named 'Body' exists.
    """
    # Prefer an explicit Body subcontext
    for ctx in ifc_file.by_type("IfcGeometricRepresentationSubContext"):
        if ctx.ContextIdentifier == "Body":
            return ctx

    # Fall back to the first 3D geometric context
    for ctx in ifc_file.by_type("IfcGeometricRepresentationContext"):
        if not ctx.is_a("IfcGeometricRepresentationSubContext"):
            if getattr(ctx, "CoordinateSpaceDimension", 0) == 3:
                return ctx

    return None


# ---------------------------------------------------------------------------
# IFC occurrence helpers
# ---------------------------------------------------------------------------

def _create_occurrence(ifc_file, ifc_class: str, name: str):
    """Create an IFC occurrence entity, falling back gracefully on schema mismatches.

    product.json records the IFC4 class name (IfcSanitaryTerminal). If the
    target project is IFC2X3 that class doesn't exist; fall back to
    IfcFlowTerminal, then IfcBuildingElementProxy.
    """
    import ifcopenshell.api

    fallbacks = {
        "IfcSanitaryTerminal": ["IfcFlowTerminal", "IfcBuildingElementProxy"],
        "IfcFlowTerminal":     ["IfcBuildingElementProxy"],
    }
    candidates = [ifc_class] + fallbacks.get(ifc_class, ["IfcBuildingElementProxy"])

    for cls in candidates:
        try:
            return ifcopenshell.api.run(
                "root.create_entity",
                ifc_file,
                ifc_class=cls,
                name=name,
            )
        except Exception:
            continue
    return None


def _set_placement(ifc_file, occurrence, cursor_location) -> None:
    """Set the IFC placement from the Blender cursor (which is in metres).

    edit_object_placement defaults to is_si=True: the API expects SI metres
    and converts them to the project's native units internally.
    """
    import ifcopenshell.api
    import numpy as np

    try:
        matrix = np.eye(4)
        matrix[0][3] = cursor_location.x
        matrix[1][3] = cursor_location.y
        matrix[2][3] = cursor_location.z
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            ifc_file,
            product=occurrence,
            matrix=matrix,
            is_si=True,
        )
    except Exception as exc:
        print(f"IFC Product Library: placement error: {exc}")


def _get_active_storey(context, ifc_file):
    """Return the active IfcBuildingStorey, falling back to the first in the model."""
    try:
        import bonsai.tool as tool
        container = tool.Root.get_default_container()
        if container and container.is_a("IfcBuildingStorey"):
            return container
    except Exception:
        pass

    storeys = ifc_file.by_type("IfcBuildingStorey")
    return storeys[0] if storeys else None


# ---------------------------------------------------------------------------
# Blender object creation
# ---------------------------------------------------------------------------

def _create_blender_mesh_object(context, ifc_file, occurrence, product, verts, faces) -> None:
    """Create a Blender mesh object from the extracted geometry arrays.

    The mesh is built directly from the numpy vertex/face data, giving
    immediate visual feedback in the viewport without requiring Bonsai to
    reload the project.

    verts — (N, 3) float64, source metres (= Blender metres)
    faces — (M, 3) int32, triangle indices
    """
    import numpy as np

    name = occurrence.Name or product.get("identity", {}).get("name", "Product")

    try:
        mesh = bpy.data.meshes.new(name)

        # Vertices — source is metres, Blender is metres: no conversion needed
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.flatten().tolist())

        # Loops (one per face corner)
        n_faces = len(faces)
        mesh.loops.add(n_faces * 3)
        mesh.polygons.add(n_faces)

        import numpy as np
        loop_starts = (np.arange(n_faces, dtype=np.int32) * 3).tolist()
        loop_totals = [3] * n_faces
        face_verts  = faces.flatten().tolist()

        mesh.polygons.foreach_set("loop_start", loop_starts)
        mesh.polygons.foreach_set("loop_total", loop_totals)
        mesh.loops.foreach_set("vertex_index", face_verts)

        mesh.update()
        mesh.validate()

        # Object at cursor position
        obj = bpy.data.objects.new(name, mesh)
        context.scene.collection.objects.link(obj)
        obj.location = context.scene.cursor.location

        # Link to IFC element so Bonsai can manage it
        obj["ifc_definition_id"] = occurrence.id()

        # Make it the active selection
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

    except Exception as exc:
        print(f"IFC Product Library: Blender mesh creation error: {exc}")
        # Non-fatal fallback — IFC model was still correctly modified
        try:
            obj = bpy.data.objects.new(f"[IFC] {name}", None)
            obj.empty_display_type = "ARROWS"
            obj.empty_display_size = 0.1
            context.scene.collection.objects.link(obj)
            obj.location = context.scene.cursor.location
            obj["ifc_definition_id"] = occurrence.id()
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
        except Exception:
            pass
