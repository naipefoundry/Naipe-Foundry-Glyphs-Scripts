#MenuTitle: Open selected glyphs alongside the alphabet
# -*- coding: utf-8 -*-
__doc__ = """
Opens a new tab with the selected glyphs alongside Latin, Greek, or Cyrillic letters.
Useful for script fonts.
"""

import vanilla
from GlyphsApp import Glyphs

# ── Alphabet definitions ────────────────────────────────────────────────────

ALPHABETS = {
    "Latin": {
        "lower": list("abcdefghijklmnopqrstuvwxyz"),
        "upper": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    },
    "Greek": {
        "lower": list("αβγδεζηθικλμνξοπρσςτυφχψω"),
        "upper": list("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"),
    },
    "Cyrillic": {
        # ё/Ё and й/Й removed — accented forms irrelevant for kerning.
        "lower": list("абвгдежзиклмнопрстуфхцчшщъыьэюя"),
        "upper": list("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"),
    },
}

# ── Preferences helpers ──────────────────────────────────────────────────────

PREF_KEY_LATIN    = "com.glyphsapp.OpenSelectedGlyphsAlongsideTheAlphabet.Latin"
PREF_KEY_GREEK    = "com.glyphsapp.OpenSelectedGlyphsAlongsideTheAlphabet.Greek"
PREF_KEY_CYRILLIC = "com.glyphsapp.OpenSelectedGlyphsAlongsideTheAlphabet.Cyrillic"
PREF_KEY_CASE     = "com.glyphsapp.OpenSelectedGlyphsAlongsideTheAlphabet.Case"   # 0 = lower, 1 = upper

def get_pref(key, default):
    v = Glyphs.defaults[key]
    return default if v is None else v

# ── Font helpers ─────────────────────────────────────────────────────────────

def font_has_char(font, char):
    """Return True if the font contains a glyph for the given Unicode character."""
    cp = "%04X" % ord(char)
    for g in font.glyphs:
        if g.unicode == cp:
            return True
    return False

def filter_alphabet(font, chars):
    """Remove characters that are absent from the font."""
    return [c for c in chars if font_has_char(font, c)]

def glyph_string(glyph):
    """Return the tab-string representation of a glyph (char or /name)."""
    if glyph.unicode:
        return chr(int(glyph.unicode, 16))
    return "/" + glyph.name

# ── Core string builder ──────────────────────────────────────────────────────

def build_output(selected_glyphs_dict, alphabet_chars, line_width=10):
    """
    For each selected glyph, produce lines like:
        <glyph><a><glyph><b>…  (line_width pairs per line)
    with the glyph repeated AFTER the alphabet letter too (end of each line).
    After all alphabet lines for a glyph, add two blank lines.
    """
    result = ""
    for glyph_name, glyph_str in selected_glyphs_dict.items():
        count = 0
        line_chars = []
        for letter in alphabet_chars:
            line_chars.append(glyph_str + letter)
            count += 1
            if count % line_width == 0:
                # Append the target glyph once more at the end of the line
                result += "".join(line_chars) + glyph_str + "\n"
                line_chars = []
        # Flush any remaining letters
        if line_chars:
            result += "".join(line_chars) + glyph_str + "\n"
        result += "\n\n"
    return result

# ── GUI ──────────────────────────────────────────────────────────────────────

class AlphabetDialog:
    def __init__(self):
        self.font = Glyphs.font
        if not self.font:
            print("No font open!")
            return

        # Restore saved preferences
        self.use_latin    = bool(get_pref(PREF_KEY_LATIN,    1))
        self.use_greek    = bool(get_pref(PREF_KEY_GREEK,    0))
        self.use_cyrillic = bool(get_pref(PREF_KEY_CYRILLIC, 0))
        self.case_index   = int(get_pref(PREF_KEY_CASE,      0))  # 0=lower, 1=upper

        W = 320
        PAD = 16
        y = PAD

        # Placeholder size — will be resized after all controls are placed
        self.w = vanilla.FloatingWindow((W, 100), "Open Glyphs Alongside Alphabet")

        # Scripts label + three checkboxes side by side
        self.w.scriptLabel = vanilla.TextBox((PAD, y, -PAD, 20), "Scripts:", sizeStyle="regular")
        y += 26

        col = (W - PAD * 2) // 3   # divide available width into 3 equal columns
        self.w.latinCheck    = vanilla.CheckBox((PAD + col * 0, y, col, 22), "Latin",    value=self.use_latin,    callback=self.checkCallback)
        self.w.greekCheck    = vanilla.CheckBox((PAD + col * 1, y, col, 22), "Greek",    value=self.use_greek,    callback=self.checkCallback)
        self.w.cyrillicCheck = vanilla.CheckBox((PAD + col * 2, y, col, 22), "Cyrillic", value=self.use_cyrillic, callback=self.checkCallback)
        y += 34

        # Case radio
        self.w.caseLabel = vanilla.TextBox((PAD, y, -PAD, 20), "Case:", sizeStyle="regular")
        y += 26
        self.w.caseRadio = vanilla.RadioGroup((PAD, y, -PAD, 22), ["Lowercase", "Uppercase"],
                                               isVertical=False, callback=self.caseCallback)
        self.w.caseRadio.set(self.case_index)
        y += 34

        # Run button
        self.w.runButton = vanilla.Button((PAD, y, -PAD, 24), "Open Tab", callback=self.run)
        y += 24 + PAD  # bottom padding

        self.w.resize(W, y)
        self.w.open()

    # Callbacks ────────────────────────────────────────────────────────────────

    def checkCallback(self, sender):
        self.use_latin    = self.w.latinCheck.get()
        self.use_greek    = self.w.greekCheck.get()
        self.use_cyrillic = self.w.cyrillicCheck.get()

    def caseCallback(self, sender):
        self.case_index = sender.get()

    def run(self, sender):
        # Save preferences
        Glyphs.defaults[PREF_KEY_LATIN]    = int(self.use_latin)
        Glyphs.defaults[PREF_KEY_GREEK]    = int(self.use_greek)
        Glyphs.defaults[PREF_KEY_CYRILLIC] = int(self.use_cyrillic)
        Glyphs.defaults[PREF_KEY_CASE]     = self.case_index

        if not (self.use_latin or self.use_greek or self.use_cyrillic):
            print("Please select at least one script.")
            return

        case_key = "lower" if self.case_index == 0 else "upper"

        # Build combined alphabet, filtered to glyphs in this font
        combined = []
        for script, active in [("Latin", self.use_latin),
                                ("Greek", self.use_greek),
                                ("Cyrillic", self.use_cyrillic)]:
            if active:
                filtered = filter_alphabet(self.font, ALPHABETS[script][case_key])
                combined.extend(filtered)

        if not combined:
            print("None of the selected alphabet characters are present in this font.")
            return

        # Collect selected glyphs
        selected_dict = {}
        for layer in self.font.selectedLayers:
            glyph = layer.parent
            selected_dict[glyph.name] = glyph_string(glyph)

        if not selected_dict:
            print("No glyphs selected.")
            return

        output = build_output(selected_dict, combined)

        tab = self.font.newTab()
        tab.text = output

        self.w.close()

# ── Entry point ──────────────────────────────────────────────────────────────

AlphabetDialog()
