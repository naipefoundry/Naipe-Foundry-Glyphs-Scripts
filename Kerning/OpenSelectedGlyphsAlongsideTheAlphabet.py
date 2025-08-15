#MenuTitle: Open selected glyphs alongside the alphabet
# -*- coding: utf-8 -*-
__doc__="""
Useful for script fonts. Opens a new tab with the selected glyphs alongside each letter in the lowercase alphabet
"""

# Get the current font and all its glyphs
font = Glyphs.font
glyphs = font.glyphs

# Create an empty dictionary to store selected glyphs
SelectedGlyphs = {}

# Get the selected layers from the Glyphs font
selected_glyphs = Font.selectedLayers

# Iterate through each selected glyph
for layer in selected_glyphs:
    # Get the parent glyph of the current layer
    glyph = layer.parent
    
    # Check if the glyph has a Unicode value assigned
    unicode_value = glyph.unicode
    
    # If the glyph has no Unicode value
    if unicode_value is None:
        # Construct a string with a forward slash followed by the glyph name and a space
        unicode_string = "/" + glyph.name + " "
    else:
        # If the glyph has a Unicode value, convert it to a character
        unicode_string = chr(int(unicode_value, 16))
    
    # Add the glyph name and its corresponding value (either Unicode character or the string with the glyph name) to the SelectedGlyphs dictionary
    SelectedGlyphs[glyph.name] = unicode_string

def add_glyph_before_alphabet(selected_glyphs):
    alphabet = 'abcdefghhijkllmnopqrstuvwxyz'
#    alphabet = 'abcdefghhijkllmnopqrstuvwxyzßæðøþœ'
#    alphabet = 'nmuriıjȷlhkoecbpqdastfvywxzg'
    result = ''
    count = 0
    for glyph_name in selected_glyphs:
        glyph_value = selected_glyphs[glyph_name]
        for letter in alphabet:
            result += glyph_value + letter
            count += 1
            # Add a newline after processing every 10 characters
            if count % 10 == 0:
                result += '\n'
        # Add a double newline after processing each set of alphabet letters for each glyph
        result += '\n\n'
        # Reset count for the next glyph
        count = 0
    return result

output_string = add_glyph_before_alphabet(SelectedGlyphs)

# Create a new tab in the font editor and set its text content to the generated output
tab = font.newTab()
tab.text = output_string