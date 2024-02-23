#MenuTitle: Copy content from Color 3 to Color 1 then remove overlap
# -*- coding: utf-8 -*-
__doc__="""
Copies content from Color layer 3 and adds it to Color Layer 1, preserving the original content of Color 1, then removes the overlap in Color 1.
"""

##Right now this script only works on hard-coded Color layer indices 3 and 1, it'd be nice to have a GUI at some point where one selects which layer to copy to and from, with toggles for keeping the data in the target layer or not, and another for removing the overlap or not


def copy_color3_to_color1(glyph):
    # Find Color 3 layer
    color3_layer = None
    for layer in glyph.layers:
        if layer.name == "Color 3":
            color3_layer = layer
            break

    if color3_layer:
        # Find or create Color 1 layer
        color1_layer = None
        for layer in glyph.layers:
            if layer.name == "Color 1":
                color1_layer = layer
                break

        if not color1_layer:
            color1_layer = GSLayer()
            color1_layer.name = "Color 1"
            glyph.layers.append(color1_layer)

        # Copy contours from Color 3 to Color 1 layer
        for shape in color3_layer.shapes:
            new_shape = shape.copy()
            color1_layer.shapes.append(new_shape)

        # Remove overlaps in Color 1 layer
        color1_layer.removeOverlap()

def find_and_copy_color3_to_color1():
    # Get the currently selected glyphs
    selected_glyphs = Glyphs.font.selectedLayers

    # Dictionary to store glyphs with Color 3 layer
    glyphs_with_color3 = {}

    # Iterate over each selected glyph layer
    for glyph_layer in selected_glyphs:
        glyph = glyph_layer.parent

        # Flag to check if Color 3 layer exists
        has_color_3_layer = False

        # Iterate over each layer in the glyph
        for layer in glyph.layers:
            # Check if the layer is Color 3
            if layer.name == "Color 3":
                has_color_3_layer = True

        # Store glyph name if Color 3 layer exists
        if has_color_3_layer:
            glyphs_with_color3[glyph.name] = True

    # Copy contours from Color 3 to Color 1 layer for each glyph in the dictionary
    for glyph_name in glyphs_with_color3:
        glyph = Glyphs.font.glyphs[glyph_name]
        copy_color3_to_color1(glyph)
        print(f"🌈 Copied Color 3 into Color 1 of {glyph_name}")

# Execute the function
find_and_copy_color3_to_color1()
