#MenuTitle: Find Glyphs Without Synched Side Bearings
# -*- coding: utf-8 -*-
__doc__="""
Checks the side bearings on all masters to find glyphs which don't have them equal on all masters and opens them to a new tab
"""

##################################################
### This part finds one letter containing each ###
### diacritic and groups them in a single tab  ###
##################################################

# Access the current font
font = Glyphs.font

if font is not None:
    glyph_diff_dict = {}

    # Loop through all glyphs in the font
    for glyph in font.glyphs:
        for master in font.masters:
            layer = glyph.layers[master.id]
            left_side_bearing = layer.LSB
            right_side_bearing = layer.RSB

            # Check if glyph has at least one contour
#            if len(layer.paths) == 0:
#                continue
            
            # Check if LSB and RSB values are not the same in the current master
            if (left_side_bearing != layer.parent.layers[font.selectedFontMaster.id].LSB) or (right_side_bearing != layer.parent.layers[font.selectedFontMaster.id].RSB):
                glyph_diff_dict[glyph.name] = (left_side_bearing, right_side_bearing)
                break

    # Create a list of unicode_string values
    unicode_list = []
    for glyph_name, _ in glyph_diff_dict.items():
        glyph = font.glyphs[glyph_name]
        if glyph.unicode is None:
            unicode_list.append("/" + glyph_name)
        else:
            unicode_list.append(chr(int(glyph.unicode, 16)))

    # Print the unicode_string values as a space-separated list
    print(" ".join(unicode_list))
    
    # Create a new tab and populate it with the unicode_list
    new_tab = font.newTab()
    new_tab.text = " ".join(unicode_list)

else:
    print("No font available.")
