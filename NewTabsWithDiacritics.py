#MenuTitle: New Tabs With Diacritics

# create an empty dictionary
Diacritic_Dictionary = {}

# get the current font
font = Glyphs.font

# loop through all glyphs in the font
for glyph in font.glyphs:
    # check if the glyph is a diacritic mark
    if glyph.category == "Mark" and glyph.subCategory == "Nonspacing":
        # add the diacritic mark as a key in the dictionary
        Diacritic_Dictionary[glyph.name] = []

# loop through all glyphs in the font
for glyph in font.glyphs:
    # get the first layer of the glyph
    layer = glyph.layers[0]

    # loop through all components in the layer
    for component in layer.components:
        # check if the component is a diacritic mark
        if component.componentName in Diacritic_Dictionary:
            # get the Unicode code point of the glyph and convert it to a Unicode string
            if glyph.unicode is None:
                unicode_string = "/" + glyph.name + " " 
            else:
                unicode_string = chr(int(glyph.unicode, 16))
            # add the Unicode string to the list of values for the diacritic mark key in the dictionary
            Diacritic_Dictionary[component.componentName].append(unicode_string)

# create a new dictionary to store simplified diacritic marks
Simplified_Diacritic_Dictionary = {}

# loop through all keys in Diacritic_Dictionary
for key in Diacritic_Dictionary:
    # remove the suffix from the key name
    simplified_key = key.split(".")[0]
    # if the simplified key already exists in Simplified_Diacritic_Dictionary, append the values
    if simplified_key in Simplified_Diacritic_Dictionary:
        Simplified_Diacritic_Dictionary[simplified_key] += "\n" + ''.join(Diacritic_Dictionary[key])
    # otherwise, create a new key-value pair
    else:
        Simplified_Diacritic_Dictionary[simplified_key] = ''.join(Diacritic_Dictionary[key])

# create a new tab for each key in Simplified_Diacritic_Dictionary
for key in Simplified_Diacritic_Dictionary:
    tab = font.newTab()
    tab.text = Simplified_Diacritic_Dictionary[key]
    tab.textCursor = 0

# print the dictionary to the console
print(Simplified_Diacritic_Dictionary)