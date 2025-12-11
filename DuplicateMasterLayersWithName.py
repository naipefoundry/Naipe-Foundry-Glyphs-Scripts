# MenuTitle: Duplicate Master Layers with Name
# -*- coding: utf-8 -*-
__doc__ = """
Opens a UI to duplicate each master layer of the selected glyphs with a user-defined name prefix.
"""

import GlyphsApp
from vanilla import FloatingWindow, TextBox, EditText, Button

class DuplicateLayersUI:
    def __init__(self):
        self.w = FloatingWindow((300, 100), "Duplicate Layers")

        self.w.text = TextBox((15, 15, -15, 17), "New layer name prefix:")
        self.w.input = EditText((15, 35, -15, 25), placeholder="e.g. Copy")
        self.w.button = Button((15, 65, -15, 25), "Duplicate Layers", callback=self.duplicateLayers)

        self.w.open()

    def duplicateLayers(self, sender):
        font = Glyphs.font
        if not font:
            Glyphs.showNotification("No Font Open", "Please open a font to run this script.")
            return

        selected_glyphs = [l.parent for l in font.selectedLayers]
        selected_glyphs = list(set(selected_glyphs))  # remove duplicates

        if not selected_glyphs:
            Glyphs.showNotification("No Glyphs Selected", "Please select one or more glyphs.")
            return

        name_prefix = self.w.input.get().strip()
        if not name_prefix:
            Glyphs.showNotification("Missing Name", "Please enter a name prefix.")
            return

        masters = font.masters

        for glyph in selected_glyphs:
            for master in masters:
                original_layer = glyph.layers[master.id]
                duplicate_layer = original_layer.copy()
                duplicate_layer.name = f"{name_prefix} ({master.name})"
                duplicate_layer.associatedMasterId = master.id
                glyph.layers.append(duplicate_layer)

        Glyphs.showNotification(
            "Duplication Done",
            f"Layers duplicated for {len(selected_glyphs)} selected glyph(s) with prefix '{name_prefix}'."
        )

DuplicateLayersUI()
