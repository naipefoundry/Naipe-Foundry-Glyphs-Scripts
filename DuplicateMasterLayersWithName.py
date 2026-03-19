# MenuTitle: Duplicate Master Layers with Name
# -*- coding: utf-8 -*-
__doc__ = """
Opens a UI to duplicate each master layer of the selected glyphs with a user-defined name prefix.
Optionally decomposes components in the duplicated layer, leaving the original untouched.
"""

from vanilla import FloatingWindow, TextBox, EditText, Button, CheckBox


class DuplicateLayersUI:
    def __init__(self):
        self.w = FloatingWindow((300, 135), "Duplicate Layers")
        self.w.text = TextBox((15, 15, -15, 17), "New layer name prefix:")
        self.w.input = EditText(
            (15, 37, -15, 25),
            placeholder="e.g. Copy",
            continuous=False,
        )
        self.w.decompose_checkbox = CheckBox(
            (15, 70, -15, 20),
            "Decompose components in duplicated layer",
            value=False,
        )
        self.w.button = Button(
            (15, 100, -15, 25),
            "Duplicate Layers",
            callback=self.duplicateLayers,
        )
        self.w.open()

    def duplicateLayers(self, sender):
        font = Glyphs.font
        if not font:
            Message("Please open a font to run this script.", "No Font Open")
            return

        selected_glyphs = list({layer.parent for layer in font.selectedLayers})
        if not selected_glyphs:
            Message("Please select one or more glyphs.", "No Glyphs Selected")
            return

        name_prefix = self.w.input.get().strip()
        if not name_prefix:
            Message("Please enter a name prefix.", "Missing Name")
            return

        should_decompose = self.w.decompose_checkbox.get()
        masters = font.masters
        count = 0
        decomposed_count = 0

        for glyph in selected_glyphs:
            for master in masters:
                original_layer = glyph.layers[master.id]
                if original_layer is None:
                    continue

                duplicate_layer = original_layer.copy()
                duplicate_layer.name = f"{name_prefix} ({master.name})"
                duplicate_layer.associatedMasterId = master.id

                # Append first so the layer has font context for component resolution
                glyph.layers.append(duplicate_layer)

                if should_decompose and duplicate_layer.components:
                    duplicate_layer.decomposeComponents()
                    decomposed_count += 1

                count += 1

        self.w.close()

        detail = f"Duplicated {count} layer(s) across {len(selected_glyphs)} glyph(s) with prefix '{name_prefix}'."
        if should_decompose:
            detail += f"\n{decomposed_count} layer(s) were decomposed."
        Message(detail, "Duplication Done")


DuplicateLayersUI()