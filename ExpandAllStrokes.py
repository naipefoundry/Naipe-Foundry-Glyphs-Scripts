# MenuTitle: Expand All Strokes
# -*- coding: utf-8 -*-
from vanilla import Window, TextBox, Button

__doc__ = """
Turns all live strokes into paths. It's very destructive, but there's a confirmation dialogue.
"""

class ExpandStrokesDialog:
    def __init__(self):
        self.w = Window((280, 160), "Expand Strokes", minSize=(280, 160))
        
        # Centered prompt with warning emojis and double break after "undone."
        message = "⚠️ This will expand all strokes and\ncan't be undone. ⚠️\n\nAre you sure? 🧐"
        self.w.text = TextBox(
            (15, 25, -15, 70),
            message,
            sizeStyle="regular",
            alignment="center"
        )
        
        self.w.runButton = Button((15, -45, 115, 20), "I'm sure 😎", callback=self.run)
        self.w.cancelButton = Button((-130, -45, 115, 20), "Cancel", callback=self.cancel)
        
        self.w.open()
    
    def run(self, sender):
        import GlyphsApp
        font = Glyphs.font
        if not font:
            Glyphs.showMacroWindow()
            print("No font open.")
            self.w.close()
            return
        
        count = 0
        for g in font.glyphs:
            for l in g.layers:
                if l.isMasterLayer or l.isSpecialLayer:
                    l.flattenOutlinesRemoveOverlap_origHints_secondaryPath_extraHandles_error_(
                        False, None, None, None, None
                    )
                    count += 1
        
        Glyphs.showMacroWindow()
        print(f"✅ Expanded strokes in {count} layers.")
        self.w.close()
    
    def cancel(self, sender):
        self.w.close()

ExpandStrokesDialog()