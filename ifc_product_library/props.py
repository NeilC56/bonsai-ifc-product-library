"""Scene-level property group — holds UI state that Blender needs to own
(i.e. the search field, which must be a proper bpy property for the text
widget to work). Everything else (expanded categories, selected product) lives
in library_index as plain Python state, which avoids the overhead of registering
a CollectionProperty for every slug in the library.
"""

import bpy


class IFCProductLibraryState(bpy.types.PropertyGroup):
    search_query: bpy.props.StringProperty(
        name="Search",
        description="Filter products by name, manufacturer, description, or tag",
        default="",
        options={"TEXTEDIT_UPDATE"},  # update on every keystroke
    )
