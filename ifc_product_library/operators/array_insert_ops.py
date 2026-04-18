"""Array insert operator — places multiple beam/joist instances in a row.

Each instance is a separate IFC entity with its own GlobalId, representation,
and placement.  The same scaled+rotated vertex array is reused for all
instances; only the placement translation differs.

Beam geometry is scaled along its longest axis to match the requested beam
length, then rotated (if needed) so the joist runs perpendicular to the
array direction:
    array_direction "X" → joists spaced along X, each joist runs along Y
    array_direction "Y" → joists spaced along Y, each joist runs along X
"""

import bpy
import numpy as np

from ..core import library_index
from .insert_ops import (
    _extract_mesh,
    _find_body_context,
    _create_occurrence,
    _get_active_storey,
)


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

def _is_beam_product(product: dict) -> bool:
    """Return True if this product should show the Array Insert UI."""
    cat = product.get("category", {}).get("path", "")
    ifc_class = product.get("ifc", {}).get("class", "")
    return (
        cat.startswith("structural/joists")
        or cat.startswith("structural/steel")
        or ifc_class == "IfcBeam"
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _prepare_array_geometry(
    verts: "np.ndarray",
    faces: "np.ndarray",
    beam_length_mm: float,
    array_direction: str,
) -> tuple["np.ndarray", "np.ndarray"]:
    """Scale the source geometry to *beam_length_mm* and orient it correctly.

    The source mesh may have its long axis along X or Y.  The array_direction
    tells us which axis the joists are SPACED along:
        "X" → joists are spaced along X, so each joist must run along Y
        "Y" → joists are spaced along Y, so each joist must run along X

    Steps:
    1. Find the longest bounding-box axis (= natural length axis of the mesh).
    2. Scale along that axis so the beam is exactly beam_length_mm long.
    3. If the length axis doesn't match the required run-axis, rotate 90° around Z.

    NOTE — rotation direction:
        We use the CCW convention: x_new = −y_old, y_new = x_old.
        If inserted joists appear rotated 90° the wrong way, swap to:
        x_new = y_old, y_new = −x_old
        This depends on the orientation of the source IFC geometry.
    """
    mins = verts.min(axis=0)
    maxs = verts.max(axis=0)
    dims = maxs - mins

    length_axis = int(np.argmax(dims))          # 0=X, 1=Y (Z excluded implicitly for joists)
    current_length_m = dims[length_axis]
    target_length_m  = beam_length_mm / 1000.0

    scaled = verts.copy()
    if current_length_m > 1e-6:
        scale = target_length_m / current_length_m
        mid   = (mins[length_axis] + maxs[length_axis]) / 2.0
        scaled[:, length_axis] = mid + (verts[:, length_axis] - mid) * scale

    # Determine which axis the joist should run along after placement
    # array_direction "X" → joist runs along Y → target_axis = 1
    # array_direction "Y" → joist runs along X → target_axis = 0
    target_axis = 1 if array_direction == "X" else 0

    if length_axis != target_axis:
        # Rotate 90° CCW around Z: (x, y) → (−y, x)
        rotated = scaled.copy()
        rotated[:, 0] = -scaled[:, 1]
        rotated[:, 1] =  scaled[:, 0]
        scaled = rotated

    return scaled, faces


def _compute_positions(
    pg,
    cursor_location,
) -> tuple[list[tuple[float, float, float]], int, int, float]:
    """Compute joist positions along the array direction.

    Returns
    -------
    positions   — list of (x, y, z) in metres for each joist
    n_joists    — total number of joists
    n_spaces    — number of regular spaces
    odd_m       — size of the odd (remainder) gap in metres
    """
    span_m    = pg.span_length_mm   / 1000.0
    spacing_m = pg.spacing_mm       / 1000.0
    start_m   = pg.start_offset_mm  / 1000.0
    end_m     = pg.end_offset_mm    / 1000.0

    usable   = span_m - start_m - end_m
    if usable <= 0 or spacing_m <= 0:
        # Degenerate case — place a single joist at the start offset
        cx, cy, cz = cursor_location.x, cursor_location.y, cursor_location.z
        if pg.array_direction == "X":
            return [(cx + start_m, cy, cz)], 1, 0, 0.0
        else:
            return [(cx, cy + start_m, cz)], 1, 0, 0.0

    n_spaces = int(usable / spacing_m)
    n_joists = n_spaces + 1
    odd_m    = usable - n_spaces * spacing_m    # remainder gap

    # If odd_at_start, shift all positions by odd_m so the remainder sits
    # between the wall and the first joist rather than after the last joist.
    shift = odd_m if pg.odd_at_start else 0.0

    cx, cy, cz = cursor_location.x, cursor_location.y, cursor_location.z
    positions: list[tuple[float, float, float]] = []

    if pg.array_direction == "X":
        base = cx + start_m + shift
        for i in range(n_joists):
            positions.append((base + i * spacing_m, cy, cz))
    else:   # "Y"
        base = cy + start_m + shift
        for i in range(n_joists):
            positions.append((cx, base + i * spacing_m, cz))

    return positions, n_joists, n_spaces, odd_m


# ---------------------------------------------------------------------------
# Main operator
# ---------------------------------------------------------------------------

class IFCLIB_OT_InsertProductArray(bpy.types.Operator):
    """Insert a row of beam/joist instances into the active Bonsai IFC project."""
    bl_idname  = "ifclib.insert_product_array"
    bl_label   = "Insert Array"
    bl_description = (
        "Insert multiple beam/joist instances at regular centres "
        "starting from the 3D cursor"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # ── Validate selection ─────────────────────────────────────────────
        state = library_index.get_ui_state()
        slug  = state["selected_product_slug"]
        if not slug:
            self.report({"WARNING"}, "No product selected")
            return {"CANCELLED"}

        product = library_index.get_product(slug)
        if not product:
            self.report({"ERROR"}, f"Product '{slug}' not found in index")
            return {"CANCELLED"}

        # ── Require Bonsai ─────────────────────────────────────────────────
        try:
            from bonsai.bim.ifc import IfcStore
        except ImportError:
            self.report({"ERROR"}, "Bonsai (BlenderBIM) is not installed")
            return {"CANCELLED"}

        ifc_file = IfcStore.get_file()
        if ifc_file is None:
            self.report({"ERROR"}, "No active IFC project — open a Bonsai project first")
            return {"CANCELLED"}

        # ── Locate product.ifc ─────────────────────────────────────────────
        import os
        folder           = product.get("_folder_path", "")
        product_ifc_path = os.path.join(folder, "product.ifc")
        if not os.path.exists(product_ifc_path):
            self.report({"ERROR"}, f"product.ifc not found: {product_ifc_path}")
            return {"CANCELLED"}

        try:
            return self._insert_array(context, ifc_file, product_ifc_path, product)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.report({"ERROR"}, f"Array insert failed: {exc}")
            return {"CANCELLED"}

    # -----------------------------------------------------------------------

    def _insert_array(self, context, ifc_file, product_ifc_path: str, product: dict):
        import ifcopenshell.api
        import numpy as np

        name = product.get("identity", {}).get("name", "Product")
        pg   = context.scene.ifclib_array_insert

        # ── 1. Tessellate source geometry ──────────────────────────────────
        verts, faces = _extract_mesh(product_ifc_path)
        if verts is None or len(faces) == 0:
            self.report({"ERROR"}, "Could not tessellate geometry from product.ifc")
            return {"CANCELLED"}

        # ── 2. Scale & rotate geometry (shared across all instances) ───────
        scaled_verts, faces = _prepare_array_geometry(
            verts, faces, pg.beam_length_mm, pg.array_direction
        )
        scaled_verts_list = scaled_verts.tolist()
        faces_list        = faces.tolist()

        # ── 3. Compute instance positions ──────────────────────────────────
        positions, n_joists, n_spaces, odd_m = _compute_positions(
            pg, context.scene.cursor.location
        )

        if n_joists < 1:
            self.report({"WARNING"}, "No joists to insert — check span and spacing values")
            return {"CANCELLED"}

        if n_joists == 1 and (pg.span_length_mm - pg.start_offset_mm - pg.end_offset_mm) <= 0:
            self.report(
                {"WARNING"},
                "Wall offsets exceed span — inserting single joist at start offset"
            )

        # ── 4. IFC context & storey ────────────────────────────────────────
        body_context = _find_body_context(ifc_file)
        if body_context is None:
            self.report({"ERROR"}, "No Body representation context found in IFC project")
            return {"CANCELLED"}

        storey    = _get_active_storey(context, ifc_file)
        ifc_class = product.get("ifc", {}).get("class", "IfcBuildingElementProxy")
        predefined_type = product.get("ifc", {}).get("predefined_type", "")

        print(
            f"IFC Product Library: inserting array of {n_joists} × '{name}' "
            f"at {int(pg.spacing_mm)}mm centres"
        )

        # ── 5. Loop — one IFC entity + Blender object per position ─────────
        error_count = 0
        inserted    = 0

        bpy.ops.object.select_all(action="DESELECT")
        last_obj = None

        for i, (px, py, pz) in enumerate(positions):
            try:
                # Create IFC occurrence
                occurrence = _create_occurrence(
                    ifc_file, ifc_class, f"{name} [{i + 1}]"
                )
                if occurrence is None:
                    error_count += 1
                    continue

                if predefined_type and predefined_type not in ("NOTDEFINED", "USERDEFINED"):
                    try:
                        occurrence.PredefinedType = predefined_type
                    except Exception:
                        pass

                # Each occurrence gets its own representation
                representation = ifcopenshell.api.run(
                    "geometry.add_mesh_representation",
                    ifc_file,
                    context=body_context,
                    vertices=[scaled_verts_list],
                    faces=[faces_list],
                )

                ifcopenshell.api.run(
                    "geometry.assign_representation",
                    ifc_file,
                    product=occurrence,
                    representation=representation,
                )

                # Placement at per-instance position (SI metres)
                matrix = np.eye(4)
                matrix[0][3] = px
                matrix[1][3] = py
                matrix[2][3] = pz
                ifcopenshell.api.run(
                    "geometry.edit_object_placement",
                    ifc_file,
                    product=occurrence,
                    matrix=matrix,
                    is_si=True,
                )

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

                # Blender mesh object at per-instance position
                obj = _create_blender_mesh_object_at(
                    context, ifc_file, occurrence, product,
                    scaled_verts, faces, (px, py, pz)
                )
                if obj:
                    obj.select_set(True)
                    last_obj = obj

                inserted += 1

            except Exception as exc:
                import traceback
                traceback.print_exc()
                error_count += 1
                print(f"IFC Product Library: error inserting joist {i + 1}: {exc}")

        if last_obj:
            context.view_layer.objects.active = last_obj

        msg = f"Inserted {inserted} joists at {int(pg.spacing_mm)}mm centres"
        if error_count:
            msg += f" ({error_count} error{'s' if error_count != 1 else ''})"
            self.report({"WARNING"}, msg)
        else:
            self.report({"INFO"}, msg)

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Blender mesh creation (per-instance position variant)
# ---------------------------------------------------------------------------

def _create_blender_mesh_object_at(
    context,
    ifc_file,
    occurrence,
    product: dict,
    verts: "np.ndarray",
    faces: "np.ndarray",
    location: tuple[float, float, float],
):
    """Create a Blender mesh at *location* rather than at the 3D cursor.

    This is an inline variant of insert_ops._create_blender_mesh_object that
    accepts an explicit world-space location (in SI metres).  It does NOT
    call bpy.ops.object.select_all — the caller manages selection.
    """
    name = occurrence.Name or product.get("identity", {}).get("name", "Product")

    try:
        mesh = bpy.data.meshes.new(name)

        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.flatten().tolist())

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

        obj = bpy.data.objects.new(name, mesh)
        context.scene.collection.objects.link(obj)
        obj.location = location
        obj["ifc_definition_id"] = occurrence.id()

        return obj

    except Exception as exc:
        print(f"IFC Product Library: Blender mesh creation error (array): {exc}")
        try:
            obj = bpy.data.objects.new(f"[IFC] {name}", None)
            obj.empty_display_type = "ARROWS"
            obj.empty_display_size = 0.1
            context.scene.collection.objects.link(obj)
            obj.location = location
            obj["ifc_definition_id"] = occurrence.id()
            return obj
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Preset operators — written from operator execute(), not from draw()
# ---------------------------------------------------------------------------

class IFCLIB_OT_SetSpacing(bpy.types.Operator):
    """Set a preset joist spacing."""
    bl_idname  = "ifclib.set_spacing"
    bl_label   = "Set Spacing"
    bl_options = {"INTERNAL"}

    spacing: bpy.props.IntProperty(default=600)

    def execute(self, context):
        context.scene.ifclib_array_insert.spacing_mm = float(self.spacing)
        return {"FINISHED"}


class IFCLIB_OT_SetWallOffset(bpy.types.Operator):
    """Set a preset wall offset for one or both ends."""
    bl_idname  = "ifclib.set_wall_offset"
    bl_label   = "Set Wall Offset"
    bl_options = {"INTERNAL"}

    end:      bpy.props.StringProperty(default="both")  # "start" | "end" | "both"
    value_mm: bpy.props.IntProperty(default=20)

    def execute(self, context):
        pg = context.scene.ifclib_array_insert
        if self.end in ("start", "both"):
            pg.start_offset_mm = float(self.value_mm)
        if self.end in ("end", "both"):
            pg.end_offset_mm = float(self.value_mm)
        return {"FINISHED"}


class IFCLIB_OT_SetSpanTable(bpy.types.Operator):
    """Activate a span table and reset the load case to the first available."""
    bl_idname  = "ifclib.set_span_table"
    bl_label   = "Set Span Table"
    bl_options = {"INTERNAL"}

    filename: bpy.props.StringProperty(default="")

    def execute(self, context):
        from ..core import span_tables

        pg = context.scene.ifclib_array_insert
        pg.active_span_table = self.filename

        lib_path = library_index.get_index().get("library_path", "")
        tbl = span_tables.load_span_table(lib_path, self.filename)
        if tbl:
            cases = tbl.get("load_cases", [])
            if cases:
                pg.load_case = cases[0]["key"]

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Registration list
# ---------------------------------------------------------------------------

classes = (
    IFCLIB_OT_InsertProductArray,
    IFCLIB_OT_SetSpacing,
    IFCLIB_OT_SetWallOffset,
    IFCLIB_OT_SetSpanTable,
)
