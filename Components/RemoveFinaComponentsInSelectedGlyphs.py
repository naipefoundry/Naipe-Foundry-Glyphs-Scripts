#MenuTitle: Find and delete components with "fina" in their name
# -*- coding: utf-8 -*-
__doc__="""
Finds and deletes components whose names contain "fina" in all layers of selected glyphs
"""


def main():
    # Access the current document
    doc = Glyphs.font
    
    if not doc:
        print("No document open.")
        return
    
    # Initialize dictionary to store finaGlyphs
    finaGlyphs = {}
    
    # Get the selected glyphs
    selected_glyphs = [l.parent for l in doc.selectedLayers]
    
    if not selected_glyphs:
        print("No glyphs selected.")
        return
    
    for glyph in selected_glyphs:
        processed_components = set()  # To store processed component names for each glyph
        for master in doc.masters:
            layer = glyph.layers[master.id]
            components = layer.components
            
            if components:
                for component in components:
                    component_name = component.componentName
                    if ".fina" in component_name and component_name not in processed_components:
                        if glyph.name not in finaGlyphs:
                            finaGlyphs[glyph.name] = set()  # Use set to store layer names
                        processed_components.add(component_name)  # Add processed component name to the set

    # Remove components from layers based on finaGlyphs dictionary
    for glyph in selected_glyphs:
        for master in doc.masters:
            layer = glyph.layers[master.id]
            components = layer.components
            
            if components:
                for component in components:
                    component_name = component.componentName
                    if ".fina" in component_name:
                        finaGlyphs[glyph.name].add(layer.name)

    for glyph_name, layer_names in finaGlyphs.items():
        glyph = doc.glyphs[glyph_name]
        for layer_name in layer_names:
            for layer in glyph.layers:
                if layer.name == layer_name:
                    for shape in layer.shapes[:]:  # Iterate through a copy of shapes to safely modify the original list
                        if isinstance(shape, GSComponent) and shape.componentName.endswith(".fina"):
                            layer.shapes.remove(shape)
                            print(f"🗑️ Deleted {shape.componentName} from {glyph_name} {layer_name}")

if __name__ == "__main__":
    main()
