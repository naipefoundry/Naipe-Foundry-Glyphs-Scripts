#MenuTitle: Kerning String Maker
# -*- coding: utf-8 -*-
__doc__="""
Creates new tabs with kerning strings based on YOUR character set.
"""

import vanilla
from GlyphsApp import Glyphs

# -----------------------------
# 1. CONFIGURATION
# -----------------------------

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

UI_GROUPS = [
    {"label": "Upper case", "key": "UC"},
    {"label": "Lower case", "key": "lc"},
    {"label": "Numbers", "key": "numbers"},
    {"label": "Punctuation and Symbols", "key": "punctuation"}
]

DATA = {
    "UC_LTN": {"chars": "HILEFTKMNUƯJŊOƠQCGŒØDƏBPRÞAÆVWYXZSẞĦÐŁĽ", "l_ctrl": "OH", "r_ctrl": "HO"},
    "lc_LTN": {"chars": "nmuưriıjȷŋhlłkoơøœeəcðbpþqdďđħgaætŧťfvywxzsß", "l_ctrl": "on", "r_ctrl": "no"},
    "UC_CYR": {"chars": "НИПЏШЫІМЕЦЩДЈЮОФСЄЭЗВРЯГҐТЪЋЂБЬЊЛЉКЖХУЧАЅ", "l_ctrl": "ОН", "r_ctrl": "НО"},
    "lc_CYR": {"chars": "нипџшыміцщдјюобфрћђесєэзвягґтьъњлљкжхчуаѕ", "l_ctrl": "он", "r_ctrl": "но"},
    "punctuation": {
        "chars": [".", ",", ":", ";", "-", "_", "/", "\\", "¡!", "¿?", "()", "[]", "{}", "‘’", "‚‘", "’", "\"\"", "\'\'", "‹›", "›‹", "*", "#", "&", "@", "©", "®", "¶", "§", "№", "$", "€", "£", "¥", "₦", "₹", "₩", "฿", "₫", "¢", "₴", "₽", "%", "‰", "†", "‡", "™", "ª", "º", "®", "↑", "↓", "↖", "↙", "←", "→", "↘", "↗", "☚", "☛", "❦", "<>"],
        "l_ctrl": "OH", "r_ctrl": "HO" 
    }
}

class KerningUI:
    def __init__(self):
        self.ui_width = 320
        self.current_height = 20
        self.w = vanilla.FloatingWindow((self.ui_width, 100), "Kerning String Maker")
        
        self.w.labelScript = vanilla.TextBox((20, self.current_height, -20, 20), "Writing System")
        self.current_height += 24
        self.w.scriptRadio = vanilla.RadioGroup((20, self.current_height, -20, 20), ["Latin", "Cyrillic"], isVertical=False)
        self.w.scriptRadio.set(0)
        self.current_height += 45
        
        self.w.labelOrder = vanilla.TextBox((20, self.current_height, -20, 20), "Character Order")
        self.current_height += 24
        self.w.orderRadio = vanilla.RadioGroup((20, self.current_height, -20, 20), ["By Shape", "Alphabetical"], isVertical=False)
        self.w.orderRadio.set(0)
        self.current_height += 45

        self.w.labelPrimary = vanilla.TextBox((20, self.current_height, -20, 20), "Kern This")
        self.current_height += 24
        self.w.primaryDropdown = vanilla.PopUpButton((20, self.current_height, -20, 20), [g["label"] for g in UI_GROUPS])
        self.current_height += 45

        self.w.labelSecondary = vanilla.TextBox((20, self.current_height, -20, 20), "Against This")
        self.current_height += 24
        
        self.checkboxes = {}
        for group in UI_GROUPS:
            attr = f"cb_{group['key']}"
            setattr(self.w, attr, vanilla.CheckBox((25, self.current_height, -20, 20), group["label"], value=True))
            self.checkboxes[group['key']] = getattr(self.w, attr)
            self.current_height += 24
            
        self.current_height += 20
        self.w.button = vanilla.Button((50, self.current_height, -50, 28), "Generate Kerning Tabs", callback=self.generate)
        self.current_height += 45
        
        self.w.resize(self.ui_width, self.current_height)
        self.w.open()

    def _get_flattened_and_wrappers(self, group_chars):
        flat, wrappers = [], []
        for item in group_chars:
            for c in item: flat.append(c)
            w_left = item[0]
            w_right = item[1] if len(item) > 1 else item[0]
            wrappers.append((w_left, w_right))
        return flat, wrappers

    def _format_glyph_name(self, name):
        name = name.strip().lstrip("/")
        return f"/{name} "

    def _handle_slash_punc(self, punc, is_left=True):
        if punc == "/": return "//"
        return punc

    def get_data_key(self, ui_key):
        if ui_key in ["numbers", "punctuation"]: return ui_key
        script = "LTN" if self.w.scriptRadio.get() == 0 else "CYR"
        return f"{ui_key}_{script}"

    def get_filtered_chars(self, font, data_key):
        if data_key == "numbers": return []
        raw = DATA[data_key]["chars"]
        valid = [item for item in raw if all(font.glyphForCharacter_(ord(c)) or font.glyphs[c] for c in item)]
        if self.w.orderRadio.get() == 1 and data_key != "punctuation":
            valid.sort()
        return valid

    def generate(self, sender):
        font = Glyphs.font
        if not font: return
        p_ui_key = UI_GROUPS[self.w.primaryDropdown.get()]["key"]
        p_data_key = self.get_data_key(p_ui_key)
        selected_sec_keys = [self.get_data_key(k) for k, cb in self.checkboxes.items() if cb.get()]
        
        for sec_key in selected_sec_keys:
            if "numbers" in [p_data_key, sec_key]:
                self.generate_number_tab(font, p_data_key, sec_key)
            else:
                self.generate_standard_tab(font, p_data_key, sec_key)

    def generate_standard_tab(self, font, p_key, s_key):
        p_chars = self.get_filtered_chars(font, p_key)
        s_chars = self.get_filtered_chars(font, s_key)
        is_p_punc = "punctuation" in p_key
        p_label = next(g["label"] for g in UI_GROUPS if g["key"] in p_key or p_key == g["key"])
        s_label = next(g["label"] for g in UI_GROUPS if g["key"] in s_key or s_key == g["key"])
        lines = [f"--- {p_label} vs {s_label} ---"]

        l_ctrl, r_ctrl = ("", "") if is_p_punc else (DATA[p_key]["l_ctrl"], DATA[p_key]["r_ctrl"])
        if "UC" in p_key and "lc" in s_key: r_ctrl = DATA[s_key]["r_ctrl"]

        if is_p_punc or "punctuation" in s_key:
            wrapper_src = p_chars if is_p_punc else s_chars
            target_src = s_chars if is_p_punc else p_chars
            _, wrappers = self._get_flattened_and_wrappers(wrapper_src)
            flat_targets, _ = self._get_flattened_and_wrappers(target_src)
            for w_l, w_r in wrappers:
                wl_f, wr_f = self._handle_slash_punc(w_l), self._handle_slash_punc(w_r)
                line = " ".join(f"{l_ctrl}{wl_f}{t}{wr_f}{r_ctrl}" for t in flat_targets)
                lines.append(line)
        else:
            for p in p_chars:
                line = " ".join(f"{l_ctrl}{p}{s}{r_ctrl if 'lc' in s_key and 'UC' in p_key else p+r_ctrl}" for s in s_chars)
                lines.append(line)
        font.newTab("\n\n".join(lines))

    def generate_number_tab(self, font, p_key, s_key):
        variants = []
        for cfg in NUMBER_VARIANTS_CONFIG:
            suffix = cfg["suffix"]
            glyphs = [f"{n}{'.'+suffix if suffix else ''}" for n in NUMBER_BASE_NAMES if font.glyphs[f"{n}{'.'+suffix if suffix else ''}"]]
            if glyphs: variants.append({"label": cfg["label"], "glyphs": glyphs, "suffix": suffix})

        is_p_num = p_key == "numbers"
        is_p_punc = p_key == "punctuation"
        
        # Resolve clean labels for the secondary group
        if is_p_num or is_p_punc:
            sec_ui_key = s_key.split('_')[0]
            sec_label = next((g["label"] for g in UI_GROUPS if g["key"] == sec_ui_key), "Others")
        else:
            sec_label = "Numbers"

        all_lines = []
        for var in variants:
            # Fix Labeling
            p_title = var["label"] if is_p_num else ("Punctuation" if is_p_punc else "Letters")
            s_title = var["label"] if not is_p_num and not is_p_punc else sec_label
            all_lines.append(f"--- {p_title} vs {s_title} ---")
            
            z_fmt = self._format_glyph_name(f"zero{'.'+var['suffix'] if var['suffix'] else ''}")
            l_ctrl, r_ctrl = ("", "") if is_p_punc else (f"{z_fmt}{z_fmt}", f"{z_fmt}{z_fmt}")
            if not is_p_num and not is_p_punc:
                l_ctrl, r_ctrl = DATA[p_key]["l_ctrl"], DATA[p_key]["r_ctrl"]

            if "punctuation" in [p_key, s_key]:
                punc_data = self.get_filtered_chars(font, "punctuation")
                _, wrappers = self._get_flattened_and_wrappers(punc_data)
                if is_p_punc: 
                    for w_l, w_r in wrappers:
                        wl_f, wr_f = self._handle_slash_punc(w_l), self._handle_slash_punc(w_r)
                        line = " ".join(f"{wl_f}{self._format_glyph_name(n)}{wr_f}" for n in var["glyphs"])
                        all_lines.append(line)
                else: 
                    for n in var["glyphs"]:
                        n_f = self._format_glyph_name(n)
                        flat_punc, _ = self._get_flattened_and_wrappers(punc_data)
                        line = " ".join(f"{l_ctrl}{n_f}{self._handle_slash_punc(p)}{n_f}{r_ctrl}" for p in flat_punc)
                        all_lines.append(line)
            
            elif is_p_num and s_key == "numbers":
                for n1 in var["glyphs"]:
                    n1_f = self._format_glyph_name(n1)
                    line = " ".join(f"{l_ctrl}{n1_f}{self._format_glyph_name(n2)}{n1_f}{r_ctrl}" for n2 in var["glyphs"])
                    all_lines.append(line)

            elif is_p_num: # Numbers Primary vs Letters
                letter_chars = self.get_filtered_chars(font, s_key)
                for n in var["glyphs"]:
                    n_f = self._format_glyph_name(n)
                    line = " ".join(f"{l_ctrl}{n_f}{l}{n_f}{r_ctrl}" for l in letter_chars)
                    all_lines.append(line)
            else: # Letters Primary vs Numbers
                letter_chars = self.get_filtered_chars(font, p_key)
                for l in letter_chars:
                    line = " ".join(f"{l_ctrl}{l}{self._format_glyph_name(n)}{l}{r_ctrl}" for n in var["glyphs"])
                    all_lines.append(line)

        font.newTab("\n\n".join(all_lines))

if Glyphs.font:
    KerningUI()