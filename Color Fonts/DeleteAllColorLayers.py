#MenuTitle: Delete All Color Layers
# -*- coding: utf-8 -*-
__doc__="""
Finds and deletes any layers with a colorPalette attribute in selected glyphs
"""



def delete_color_layers(glyph):
    # Find Color layers
    color_layer_indices = [i for i, layer in enumerate(glyph.layers) if layer.name.startswith("Color")]

    # Delete Color layers if found
    if color_layer_indices:
        glyph.beginUndo()  # Begin undo grouping
        for index in sorted(color_layer_indices, reverse=True):
            del glyph.layers[index]  # Remove the layer by index
        glyph.endUndo()  # End undo grouping


def find_and_delete_color_layers():
    # Get the currently selected glyphs
    selected_glyphs = Glyphs.font.selectedLayers

    # Iterate over each selected glyph layer
    for glyph_layer in selected_glyphs:
        glyph = glyph_layer.parent

        # Check if Color layers exist
        has_color_layers = any(layer.name.startswith("Color") for layer in glyph.layers)

        # Delete Color layers if exist
        if has_color_layers:
            delete_color_layers(glyph)
            print(f"✅ Deleted Color layers of {glyph.name}")

# Execute the function
find_and_delete_color_layers()
