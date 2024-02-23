#MenuTitle: Find and Replace Color Palette Index
# -*- coding: utf-8 -*-
__doc__="""
Changes Color 2 to Color 1. Hardcoded only, GUI coming eventually
"""


def update_color2_palette(glyph):
    # Find Color 2 layer
    color2_layer = None
    for layer in glyph.layers:
        if layer.name == "Color 2":
            color2_layer = layer
            break

    # Update colorPalette attribute of Color 2 layer if found
    if color2_layer is not None:
        glyph.beginUndo()  # Begin undo grouping
        color2_layer.attributes["colorPalette"] = 1
        glyph.endUndo()  # End undo grouping


def find_and_update_color2_palette():
    # Get the currently selected glyphs
    selected_glyphs = Glyphs.font.selectedLayers

    # Iterate over each selected glyph layer
    for glyph_layer in selected_glyphs:
        glyph = glyph_layer.parent

        # Check if Color 2 layer exists
        has_color_2_layer = any(layer.name == "Color 2" for layer in glyph.layers)

        # Update colorPalette attribute of Color 2 layer if exists
        if has_color_2_layer:
            update_color2_palette(glyph)
            print(f"✅ Updated colorPalette attribute for Color 2 layer in {glyph.name}")

# Execute the function
find_and_update_color2_palette()

def update_color3_to_color2(glyph):
    # Find Color 3 layer
    color3_layer = None
    for layer in glyph.layers:
        if layer.name == "Color 3":
            color3_layer = layer
            break

    # Update colorPalette attribute of Color 3 layer if found
    if color3_layer is not None:
        glyph.beginUndo()  # Begin undo grouping
        color3_layer.name = "Color 2"  # Rename the layer
        glyph.endUndo()  # End undo grouping


def find_and_update_color3_to_color2():
    # Get the currently selected glyphs
    selected_glyphs = Glyphs.font.selectedLayers

    # Iterate over each selected glyph layer
    for glyph_layer in selected_glyphs:
        glyph = glyph_layer.parent

        # Check if Color 3 layer exists
        has_color_3_layer = any(layer.name == "Color 3" for layer in glyph.layers)

        # Update Color 3 layer to Color 2 if exists
        if has_color_3_layer:
            update_color3_to_color2(glyph)
            print(f"✅ Renamed Color 3 layer to Color 2 for {glyph.name}")

# Execute the function
find_and_update_color3_to_color2()
