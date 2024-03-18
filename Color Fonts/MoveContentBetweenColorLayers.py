#MenuTitle: Move content between color layers
# -*- coding: utf-8 -*-
__doc__="""
Moves contours between one or more color font layers, with options to remove overlap and preserve target layer contents
"""


class SimpleWindow(object):
    def __init__(self):
        self.w = Window((500, 300), "Copy color font layers")
        self.w.sourceListTitle = TextBox((20, 10, 250, 20), "Select one or more source layers:")
        self.w.targetListTitle = TextBox((260, 10, 250, 20), "Select one or more target layers:")
        self.w.sourceLayerList = List((20, 40, -260, -100), [])
        self.w.targetLayerList = List((260, 40, -20, -100), [])
        self.w.keepShapesCheckBox = CheckBox((20, 215, -10, 20), "Keep target layer", value=True)
        self.w.overlapCheckBox = CheckBox((200, 215, -10, 20), "Remove overlap", value=False)
        self.w.button = Button((10, 250, -10, 20), "Copy shapes", callback=self.buttonCallback)
        self.w.open()
        
    def buttonCallback(self, sender):
        # Check if Glyphs.font is available
        if Glyphs.font:
            sourceLayerIndices = self.w.sourceLayerList.getSelection()
            targetLayerIndices = self.w.targetLayerList.getSelection()
            
            keepShapeSetting = self.w.keepShapesCheckBox.get()
            overlapSetting = self.w.overlapCheckBox.get()
            
            selectedGlyphs = Glyphs.font.selection
            
            # Iterate through selected glyphs once
            for glyph in selectedGlyphs:
                glyphName = glyph.name
                
                # Check if glyph has layers
                if glyph.layers:
                    # If Keep target layer checkbox is unchecked iterate through target layers and clear the shapes
                    if not keepShapeSetting:
                        for targetIndex in targetLayerIndices:
                            # Check if target index is valid
                            if targetIndex < len(glyph.layers):
                                targetLayer = glyph.layers[targetIndex]
                                targetLayer.clear()
                                print(f"❌ Removed shapes in {targetLayer.name} of {glyphName}")

                    # Iterate through selected source layers indices once
                    for sourceIndex in sourceLayerIndices:
                        # Check if source index is valid
                        if sourceIndex < len(glyph.layers):
                            sourceLayer = glyph.layers[sourceIndex]
                            
                            # Iterate through selected target layers indices once
                            for targetIndex in targetLayerIndices:
                                # Check if target index is valid
                                if targetIndex < len(glyph.layers):
                                    targetLayer = glyph.layers[targetIndex]
                                    
                                    # Iterate through the shapes present within the selected source layers once
                                    for shape in sourceLayer.shapes:
                                        newShape = shape.copy()
                                        targetLayer.shapes.append(newShape)
                                    
                                    # Prints which source layer has been copied to which target layer and specifies which glyph
                                    print(f"🌈 Copied from {sourceLayer.name} to {targetLayer.name} of {glyphName}")
                                    
                                    # If the remove overlap checkbox is checked prints an indication that the overlap between shapes within the target layer was removed
                                    if overlapSetting:
                                        targetLayer.removeOverlap()
                                        print(f"✅ Removed overlap of {targetLayer.name}")
                else:
                    print(f"⚠️ {glyphName} has no layers.")
        else:
            print("⚠️ There are no fonts selected")
    
    ### UpdateUILists updates the interface of the lists within the window with the names of the layers of the selected glyph that contains the most amount of layers.
    ### This assumes you are working with a color font, which considers that corresponding indexed layers should have the same name.
    def UpdateUILists(self):
        if Glyphs.font:
            listItems = self.w.sourceLayerList.get()
            
            selectedGlyphs = Glyphs.font.selection
            highestLayerCount = 0
            
            for glyph in selectedGlyphs:
                thisLayerCount = len(glyph.layers)
                
                if thisLayerCount > highestLayerCount:
                    highestLayerCount = thisLayerCount
                    referenceGlyph = glyph
                    
            for layer in referenceGlyph.layers:
                listItems.append(layer.name)
                
            self.w.sourceLayerList.set(listItems)
            self.w.targetLayerList.set(listItems)
        else:
            print("⚠️ There are no fonts selected")
    
# Instantiate the SimpleWindow class to create the window
demo = SimpleWindow()
demo.UpdateUILists()