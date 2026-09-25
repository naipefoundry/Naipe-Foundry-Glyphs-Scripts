# MenuTitle: Interpolate Kerning Between Masters
# encoding: utf-8

"""
Run this in the Glyphs Macro Panel (or save it as a script and run from the Script menu).

Pick two reference masters (A and B) and a target master. The script looks at
which axis A and B differ on, finds the target's position on that same axis,
and uses the resulting ratio to interpolate (if the target sits between A and B)
or extrapolate (if it sits outside that range) every kerning pair value.

Pairs that exist in A and/or B but not yet in the target are added; pairs that
already exist in the target are overwritten.
"""

from GlyphsApp import Glyphs
import vanilla


def get_axis_index(masterA, masterB):
    """Return the index of the axis on which masterA and masterB differ.
    If they differ on more than one axis, returns the one with the largest
    absolute difference (and warns). Returns None if they don't differ at all."""
    font = masterA.font
    diffs = []
    for i in range(len(font.axes)):
        a = float(masterA.axes[i])
        b = float(masterB.axes[i])
        if abs(a - b) > 1e-6:
            diffs.append((i, abs(a - b)))
    if not diffs:
        return None, diffs
    diffs.sort(key=lambda x: -x[1])
    return diffs[0][0], diffs


def compute_t(masterA, masterB, target, axis_index):
    """Compute interpolation factor t such that:
        value = valueA + t * (valueB - valueA)
    t == 0 at A, t == 1 at B. t outside [0,1] means extrapolation."""
    a = float(masterA.axes[axis_index])
    b = float(masterB.axes[axis_index])
    x = float(target.axes[axis_index])
    if abs(b - a) < 1e-6:
        return None
    return (x - a) / (b - a)


def collect_kerning_dict(font, master_id, rtl=False):
    """Return font.kerning[master_id] (or kerningRTL) as a plain dict, or {} if empty."""
    store = font.kerningRTL if rtl else font.kerning
    if store is None:
        return {}
    d = store.get(master_id)
    if d is None:
        return {}
    return d


def all_pairs(dict_a, dict_b):
    """Union of (left, right) keys present in either kerning dict."""
    pairs = set()
    for left, rights in dict_a.items():
        for right in rights.keys():
            pairs.add((left, right))
    for left, rights in dict_b.items():
        for right in rights.keys():
            pairs.add((left, right))
    return pairs


def run_interpolation(font, masterA, masterB, target):
    axis_index, diffs = get_axis_index(masterA, masterB)

    if axis_index is None:
        print("Reference masters A and B are at the same position on every axis — nothing to interpolate along.")
        return

    if len(diffs) > 1:
        axis_name = font.axes[axis_index].name
        others = ", ".join(font.axes[i].name for i, _ in diffs[1:])
        print("Note: masters A and B differ on more than one axis (%s). Using '%s', the axis with the largest difference, and ignoring the rest." % (
            ", ".join(font.axes[i].name for i, _ in diffs), axis_name))

    t = compute_t(masterA, masterB, target, axis_index)
    if t is None:
        print("Could not compute a ratio — masters A and B have identical values on the chosen axis.")
        return

    mode = "interpolating" if 0.0 <= t <= 1.0 else "extrapolating"
    axis_name = font.axes[axis_index].name
    print("Axis: %s   A=%s  B=%s  Target=%s   t=%.4f   (%s)" % (
        axis_name,
        masterA.axes[axis_index], masterB.axes[axis_index], target.axes[axis_index],
        t, mode
    ))

    total_written = 0
    total_skipped = 0

    for rtl in (False, True):
        dict_a = collect_kerning_dict(font, masterA.id, rtl=rtl)
        dict_b = collect_kerning_dict(font, masterB.id, rtl=rtl)

        pairs = all_pairs(dict_a, dict_b)
        if not pairs:
            continue

        for left, right in pairs:
            val_a = dict_a.get(left, {}).get(right)
            val_b = dict_b.get(left, {}).get(right)

            if val_a is None and val_b is None:
                continue
            elif val_a is None:
                # Only present in B — can't interpolate a slope, just carry B's value through.
                new_val = float(val_b)
            elif val_b is None:
                # Only present in A — carry A's value through.
                new_val = float(val_a)
            else:
                val_a = float(val_a)
                val_b = float(val_b)
                new_val = val_a + t * (val_b - val_a)

            new_val = round(new_val)

            try:
                if rtl:
                    font.setKerningRTLForPair(target.id, left, right, new_val)
                else:
                    font.setKerningForPair(target.id, left, right, new_val)
                total_written += 1
            except Exception as e:
                total_skipped += 1
                print("  Skipped pair (%s, %s): %s" % (left, right, e))

    print("Done. Wrote %d kerning pair(s) to '%s'%s." % (
        total_written, target.name, (" (%d skipped)" % total_skipped) if total_skipped else ""
    ))


class KerningInterpolatorUI(object):

    def __init__(self):
        self.font = Glyphs.font
        if self.font is None:
            print("No font open.")
            return

        self.masters = list(self.font.masters)
        master_names = [m.name for m in self.masters]

        if len(self.masters) < 3:
            print("This font needs at least 3 masters (two references + one target).")
            return

        width = 320
        margin = 14
        row_h = 24
        gap = 10

        height = margin * 2 + row_h * 4 + gap * 3 + 40

        self.w = vanilla.FloatingWindow((width, height), "Kerning Interpolator / Extrapolator")

        y = margin
        self.w.labelA = vanilla.TextBox((margin, y + 4, 90, row_h), "Master A:")
        self.w.popupA = vanilla.PopUpButton((margin + 90, y, width - margin * 2 - 90, row_h), master_names,
                                             callback=self.selectionChanged)
        y += row_h + gap

        self.w.labelB = vanilla.TextBox((margin, y + 4, 90, row_h), "Master B:")
        self.w.popupB = vanilla.PopUpButton((margin + 90, y, width - margin * 2 - 90, row_h), master_names,
                                             callback=self.selectionChanged)
        y += row_h + gap

        self.w.labelTarget = vanilla.TextBox((margin, y + 4, 90, row_h), "Target:")
        self.w.popupTarget = vanilla.PopUpButton((margin + 90, y, width - margin * 2 - 90, row_h), master_names,
                                                  callback=self.selectionChanged)
        y += row_h + gap

        self.w.statusText = vanilla.TextBox((margin, y, width - margin * 2, row_h), "", sizeStyle="small")
        y += row_h + gap

        self.w.runButton = vanilla.Button((margin, y, width - margin * 2, 30), "Run", callback=self.runCallback)

        # sensible defaults: A=0, B=1, Target=2 (or last master if only 3)
        self.w.popupA.set(0)
        self.w.popupB.set(1)
        self.w.popupTarget.set(len(self.masters) - 1)

        self.updateStatus()
        self.w.open()

    def selectionChanged(self, sender):
        self.updateStatus()

    def updateStatus(self):
        idxA = self.w.popupA.get()
        idxB = self.w.popupB.get()
        idxT = self.w.popupTarget.get()

        if idxA == idxB:
            self.w.statusText.set("⚠️ Master A and B must be different.")
            return
        if idxT == idxA or idxT == idxB:
            self.w.statusText.set("⚠️ Target should differ from A and B.")
            return

        masterA = self.masters[idxA]
        masterB = self.masters[idxB]
        target = self.masters[idxT]

        axis_index, diffs = get_axis_index(masterA, masterB)
        if axis_index is None:
            self.w.statusText.set("⚠️ A and B are identical on every axis.")
            return

        t = compute_t(masterA, masterB, target, axis_index)
        axis_name = self.font.axes[axis_index].name
        if t is None:
            self.w.statusText.set("⚠️ Cannot compute ratio on '%s'." % axis_name)
        elif 0.0 <= t <= 1.0:
            self.w.statusText.set("Will interpolate on '%s'  (t=%.2f)" % (axis_name, t))
        else:
            self.w.statusText.set("Will extrapolate on '%s'  (t=%.2f)" % (axis_name, t))

    def runCallback(self, sender):
        idxA = self.w.popupA.get()
        idxB = self.w.popupB.get()
        idxT = self.w.popupTarget.get()

        if idxA == idxB:
            print("Master A and B must be different masters.")
            return
        if idxT == idxA or idxT == idxB:
            print("Target master should be different from A and B.")
            return

        masterA = self.masters[idxA]
        masterB = self.masters[idxB]
        target = self.masters[idxT]

        print("--- Kerning Interpolator / Extrapolator ---")
        run_interpolation(self.font, masterA, masterB, target)

        self.w.close()


KerningInterpolatorUI()
