# MenuTitle: Word Filter
# -*- coding: utf-8 -*-
__doc__="""
Filter words from a paragraph using specified characters, with include/exclude and case-sensitive options.
"""

import vanilla
import re
from AppKit import NSFont

class WordFilterApp:
    def __init__(self):
        # Create resizable window
        self.w = vanilla.FloatingWindow(
            (600, 460),       # default window size
            "Word Filter",
            minSize=(400, 350),
            maxSize=(2000, 2000)
        )

        # Label for paragraph input
        self.w.inputLabel = vanilla.TextBox(
            (10, 10, -10, 20),
            "📝 Input paragraph:"
        )

        # Input text box
        self.w.inputText = vanilla.TextEditor((10, 30, -10, 140), "")
        self._make_plain_text(self.w.inputText)

        # Label for character input
        self.w.charLabel = vanilla.TextBox(
            (10, 180, -10, 20),
            "🔠 Characters to filter for:"
        )

        # Characters input field
        self.w.charsInput = vanilla.EditText(
            (10, 200, -10, 22),
            ""
        )

        # Label for mode selection
        self.w.modeLabel = vanilla.TextBox(
            (10, 230, -10, 20),
            "🎯 Find words that:"
        )

        # Mode radio buttons (horizontal)
        self.w.modeRadio = vanilla.RadioGroup(
            (10, 255, -10, 20),
            ["✅ Use only these characters", "🚫 Do not use these characters"],
            isVertical=False
        )
        self.w.modeRadio.set(1)  # Default: Do not use these characters

        # Case sensitivity checkbox
        self.w.caseCheckbox = vanilla.CheckBox(
            (10, 285, -10, 20),
            "🔡 Case Sensitive: Match Exact Case",
            value=False
        )

        # Filter button
        self.w.filterButton = vanilla.Button(
            (10, 315, -10, 20),
            "✨ Filter Words",
            callback=self.filter_words
        )

        # Label for output
        self.w.outputLabel = vanilla.TextBox(
            (10, 345, -10, 20),
            "📋 Filtered output:"
        )

        # Output text box
        self.w.outputText = vanilla.TextEditor((10, 365, -10, -10), "", readOnly=True)
        self._make_plain_text(self.w.outputText)

        # Open window
        self.w.open()
        self.w.makeKey()

    def _make_plain_text(self, text_editor):
        """Set the TextEditor to plain text and use a sans-serif font."""
        tv = text_editor.getNSTextView()
        tv.setRichText_(False)
        tv.setFont_(NSFont.systemFontOfSize_(12))

    def filter_words(self, sender):
        text = self.w.inputText.get()
        chars = self.w.charsInput.get()

        # Options
        mode = self.w.modeRadio.get()              # 0 = Use only, 1 = Do not use
        case_sensitive = self.w.caseCheckbox.get()

        # Prepare character set
        if not case_sensitive:
            chars_set = set(chars.lower())
        else:
            chars_set = set(chars)

        # Split words ignoring punctuation
        words = re.findall(r'\b\w+\b', text)

        filtered_words = []
        for word in words:
            check_word = word if case_sensitive else word.lower()
            has_char = any(c in chars_set for c in check_word)
            all_chars_allowed = all(c in chars_set for c in check_word)

            if mode == 0:  # Use only these characters
                if all_chars_allowed:
                    filtered_words.append(word)
            else:          # Do not use these characters
                if not has_char:
                    filtered_words.append(word)

        # Output result
        self.w.outputText.set(" ".join(filtered_words))


# Run the app
WordFilterApp()
