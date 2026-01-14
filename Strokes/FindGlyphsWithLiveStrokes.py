# MenuTitle: Find Glyphs with Live Strokes
# -*- coding: utf-8 -*-
__doc__ = """
Show glyphs with live strokes in each master, one tab per master.
"""

font = Glyphs.font
if not font:
    Message("No font open.", title="Error")
    raise SystemExit

Glyphs.showMacroWindow()
print("Scanning for live strokes in master layers…\n")

def glyph_token(glyph):
    """Return a single glyph token for a tab: Unicode or /name for non-Unicode."""
    if glyph.unicode:
        try:
            return chr(int(glyph.unicode, 16))
        except Exception:
            return f"/{glyph.name}"
    return f"/{glyph.name}"

for master in font.masters:
    stroked_glyphs = []

    for glyph in font.glyphs:
        master_layer = glyph.layers[master.id]  # get master layer directly

        if not master_layer:
            continue

        # Only count paths that have a strokeWidth set
        has_live_stroke = any(
            path.attributes and "strokeWidth" in path.attributes
            for path in master_layer.paths
        )

        if has_live_stroke:
            stroked_glyphs.append(glyph)

    print(f"--- MASTER: {master.name} ---")
    if stroked_glyphs:
        # Format glyph names in quotes, comma-separated
        glyph_names = ", ".join(f'"{g.name}"' for g in stroked_glyphs)
        print(f"Found strokes in: {glyph_names}")
        # Tab label + space-separated glyphs
        label = f"-- {master.name}\n"
        glyph_line = " ".join(glyph_token(g) for g in stroked_glyphs)
        font.newTab(label + glyph_line)
        print(f"Opened tab with {len(stroked_glyphs)} glyphs for master '{master.name}'\n")
    else:
        print("No stroked glyphs found for this master.\n")

print("Done.")
