#MenuTitle: Delete empty components
# -*- coding: utf-8 -*-
__doc__="""
Look through all layers of all glyphs, finds and deletes any empty components
"""


def findAndDeleteEmptyComponentsInFont():
    try:
        # Get the current font
        thisFont = Glyphs.font

        # Iterate through all glyphs in the font
        for glyph in thisFont.glyphs:
            # Check if the glyph has layers
            if glyph.layers:
                # Iterate through layers of the glyph
                for thisLayer in glyph.layers:
                    # Create a list to store components to be removed
                    componentsToRemove = []

                    # Iterate through components of the layer
                    for thisComponent in thisLayer.components:
                        # Check for empty components
                        if thisComponent.componentLayer and not thisComponent.componentLayer.shapes:
                            componentsToRemove.append(thisComponent)

                    # Remove empty components outside the loop
                    for component in componentsToRemove:
                        # Use GSLayer.shapes to remove the component
                        thisLayer.shapes.remove(component)

                    # Print the results to the console for each glyph
                    if componentsToRemove:
                        print(f"Empty Components in {glyph.name} - Layer: {thisLayer.name}")
                        for thisComponent in componentsToRemove:
                            print(f"\t🫙 empty component {thisComponent.componentName}")
                            print("\t\tDeleted.")

    except Exception as e:
        # Handle exceptions and print errors
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())

# Run the main function
findAndDeleteEmptyComponentsInFont()