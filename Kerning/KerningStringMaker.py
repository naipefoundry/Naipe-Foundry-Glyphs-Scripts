#MenuTitle: Kerning String Maker
# -*- coding: utf-8 -*-
__doc__="""
Creates kerning strings for Latin, Cyrillic, Numbers, or Punctuation and opens them in a new tab in Glyphs.
"""


import vanilla

# Define character groups
UC_LTN = "HILEFTKMNUJŊOQCGŒØDBPRÞAÆVWYXZSẞ"
lc_LTN = "nmuriıjȷŋhlłkoøœecðbpþqdgaætfvywxzsß"
UC_CYR = "НИПЏШЫІМЕЦЩДЈЮОФСЄЭЗВРЯГҐТЪЋЂБЬЊЛЉКЖХУЧАЅ"
lc_CYR = "нипџшыміцщдјюобфрћђесєэзвягґтьъњлљкжхчуаѕ"
Numbers = "0174253698"

# Define control characters
control_characters = {
    "UC_LTN": ("OH", "HO"),
    "lc_LTN": ("on", "no"),
    "UC_CYR": ("ОН", "НО"),
    "lc_CYR": ("он", "но"),
    "Numbers": ("00", "00"),
}

# Define punctuation patterns
punctuation_patterns = [
    ".", ",", ":", ";", "-", "_", "//", "\\", "¡!", "¿?", "()", "[]", "{}", 
    "‘’", "‚‘", "’", "‹›", "›‹", "*", "#", "&", "@", "©", "¶", "§", "№", "€", "£", "¥", "%", "‰", 
    "™", "ª", "º", "↑", "↗", "→", "☚", "☛", "❦"
]

class KerningUI:
    def __init__(self):
        # Create a floating window with title
        self.w = vanilla.FloatingWindow((300, 480), "Kerning String Maker")
        
        y = 10  # Track vertical position
        
        # Script selection
        self.w.text0 = vanilla.TextBox((10, y, -10, 20), "Writing system:")
        y += 25
        self.w.scriptRadio = vanilla.RadioGroup((10, y, -10, 40), ["Latin", "Cyrillic"], isVertical=False)
        self.w.scriptRadio.set(0)  # Default to "Latin"
        y += 45
        
        # Character order selection
        self.w.text_order = vanilla.TextBox((10, y, -10, 20), "Character order:")
        y += 25
        self.w.orderRadio = vanilla.RadioGroup((10, y, -10, 20), ["By Shape", "Alphabetical"], isVertical=False)
        self.w.orderRadio.set(0)  # Default to "By Shape"
        y += 30
        
        # Primary group dropdown
        self.w.text1 = vanilla.TextBox((10, y, -10, 20), "Kern this:")
        y += 25
        self.w.primaryDropdown = vanilla.PopUpButton((10, y, -10, 20), ["Upper case", "Lower case", "Numbers", "Punctuation and Symbols"])
        y += 35
        
        # Secondary group checkboxes
        self.w.text2 = vanilla.TextBox((10, y, -10, 20), "Against this:")
        y += 25
        self.w.secondaryCheckboxes = vanilla.Group((10, y, -10, 100))  # Increased the height to prevent clipping
        self.w.secondaryCheckboxes.cb_upper = vanilla.CheckBox((10, 0, -10, 20), "Upper case", value=True)
        self.w.secondaryCheckboxes.cb_lower = vanilla.CheckBox((10, 25, -10, 20), "Lower case", value=True)
        self.w.secondaryCheckboxes.cb_numbers = vanilla.CheckBox((10, 50, -10, 20), "Numbers", value=True)
        y += 105
        
        # Generate button
        self.w.button = vanilla.Button((60, y, 200, 20), "New tabs with Kerning Strings", callback=self.generateKerningStrings)
        y += 30
        
        # Set the window size to fit the content
        self.w.resize(300, y)  # Dynamically adjust height based on content
        
        self.w.open()

    def generateKerningStrings(self, sender):
        # Get user selections
        selected_script = self.w.scriptRadio.get()  # 0=Latin, 1=Cyrillic
        process_latin = selected_script == 0
        process_cyrillic = selected_script == 1
        
        alphabetical_order = self.w.orderRadio.get() == 1  # 0=By Shape, 1=Alphabetical
        
        # Determine primary group
        primary_index = self.w.primaryDropdown.get()
        primary_group_label = ["Upper case", "Lower case", "Numbers", "Punctuation and Symbols"][primary_index]
        
        # Map to internal group names
        if primary_group_label == "Lower case":
            primary_group_name = "lc_LTN" if process_latin else "lc_CYR" if process_cyrillic else None
        elif primary_group_label == "Upper case":
            primary_group_name = "UC_LTN" if process_latin else "UC_CYR" if process_cyrillic else None
        elif primary_group_label == "Punctuation and Symbols":
            primary_group_name = "punctuation_patterns"
        else:
            primary_group_name = "Numbers"

        # Determine secondary groups
        secondary_groups = []
        process_lower = self.w.secondaryCheckboxes.cb_lower.get()
        process_upper = self.w.secondaryCheckboxes.cb_upper.get()
        process_numbers = self.w.secondaryCheckboxes.cb_numbers.get()
        
        if process_latin:
            if process_lower: secondary_groups.append("lc_LTN")
            if process_upper: secondary_groups.append("UC_LTN")
        if process_cyrillic:
            if process_lower: secondary_groups.append("lc_CYR")
            if process_upper: secondary_groups.append("UC_CYR")
        if process_numbers: secondary_groups.append("Numbers")

        # Filter to avoid kerning Latin against Cyrillic
        if "lc_LTN" in secondary_groups and "lc_CYR" in secondary_groups:
            secondary_groups = [group for group in secondary_groups if group != "lc_CYR"]
        if "UC_LTN" in secondary_groups and "UC_CYR" in secondary_groups:
            secondary_groups = [group for group in secondary_groups if group != "UC_CYR"]

        # Get font reference
        font = Glyphs.font
        if not font:
            Message("No font open in Glyphs.", title="Error")
            return

        # Generate tabs for each combination
        for secondary_group in secondary_groups:
            lines = [f"--- {primary_group_label} vs {secondary_group.replace('_', ' ')} ---"]
            
            # Get control characters
            left_ctrl, right_ctrl = control_characters.get(secondary_group, ("", ""))
            if primary_group_name == "Numbers":
                left_ctrl, right_ctrl = control_characters.get(secondary_group, ("", ""))
            else:
                left_ctrl, right_ctrl = control_characters.get(primary_group_name, ("", ""))

            # Get characters (sorted if needed)
            if primary_group_name == "punctuation_patterns":
                primary_chars = punctuation_patterns
            else:
                primary_chars = sorted(globals()[primary_group_name]) if alphabetical_order else globals()[primary_group_name]
            
            secondary_chars = sorted(globals()[secondary_group]) if alphabetical_order else globals()[secondary_group]

            # Generate kerning pairs
            for char1 in primary_chars:
                if primary_group_name == "punctuation_patterns":
                    if len(char1) == 2:  # Handle paired punctuation like () or []
                        line = char1[0] + "".join(f"{char}{char1[1]}{char1[0]}" for char in secondary_chars[:-1]) + f"{secondary_chars[-1]}{char1[1]}"
                    else:  # Handle single-character punctuation
                        line = char1 + "".join(f"{char}{char1}" for char in secondary_chars)
                else:
                    if "UC" in primary_group_name and "lc" in secondary_group:  # Upper case vs lower case (script-agnostic)
                        line = " ".join(f"{left_ctrl}{char1}{char2}{control_characters.get(secondary_group, ('', ''))[1]}" for char2 in secondary_chars)
                    else:
                        line = " ".join(f"{left_ctrl}{char1}{char2}{char1}{right_ctrl}" for char2 in secondary_chars)
                lines.append(line)
            
            # Create new tab with DOUBLE line breaks
            font.newTab("\n\n".join(lines))  # Changed to \n\n

# Launch the UI
KerningUI()
