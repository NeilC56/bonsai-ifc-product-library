"""
IFC Product Library — IFC Writer

Creates a standards-compliant IFC4 file from a Blender mesh object + metadata dict.

The output file contains:
  - Minimal IFC project structure (Project → Site → Building → Storey)
  - One IfcTypeProduct subclass (the type definition, stored in the library)
  - One IfcProduct occurrence with identity placement at origin
  - IfcTriangulatedFaceSet geometry (IFC4 native, compact tessellation)
  - Property sets populated from metadata['properties']

This is the reverse of the insert operation in insert_ops.py.
"""

def create_product_ifc(
    obj_name: str,   # name of the mesh object in bpy.data.objects
    metadata: dict,  # product.json dict
    output_path: str,
) -> None:
    """Write a product.ifc file from a Blender mesh + metadata.

    Accepts an object *name* rather than a direct object reference so that
    a fresh bpy.data.objects lookup is always performed at export time,
    avoiding stale StructRNA references that arise when mesh data is replaced
    during the cleanup steps (decimate, apply modifiers, join, etc.).

    Raises:
        ImportError  — if ifcopenshell is not available
        ValueError   — if the named object no longer exists, or has no mesh data
        OSError      — if output_path cannot be written
    """
    import bpy
    import ifcopenshell
    import ifcopenshell.api

    # Resolve the object by name at export time
    mesh_obj = bpy.data.objects.get(obj_name)
    if mesh_obj is None:
        raise ValueError(
            f"Object '{obj_name}' no longer exists in the scene. "
            "It may have been deleted or renamed during cleanup."
        )
    if mesh_obj.type != "MESH":
        raise ValueError(
            f"Object '{obj_name}' is a {mesh_obj.type}, not a MESH."
        )

    # ------------------------------------------------------------------
    # 1. Create IFC4 file
    # ------------------------------------------------------------------
    model = ifcopenshell.api.run("project.create_file", version="IFC4")

    # ------------------------------------------------------------------
    # 2. Create project with mm units
    # ------------------------------------------------------------------
    product_name = metadata.get("identity", {}).get("name", "Product")
    project = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcProject",
        name=product_name,
    )

    # Set length unit to millimetres (LENGTHUNIT with MILLI prefix on METRE)
    length_unit = ifcopenshell.api.run(
        "unit.add_si_unit", model,
        unit_type="LENGTHUNIT",
        prefix="MILLI",
    )
    ifcopenshell.api.run("unit.assign_unit", model, units=[length_unit])

    # ------------------------------------------------------------------
    # 3. Create representation contexts
    # ------------------------------------------------------------------
    model_ctx = ifcopenshell.api.run(
        "context.add_context", model,
        context_type="Model",
    )
    body_ctx = ifcopenshell.api.run(
        "context.add_context", model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model_ctx,
    )

    # ------------------------------------------------------------------
    # 4. Minimal spatial hierarchy
    # ------------------------------------------------------------------
    site = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcSite",
        name="Library Site",
    )
    building = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcBuilding",
        name="Library Building",
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcBuildingStorey",
        name="Ground Floor",
    )

    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=site, products=[building])
    ifcopenshell.api.run("aggregate.assign_object", model,
                         relating_object=building, products=[storey])

    # ------------------------------------------------------------------
    # 5. Build geometry from Blender mesh
    # ------------------------------------------------------------------
    verts_mm, triangles = _mesh_to_triangles(mesh_obj)

    if not verts_mm or not triangles:
        raise ValueError(f"Object '{mesh_obj.name}' has no mesh data to export")

    # IfcTriangulatedFaceSet — indices are 1-based in IFC
    point_list = model.createIfcCartesianPointList3D(verts_mm)
    coord_index = [tuple(i + 1 for i in tri) for tri in triangles]
    faceset = model.createIfcTriangulatedFaceSet(
        Coordinates=point_list,
        CoordIndex=coord_index,
    )

    shape_rep = model.createIfcShapeRepresentation(
        ContextOfItems=body_ctx,
        RepresentationIdentifier="Body",
        RepresentationType="Tessellation",
        Items=[faceset],
    )
    product_shape = model.createIfcProductDefinitionShape(
        Representations=[shape_rep],
    )

    # ------------------------------------------------------------------
    # 6. Determine IFC class from metadata
    # ------------------------------------------------------------------
    ifc_info = metadata.get("ifc", {})
    ifc_class = ifc_info.get("class", "IfcBuildingElementProxy")
    predefined_type = ifc_info.get("predefined_type", "NOTDEFINED")

    # IFC4 type class name convention: append "Type" to occurrence class
    # Special cases: IfcDoor → IfcDoorType, IfcWindow → IfcWindowType, etc.
    type_class = _ifc_type_class(ifc_class)

    # ------------------------------------------------------------------
    # 7. Create type product
    # ------------------------------------------------------------------
    type_entity = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class=type_class,
        name=product_name,
    )
    # Set predefined type if the attribute exists
    try:
        type_entity.PredefinedType = predefined_type
    except Exception:
        pass

    # Assign representation to type
    # MappingOrigin must be IfcAxis2Placement3D (not IfcLocalPlacement)
    type_entity.RepresentationMaps = [
        model.createIfcRepresentationMap(
            MappingOrigin=_axis2_placement(model),
            MappedRepresentation=shape_rep,
        )
    ]

    # ------------------------------------------------------------------
    # 8. Create occurrence
    # ------------------------------------------------------------------
    occurrence = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class=ifc_class,
        name=product_name,
    )
    try:
        occurrence.PredefinedType = predefined_type
    except Exception:
        pass

    # Assign representation
    occurrence.Representation = product_shape

    # Place at origin (occurrence uses IfcLocalPlacement)
    occurrence.ObjectPlacement = _local_placement(model)

    # Assign to storey
    ifcopenshell.api.run("spatial.assign_container", model,
                         relating_structure=storey,
                         products=[occurrence])

    # ------------------------------------------------------------------
    # 9. Property sets
    # ------------------------------------------------------------------
    _write_property_sets(model, occurrence, metadata)

    # Also copy key identity properties to the type
    _write_identity_pset(model, type_entity, metadata)

    # ------------------------------------------------------------------
    # 10. Write file
    # ------------------------------------------------------------------
    model.write(output_path)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _mesh_to_triangles(mesh_obj) -> tuple[list, list]:
    """Convert a Blender mesh object to (vertices_mm, triangles).

    vertices_mm: list of (x, y, z) tuples in millimetres
    triangles:   list of (i0, i1, i2) zero-based index tuples

    Applies the object's world matrix and converts Blender metres → mm.
    Triangulates quads/ngons via a tessellation step.
    """
    import bpy
    import bmesh

    # Work on a copy to avoid modifying the original
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    # Triangulate in-place on the temporary mesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()

    # Extract all vertex/polygon data BEFORE calling to_mesh_clear().
    # to_mesh_clear() frees the temporary Mesh data-block; accessing
    # mesh.vertices or mesh.polygons afterwards raises
    # "StructRNA of type Mesh has been removed".
    mat = mesh_obj.matrix_world
    scale = 1000.0  # Blender metres → mm

    vertices = []
    for v in mesh.vertices:
        world = mat @ v.co
        vertices.append((
            round(world.x * scale, 4),
            round(world.y * scale, 4),
            round(world.z * scale, 4),
        ))

    triangles = []
    for poly in mesh.polygons:
        if len(poly.vertices) == 3:
            triangles.append(tuple(poly.vertices))

    # Safe to release the temporary mesh now that data extraction is done
    eval_obj.to_mesh_clear()

    return vertices, triangles


def _axis2_placement(model):
    """Create an IfcAxis2Placement3D at the world origin.

    Used for IfcRepresentationMap.MappingOrigin (type attribute).
    """
    origin = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
    x_axis = model.createIfcDirection((1.0, 0.0, 0.0))
    z_axis = model.createIfcDirection((0.0, 0.0, 1.0))
    return model.createIfcAxis2Placement3D(origin, z_axis, x_axis)


def _local_placement(model):
    """Create an IfcLocalPlacement at the world origin.

    Used for IfcProduct.ObjectPlacement (occurrence attribute).
    """
    axis2 = _axis2_placement(model)
    return model.createIfcLocalPlacement(RelativePlacement=axis2)


# ---------------------------------------------------------------------------
# IFC class name helpers
# ---------------------------------------------------------------------------

_TYPE_OVERRIDES: dict[str, str] = {
    # Some IFC4 type class names don't follow the simple +Type pattern
    "IfcBuildingElementProxy": "IfcBuildingElementProxyType",
    "IfcFurnishingElement":    "IfcFurnishingElementType",
    "IfcBuildingElementPart":  "IfcBuildingElementPartType",
}


def _ifc_type_class(ifc_class: str) -> str:
    """Return the IFC type class name for a given occurrence class."""
    if ifc_class in _TYPE_OVERRIDES:
        return _TYPE_OVERRIDES[ifc_class]
    return ifc_class + "Type"


# ---------------------------------------------------------------------------
# Property set writing
# ---------------------------------------------------------------------------

def _write_property_sets(model, element, metadata: dict) -> None:
    """Create Pset_ProductLibraryIdentity and category-specific Pset."""
    import ifcopenshell.api

    props_dict = metadata.get("properties", {})
    if not props_dict:
        return

    # Category-specific Pset (e.g. Pset_SanitaryTerminalTypeCommon)
    category_path = metadata.get("category", {}).get("path", "")
    pset_name = _pset_name_for_category(category_path)

    pset = ifcopenshell.api.run(
        "pset.add_pset", model,
        product=element,
        name=pset_name,
    )

    # Convert Python values to the right IFC type via the string rep
    pset_props = {}
    for key, value in props_dict.items():
        label = key.replace("_", " ").title()
        if isinstance(value, bool):
            pset_props[label] = value
        elif isinstance(value, int):
            pset_props[label] = value
        elif isinstance(value, float):
            pset_props[label] = value
        else:
            pset_props[label] = str(value)

    if pset_props:
        ifcopenshell.api.run(
            "pset.edit_pset", model,
            pset=pset,
            properties=pset_props,
        )


def _write_identity_pset(model, element, metadata: dict) -> None:
    """Write a Pset_ProductLibraryIdentity with catalogue information."""
    import ifcopenshell.api

    identity = metadata.get("identity", {})
    dims = metadata.get("dimensions", {})
    classification = metadata.get("classification", {})
    compliance = metadata.get("compliance", {})

    props = {}

    if identity.get("manufacturer"):
        props["Manufacturer"] = identity["manufacturer"]
    if identity.get("model_number"):
        props["ModelNumber"] = identity["model_number"]
    if identity.get("product_url"):
        props["ProductURL"] = identity["product_url"]
    if dims.get("width_mm"):
        props["Width_mm"] = float(dims["width_mm"])
    if dims.get("depth_mm"):
        props["Depth_mm"] = float(dims["depth_mm"])
    if dims.get("height_mm"):
        props["Height_mm"] = float(dims["height_mm"])
    if dims.get("weight_kg"):
        props["Weight_kg"] = float(dims["weight_kg"])

    uniclass = classification.get("uniclass_2015", {})
    if uniclass.get("code"):
        props["Uniclass2015"] = uniclass["code"]

    if compliance.get("doc_m"):
        props["DocM_Compliant"] = True

    tags = metadata.get("category", {}).get("tags", [])
    if tags:
        props["Tags"] = ", ".join(tags)

    if not props:
        return

    pset = ifcopenshell.api.run(
        "pset.add_pset", model,
        product=element,
        name="Pset_ProductLibraryIdentity",
    )
    ifcopenshell.api.run(
        "pset.edit_pset", model,
        pset=pset,
        properties=props,
    )


def _pset_name_for_category(category_path: str) -> str:
    """Return a sensible Pset name based on category."""
    mapping = {
        "sanitaryware":    "Pset_SanitaryTerminalTypeCommon",
        "ironmongery":     "Pset_DoorHardwareTypeCommon",
        "doors":           "Pset_DoorCommon",
        "windows":         "Pset_WindowCommon",
        "insulation":      "Pset_ThermalInsulationCommon",
        "furniture":       "Pset_FurnitureTypeCommon",
        "accessibility":   "Pset_ProductLibraryAccessibility",
    }
    top_level = category_path.split("/")[0] if category_path else ""
    return mapping.get(top_level, "Pset_ProductLibraryCommon")
