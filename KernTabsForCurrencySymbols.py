#MenuTitle: Kern Tabs for Currency Symbols
# -*- coding: utf-8 -*-
__doc__="""
Opens new tabs for kerning each currency symbol against all figures
"""

# Get the current font and all its glyphs
font = Glyphs.font
glyphs = font.glyphs

# Find all currency glyphs and convert their glyph names to characters
currency_glyphs = [
    chr(int(glyph.unicode, 16))
    for glyph in glyphs
    if glyph.category == "Symbol" and glyph.subCategory == "Currency"
]

# Generate a dictionary of currency tabs with the tab text as specified
CurrencyTabs = {}
for currency_glyph in currency_glyphs:
    CurrencyTabs[currency_glyph] = "\n".join([
        " ".join([
            f"nn{currency_glyph}{i}{currency_glyph}nn",
            f"HH{currency_glyph}{i}{currency_glyph}HH"
        ])
        for i in range(10)
    ])

# Open a new tab for each currency glyph and set the tab text to the corresponding tab text in the dictionary
for key, value in CurrencyTabs.items():
    tab = font.newTab()
    tab.text = value