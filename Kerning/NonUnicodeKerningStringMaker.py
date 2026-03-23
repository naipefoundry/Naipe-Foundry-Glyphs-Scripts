#MenuTitle: Non-unicode Kerning String Maker
# -*- coding: utf-8 -*-
__doc__="""
Creates new tabs with kerning strings for your non-unicode glyphs.
"""

import vanilla
from GlyphsApp import Glyphs

# -----------------------------
# 1. CONFIGURATION
# -----------------------------

UI_GROUPS = [
    {"label": "Upper case", "key": "UC"},
    {"label": "Lower case", "key": "lc"},
    {"label": "Numbers", "key": "numbers"},
    {"label": "Punctuation and Symbols", "key": "punctuation"}
]

NUMBER_BASE_NAMES = ["zero", "one", "seven", "four", "two", "five", "three", "six", "nine", "eight"]

NUMBER_VARIANTS_CONFIG = [
    {"suffix": None, "label": "Default Numbers"},
    {"suffix": "lf", "label": "Lining Figures"},
    {"suffix": "osf", "label": "Old Style Figures"},
    {"suffix": "dnom", "label": "Denominators"},
    {"suffix": "numr", "label": "Numerators"},
    {"suffix": "sinf", "label": "Inferiors"},
    {"suffix": "sups", "label": "Superiors"},
    {"suffix": "tf", "label": "Tabular Figures"},
    {"suffix": "tosf", "label": "Tabular Old Style Figures"},
]

DATA = {
    "UC_LTN": {"chars": "HILEFTKMNUƯJŊOƠQCGŒØDƏBPRÞAÆVWYXZSẞĦÐŁĽ", "l_ctrl": "OH", "r_ctrl": "HO"},
    "lc_LTN": {"chars": "nmuưriıjȷŋhlłľkoơøœeəcðbþpqdďđħgaætŧťfvywxzsß", "l_ctrl": "on", "r_ctrl": "no"},
    "UC_CYR": {"chars": "НИПЏШЫІМЕЦЩДЈЮОФСЄЭЗВРЯГҐТЪЋЂБЬЊЛЉКЖХУЧАЅ", "l_ctrl": "ОН", "r_ctrl": "НО"},
    "lc_CYR": {"chars": "нипџшыміцщдјюобфрћђесєэзвягґтьъњлљкжхчуаѕ", "l_ctrl": "он", "r_ctrl": "но"},
    "UC_GRK": {"chars": "ΗΠΙΓΕΤΚΜΝΞΒΡΨΟΘΩΦΑΔΛΥΧΖΣΉΊΈΌΆΏΎΎ", "l_ctrl": "ΟΗ", "r_ctrl": "ΗΟ"},
    "lc_GRK": {"chars": "ηπιτκμοσρδαβφψωεςζξθυνγχλ", "l_ctrl": "οη", "r_ctrl": "ηο"},
    "punctuation": {
        "chars": [".", ",", ":", ";", "-", "_", "/", "\\", "¡!", "¿?", "()", "[]", "{}", "‘’", "‚‘", "’", "\"\"", "\'\'", "‹›", "›‹", "*", "#", "&", "@", "©", "®", "¶", "§", "№", "$", "€", "£", "¥", "₦", "₹", "₩", "฿", "₫", "¢", "₴", "₽", "%", "‰", "†", "‡", "™", "ª", "º", "®", "↑", "↓", "↖", "↙", "←", "→", "↘", "↗", "☚", "☛", "❦", "<>"],
        "chars_GRK": ["·"],  # ano teleia, prepended when Greek is selected
        "l_ctrl": "OH", "r_ctrl": "HO"
    }
}

class VariantKerningUI:
    def __init__(self):
        self.ui_width = 380
        y = 20

        total_height = (
            20 + 24 +               # Script label + radio
            45 +                    # gap
            20 + 24 +               # Order label + radio
            45 +                    # gap
            20 + 4 +                # Kern This label
            48 + 21 +               # glyph input field + gap
            20 + 24 +               # Against This label
            len(UI_GROUPS) * 24 +   # checkboxes
            20 +                    # gap before button
            28 + 17                 # button + bottom padding
        )

        self.w = vanilla.FloatingWindow((self.ui_width, total_height), "Non-unicode Kerning String Maker")

        self.w.labelScript = vanilla.TextBox((20, y, -20, 20), "Writing System")
        y += 24
        self.w.scriptRadio = vanilla.RadioGroup((20, y, -20, 20), ["Latin", "Cyrillic", "Greek"], isVertical=False)
        self.w.scriptRadio.set(0)
        y += 45

        self.w.labelOrder = vanilla.TextBox((20, y, -20, 20), "Character Order")
        y += 24
        self.w.orderRadio = vanilla.RadioGroup((20, y, -20, 20), ["By Shape", "Alphabetical"], isVertical=False)
        self.w.orderRadio.set(0)
        y += 45

        self.w.labelPrimary = vanilla.TextBox((20, y, -20, 20), "Kern These Glyphs:  ⚠️ Must be space-separated ⚠️")
        y += 24
        self.w.glyphInput = vanilla.EditText((20, y, -20, 48))
        y += 48 + 21

        self.w.labelSecondary = vanilla.TextBox((20, y, -20, 20), "Against This")
        y += 24

        self.checkboxes = {}
        for group in UI_GROUPS:
            attr = f"cb_{group['key']}"
            setattr(self.w, attr, vanilla.CheckBox((25, y, -20, 20), group["label"], value=True))
            self.checkboxes[group['key']] = getattr(self.w, attr)
            y += 24

        y += 20
        self.w.button = vanilla.Button((50, y, -50, 28), "Generate Kerning Tabs", callback=self.generate)

        self.w.open()

    def _format_glyph_name(self, name):
        name = name.strip().lstrip("/")
        return f"/{name} "

    def _handle_slash_punc(self, punc):
        if punc == "/": return "/slash "
        return punc

    def _get_flattened_and_wrappers(self, group_chars):
        flat, wrappers = [], []
        for item in group_chars:
            for c in item: flat.append(c)
            w_left = item[0]
            w_right = item[1] if len(item) > 1 else item[0]
            wrappers.append((w_left, w_right))
        return flat, wrappers

    def get_data_key(self, ui_key):
        if ui_key in ["numbers", "punctuation"]: return ui_key
        script = ["LTN", "CYR", "GRK"][self.w.scriptRadio.get()]
        return f"{ui_key}_{script}"

    def get_filtered_chars(self, font, data_key):
        if data_key == "numbers": return []
        raw = list(DATA[data_key]["chars"])
        if data_key == "punctuation" and self.w.scriptRadio.get() == 2:
            raw = DATA["punctuation"].get("chars_GRK", []) + raw
        valid = [item for item in raw if all(font.glyphForCharacter_(ord(c)) or font.glyphs[c] for c in item)]
        if self.w.orderRadio.get() == 1 and data_key != "punctuation":
            valid.sort()
        return valid

    def get_variant_glyphs(self, font):
        raw_input = self.w.glyphInput.get().strip()
        if not raw_input: return []
        names = [n.strip().lstrip("/") for n in raw_input.split() if n.strip()]
        return [n for n in names if font.glyphs[n]]

    def generate(self, sender):
        font = Glyphs.font
        if not font: return

        variant_glyphs = self.get_variant_glyphs(font)
        if not variant_glyphs: return

        selected_sec_keys = [self.get_data_key(k) for k, cb in self.checkboxes.items() if cb.get()]

        for sec_key in selected_sec_keys:
            if sec_key == "numbers":
                self.generate_vs_numbers_tab(font, variant_glyphs)
            else:
                self.generate_standard_tab(font, variant_glyphs, sec_key)

    def generate_standard_tab(self, font, variant_glyphs, s_key):
        is_s_punc = s_key == "punctuation"
        s_label = next(g["label"] for g in UI_GROUPS if g["key"] in s_key or s_key == g["key"])
        lines = [f"--- Your Glyphs vs {s_label} ---"]

        if is_s_punc:
            punc_chars = self.get_filtered_chars(font, s_key)
            _, wrappers = self._get_flattened_and_wrappers(punc_chars)
            for w_l, w_r in wrappers:
                wl_f = self._handle_slash_punc(w_l)
                wr_f = self._handle_slash_punc(w_r)
                line = " ".join(f"{wl_f}{self._format_glyph_name(v)}{wr_f}" for v in variant_glyphs)
                lines.append(line)
        else:
            s_chars = self.get_filtered_chars(font, s_key)
            l_ctrl = DATA[s_key]["l_ctrl"]
            r_ctrl = DATA[s_key]["r_ctrl"]
            for v in variant_glyphs:
                v_f = self._format_glyph_name(v)
                line = " ".join(f"{l_ctrl}{v_f}{s}{r_ctrl}" for s in s_chars)
                lines.append(line)

        font.newTab("\n\n".join(lines))

    def generate_vs_numbers_tab(self, font, variant_glyphs):
        variants = []
        for cfg in NUMBER_VARIANTS_CONFIG:
            suffix = cfg["suffix"]
            glyphs = [f"{n}{'.'+suffix if suffix else ''}" for n in NUMBER_BASE_NAMES if font.glyphs[f"{n}{'.'+suffix if suffix else ''}"]]
            if glyphs: variants.append({"label": cfg["label"], "glyphs": glyphs, "suffix": suffix})

        all_lines = []
        for var in variants:
            all_lines.append(f"--- Your Glyphs vs {var['label']} ---")
            z_fmt = self._format_glyph_name(f"zero{'.'+var['suffix'] if var['suffix'] else ''}")
            l_ctrl = f"{z_fmt}{z_fmt}"
            r_ctrl = f"{z_fmt}{z_fmt}"
            for v in variant_glyphs:
                v_f = self._format_glyph_name(v)
                line = " ".join(f"{l_ctrl}{v_f}{self._format_glyph_name(n)}{v_f}{r_ctrl}" for n in var["glyphs"])
                all_lines.append(line)

        font.newTab("\n\n".join(all_lines))

if Glyphs.font:
    VariantKerningUI()
