#MenuTitle: New Tabs With Diacritics

##################################################
### This part finds one letter containing each ###
### diacritic and groups them in a single tab  ###
##################################################

# create an empty dictionary
NewDiacritic_Dictionary = {}

# get the current font
font = Glyphs.font

# loop through all glyphs in the font
for glyph in font.glyphs:
    # check if the glyph is a diacritic mark
    if glyph.category == "Mark" and glyph.subCategory == "Nonspacing":
        # add the diacritic mark as a key in the dictionary
        NewDiacritic_Dictionary[glyph.name] = []

# create a new dictionary to store the diacritic specimens
Diacritic_Specimens = {}

# loop through all glyphs in the font again
for glyph in font.glyphs:
    # check if the glyph is a letter
    if glyph.category == "Letter":
        # check if the glyph contains any diacritic marks
        for layer in glyph.layers:
            if layer is not None: # added check for layer existence
                for component in layer.components:
                    if component.componentName in NewDiacritic_Dictionary.keys():
                        # add the glyph name to the list of specimens for the diacritic mark
                        NewDiacritic_Dictionary[component.componentName].append(glyph.name)
                        break

# create a new list to store the example glyphs
Example_Glyphs = []

# loop through all diacritic marks in the dictionary
for diacritic in sorted(NewDiacritic_Dictionary.keys()):
    # get the list of specimens for the diacritic mark
    specimens = NewDiacritic_Dictionary[diacritic]
    if len(specimens) > 0:
        # add the first specimen to the example glyphs list
        Example_Glyphs.append(sorted(specimens)[0])

# create a space-separated string of the example glyph names and alphabetize the words
example_glyphs_string = " ".join(sorted(Example_Glyphs))

# convert the words in example_glyphs_string into single characters
example_glyphs_characters = ""
for word in example_glyphs_string.split():
    glyph = font.glyphs[word]
    example_glyphs_characters += glyph.string

# open a new tab with example_glyphs_characters as its text
new_tab = font.newTab()
new_tab.text = example_glyphs_characters

# print the example glyphs string to the console
print("Example glyphs for diacritic marks:")
print(example_glyphs_characters)


#########################################################
### This part finds all the letters that contain each ###
### diacritic and groups them in separate single tabs ###
#########################################################


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
