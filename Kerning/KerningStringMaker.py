#MenuTitle: Kerning String Maker
# -*- coding: utf-8 -*-
__doc__="""
Creates kerning strings for Latin, Cyrillic, Numbers, or Punctuation and opens them in a new tab in Glyphs.
"""

import vanilla

# -----------------------------
# Configuration
# -----------------------------

# Base glyph names for numbers (in kerning order, not numerical)
NUMBER_BASE_NAMES = ["zero", "one", "seven", "four", "two", "five", "three", "six", "nine", "eight"]

# Number variant configuration (order matters - tabular last!)
NUMBER_VARIANTS_CONFIG = [
    {"suffix": None, "label": "Default Numbers", "order": 1},
    {"suffix": "lf", "label": "Lining Figures", "order": 2},
    {"suffix": "osf", "label": "Old Style Figures", "order": 3},
    {"suffix": "dnom", "label": "Denominators", "order": 4},
    {"suffix": "numr", "label": "Numerators", "order": 5},
    {"suffix": "sinf", "label": "Inferiors", "order": 6},
    {"suffix": "numr", "label": "Superiors", "order": 7},
    {"suffix": "tf", "label": "Tabular Figures", "order": 8, "warning": "!!! Tabular figures ahead, do not kern !!!"},
    {"suffix": "tosf", "label": "Tabular Old Style Figures", "order": 9},
]

# Unified character group definitions
CHARACTER_GROUPS = {
    "UC_LTN": {
        "chars": "HILEFTKMNUƯJŊOƠQCGŒØDƏBPRÞAÆVWYXZSẞ",
        "control": ("OH", "HO"),
        "label": "Latin Upper-Case"
    },
    "lc_LTN": {
        "chars": "nmuưriıjȷŋhlłkoơøœeəcðbpþqdďđħgaætŧťfvywxzsß",
        "control": ("on", "no"),
        "label": "Latin Lower-Case"
    },
    "UC_CYR": {
        "chars": "НИПЏШЫІМЕЦЩДЈЮОФСЄЭЗВРЯГҐТЪЋЂБЬЊЛЉКЖХУЧАЅ",
        "control": ("ОН", "НО"),
        "label": "Cyrillic Upper-Case"
    },
    "lc_CYR": {
        "chars": "нипџшыміцщдјюобфрћђесєэзвягґтьъњлљкжхчуаѕ",
        "control": ("он", "но"),
        "label": "Cyrillic Lower-Case"
    },
    "punctuation_patterns": {
        "chars": [
            ".", ",", ":", ";", "-", "_", "//", "\\", "¡!", "¿?", "()", "[]", "{}",
            "‘’", "‚‘", "’", "\"\"", "\'\'", "‹›", "›‹", "*", "#", "&", "@", "©", "®", "¶", "§", "№",
            "$", "€", "£", "¥", "₦", "₹", "₩", "฿", "₫", "¢", "₴", "₽", "%", "‰", "†", "‡",
            "™", "ª", "º", "®", "↑", "↓", "↖", "↙", "←", "→", "↘", "↗", "☚", "☛", "❦", "<>"
        ],
        "control": ("", ""),
        "label": "Punctuation and Symbols"
    }
}

# -----------------------------
# Helper Functions
# -----------------------------

def filter_existing_chars(font, char_string):
    """Filter character string to only include glyphs present in font."""
    return "".join(c for c in char_string if font.glyphs[c] is not None)

def detect_number_variants(font):
    """
    Detect which number variants exist in the font.
    Returns a list of dicts with variant info, sorted by order.
    """
    variants = []
    
    for config in NUMBER_VARIANTS_CONFIG:
        suffix = config["suffix"]
        variant_nums = []
        missing_nums = []
        
        for name in NUMBER_BASE_NAMES:
            glyph_name = name if suffix is None else f"{name}.{suffix}"
            if font.glyphs[glyph_name]:
                variant_nums.append(f"/{glyph_name} ")
            else:
                missing_nums.append(name)
        
        if variant_nums:
            variant_data = {
                "suffix": suffix,
                "label": config["label"],
                "glyphs": variant_nums,
                "order": config["order"],
                "warning": config.get("warning")
            }
            variants.append(variant_data)
            
            if missing_nums:
                print(f"{config['label']}: Missing {', '.join(missing_nums)}")
    
    # Sort by order
    variants.sort(key=lambda x: x["order"])
    return variants

def get_control_chars_for_numbers(variant_suffix):
    """Get appropriate control characters for a number variant."""
    if variant_suffix is None:
        return ("/zero ", "/zero ")
    else:
        return (f"/zero.{variant_suffix} ", f"/zero.{variant_suffix} ")

# -----------------------------
# Initialize font data
# -----------------------------

font = Glyphs.font

if font:
    # Filter character groups to only existing glyphs
    for group_key in ["UC_LTN", "lc_LTN", "UC_CYR", "lc_CYR"]:
        original = CHARACTER_GROUPS[group_key]["chars"]
        CHARACTER_GROUPS[group_key]["chars"] = filter_existing_chars(font, original)
    
    # Detect number variants
    NUMBER_VARIANTS = detect_number_variants(font)
    
    print("--- AVAILABLE NUMBER VARIANTS ---")
    for variant in NUMBER_VARIANTS:
        print(f"{variant['label']}: {len(variant['glyphs'])} glyphs")

# -----------------------------
# UI
# -----------------------------

class KerningUI:
    def __init__(self):
        self.w = vanilla.FloatingWindow((300, 480), "Kerning String Maker")
        
        y = 10
        
        # Script selection
        self.w.text0 = vanilla.TextBox((10, y, -10, 20), "Writing system:")
        y += 25
        self.w.scriptRadio = vanilla.RadioGroup((10, y, -10, 40), ["Latin", "Cyrillic"], isVertical=False)
        self.w.scriptRadio.set(0)
        y += 45
        
        # Character order
        self.w.text_order = vanilla.TextBox((10, y, -10, 20), "Character order:")
        y += 25
        self.w.orderRadio = vanilla.RadioGroup((10, y, -10, 20), ["By Shape", "Alphabetical"], isVertical=False)
        self.w.orderRadio.set(0)
        y += 30
        
        # Primary group
        self.w.text1 = vanilla.TextBox((10, y, -10, 20), "Kern this:")
        y += 25
        self.w.primaryDropdown = vanilla.PopUpButton(
            (10, y, -10, 20),
            ["Upper case", "Lower case", "Numbers", "Punctuation and Symbols"]
        )
        y += 35
        
        # Secondary group checkboxes
        self.w.text2 = vanilla.TextBox((10, y, -10, 20), "Against this:")
        y += 25
        self.w.secondaryCheckboxes = vanilla.Group((10, y, -10, 100))
        self.w.secondaryCheckboxes.cb_upper = vanilla.CheckBox((10, 0, -10, 20), "Upper case", value=True)
        self.w.secondaryCheckboxes.cb_lower = vanilla.CheckBox((10, 25, -10, 20), "Lower case", value=True)
        self.w.secondaryCheckboxes.cb_numbers = vanilla.CheckBox((10, 50, -10, 20), "Numbers", value=True)
        y += 105
        
        # Generate button
        self.w.button = vanilla.Button((60, y, 200, 20), "New tabs with Kerning Strings", callback=self.generateKerningStrings)
        y += 30
        
        self.w.resize(300, y)
        self.w.open()

    def generateKerningStrings(self, sender):
        font = Glyphs.font
        if not font:
            Message("No font open in Glyphs.", title="Error")
            return
        
        # Get user selections
        selected_script = self.w.scriptRadio.get()
        process_latin = selected_script == 0
        process_cyrillic = selected_script == 1
        alphabetical_order = self.w.orderRadio.get() == 1
        
        primary_index = self.w.primaryDropdown.get()
        primary_label = ["Upper case", "Lower case", "Numbers", "Punctuation and Symbols"][primary_index]
        
        # Determine primary group
        if primary_label == "Lower case":
            primary_group = "lc_LTN" if process_latin else "lc_CYR"
        elif primary_label == "Upper case":
            primary_group = "UC_LTN" if process_latin else "UC_CYR"
        elif primary_label == "Punctuation and Symbols":
            primary_group = "punctuation_patterns"
        else:
            primary_group = "Numbers"
        
        # Determine secondary groups
        secondary_groups = []
        if self.w.secondaryCheckboxes.cb_lower.get():
            secondary_groups.append("lc_LTN" if process_latin else "lc_CYR")
        if self.w.secondaryCheckboxes.cb_upper.get():
            secondary_groups.append("UC_LTN" if process_latin else "UC_CYR")
        if self.w.secondaryCheckboxes.cb_numbers.get():
            secondary_groups.append("Numbers")
        
        # Avoid mixing Latin and Cyrillic
        if process_latin:
            secondary_groups = [g for g in secondary_groups if "CYR" not in g]
        if process_cyrillic:
            secondary_groups = [g for g in secondary_groups if "LTN" not in g]
        
        # Generate strings
        if primary_group == "Numbers":
            self._generate_numbers_primary(secondary_groups, alphabetical_order)
        else:
            self._generate_standard_primary(primary_group, primary_label, secondary_groups, alphabetical_order)
    
    def _generate_standard_primary(self, primary_group, primary_label, secondary_groups, alphabetical_order):
        """Generate kerning strings when Numbers is NOT the primary group."""
        font = Glyphs.font
        
        # Get primary characters
        if primary_group == "punctuation_patterns":
            primary_chars = CHARACTER_GROUPS[primary_group]["chars"]
        else:
            primary_data = CHARACTER_GROUPS[primary_group]["chars"]
            if not primary_data:
                Message(f"{CHARACTER_GROUPS[primary_group]['label']} is empty.", title="Empty Group")
                return
            primary_chars = sorted(primary_data) if alphabetical_order else primary_data
        
        for secondary_group in secondary_groups:
            if secondary_group == "Numbers":
                # Generate single tab with all number variants
                self._generate_tab_primary_vs_all_numbers(
                    primary_group, primary_label, primary_chars, alphabetical_order
                )
            else:
                # Standard unicode-based group
                secondary_data = CHARACTER_GROUPS[secondary_group]["chars"]
                if not secondary_data:
                    continue
                
                secondary_chars = sorted(secondary_data) if alphabetical_order else secondary_data
                self._generate_standard_tab(
                    primary_group, primary_label, primary_chars,
                    secondary_group, secondary_chars
                )
    
    def _generate_tab_primary_vs_all_numbers(self, primary_group, primary_label, primary_chars, alphabetical_order):
        """Generate a single tab with all number variants separated by labels."""
        all_sections = []
        
        for variant in NUMBER_VARIANTS:
            # Add warning label if this is tabular
            if variant.get("warning"):
                all_sections.append(f"\n\n{variant['warning']}\n")
            
            # Add variant label
            all_sections.append(f"--- {variant['label']} vs {primary_label} ---\n")
            
            left_ctrl, right_ctrl = CHARACTER_GROUPS[primary_group]["control"]
            
            for char1 in primary_chars:
                if primary_group == "punctuation_patterns":
                    if len(char1) == 2:
                        line = char1[0] + "".join(f"{num}{char1[1]}{char1[0]}" for num in variant['glyphs'][:-1]) + f"{variant['glyphs'][-1]}{char1[1]}"
                    else:
                        line = char1 + "".join(f"{num}{char1}" for num in variant['glyphs'])
                else:
                    line = " ".join(f"{left_ctrl}{char1}{num}{char1}{right_ctrl}" for num in variant['glyphs'])
                all_sections.append(line)
        
        Glyphs.font.newTab("\n\n".join(all_sections))
    
    def _generate_standard_tab(self, primary_group, primary_label, primary_chars, secondary_group, secondary_chars):
        """Generate a standard tab for non-number groups."""
        lines = [f"--- {primary_label} vs {CHARACTER_GROUPS[secondary_group]['label']} ---\n"]
        
        left_ctrl, right_ctrl = CHARACTER_GROUPS[primary_group]["control"]
        
        for char1 in primary_chars:
            if primary_group == "punctuation_patterns":
                if len(char1) == 2:
                    line = char1[0] + "".join(f"{char2}{char1[1]}{char1[0]}" for char2 in secondary_chars[:-1]) + f"{secondary_chars[-1]}{char1[1]}"
                else:
                    line = char1 + "".join(f"{char2}{char1}" for char2 in secondary_chars)
            else:
                if "UC" in primary_group and "lc" in secondary_group:
                    sec_ctrl = CHARACTER_GROUPS[secondary_group]["control"]
                    line = " ".join(f"{left_ctrl}{char1}{char2}{sec_ctrl[1]}" for char2 in secondary_chars)
                else:
                    line = " ".join(f"{left_ctrl}{char1}{char2}{char1}{right_ctrl}" for char2 in secondary_chars)
            lines.append(line)
        
        Glyphs.font.newTab("\n\n".join(lines))
    
    def _generate_numbers_primary(self, secondary_groups, alphabetical_order):
        """Generate kerning strings when Numbers IS the primary group."""
        font = Glyphs.font
        
        if not NUMBER_VARIANTS:
            Message("No number glyphs found in font.", title="Empty Group")
            return
        
        for secondary_group in secondary_groups:
            if secondary_group == "Numbers":
                # Numbers vs Numbers: single tab with all variants
                self._generate_numbers_vs_numbers_tab()
            else:
                # Numbers vs other groups: single tab with all variants
                secondary_data = CHARACTER_GROUPS[secondary_group]["chars"]
                if not secondary_data:
                    continue
                
                secondary_chars = sorted(secondary_data) if alphabetical_order else secondary_data
                self._generate_numbers_vs_group_tab(secondary_group, secondary_chars)
    
    def _generate_numbers_vs_numbers_tab(self):
        """Generate single tab with all Numbers vs Numbers variants."""
        all_sections = []
        
        for variant in NUMBER_VARIANTS:
            # Add warning label if this is tabular
            if variant.get("warning"):
                all_sections.append(f"\n\n{variant['warning']}\n")
            
            # Add variant label
            all_sections.append(f"--- {variant['label']} vs {variant['label']} ---\n")
            
            left_ctrl, right_ctrl = get_control_chars_for_numbers(variant['suffix'])
            
            for num1 in variant['glyphs']:
                line = " ".join(f"{left_ctrl}{num1}{num2}{num1}{right_ctrl}" for num2 in variant['glyphs'])
                all_sections.append(line)
        
        Glyphs.font.newTab("\n\n".join(all_sections))
    
    def _generate_numbers_vs_group_tab(self, secondary_group, secondary_chars):
        """Generate single tab with all number variants vs a group."""
        all_sections = []
        secondary_label = CHARACTER_GROUPS[secondary_group]["label"]
        
        for variant in NUMBER_VARIANTS:
            # Add warning label if this is tabular
            if variant.get("warning"):
                all_sections.append(f"\n\n{variant['warning']}\n")
            
            # Add variant label
            all_sections.append(f"--- {variant['label']} vs {secondary_label} ---\n")
            
            left_ctrl, right_ctrl = get_control_chars_for_numbers(variant['suffix'])
            
            for num in variant['glyphs']:
                line = " ".join(f"{left_ctrl}{num}{char}{num}{right_ctrl}" for char in secondary_chars)
                all_sections.append(line)
        
        Glyphs.font.newTab("\n\n".join(all_sections))

# Launch the UI
if font:
    KerningUI()
else:
    Message("Please open a font first.", title="No Font Open")