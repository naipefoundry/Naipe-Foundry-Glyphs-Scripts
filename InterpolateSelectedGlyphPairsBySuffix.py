# MenuTitle: Interpolate Selected Glyph Pairs By Suffix
# encoding: utf-8
"""
Glyph Interpolator — Batch / Selection Mode
────────────────────────────────────────────
Select a mix of base glyphs and their stylistic-set variants in the Font
view, configure the source suffix, output suffix, and interpolation factor,
then press Interpolate.

Example: select  a  a.ss01  c  c.ss01  e  e.ss01
         source suffix  = .ss01   (the "100" end)
         output suffix  = .ss02
         → creates a.ss02  c.ss02  e.ss02  at the chosen factor

Handles:
  - Regular path outlines (nodes interpolated)
  - Corner components (_corner.*) — scale and position interpolated
  - Regular components — position interpolated, name taken from glyph A
  - Anchors (matched by name)
  - Advance width

Glyphs with no base counterpart (or no source-suffix counterpart) in the
selection are skipped and listed in the status area.

Run from Glyphs: Script menu after placing this file in your Scripts folder.
Requires: Glyphs 3 with vanilla (ships with Glyphs).
"""

from __future__ import division
import traceback

import vanilla
from GlyphsApp import Glyphs, GSGlyph, GSLayer, GSPath, GSNode, GSAnchor, GSComponent, Message


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _lerp(a, b, t):
    return a + t * (b - a)


def _is_corner_or_cap(component):
    """True for _corner.* and _cap.* components (not regular glyph refs)."""
    name = component.componentName or ""
    return name.startswith("_corner.") or name.startswith("_cap.")


def _get_transform(component):
    """Return the 6-tuple affine transform of a GSComponent."""
    t = component.transform
    # In Glyphs 3 this is already a tuple; guard for NSAffineTransformStruct
    if hasattr(t, 'transformStruct'):
        s = t.transformStruct
        return (s.m11, s.m12, s.m21, s.m22, s.tX, s.tY)
    return tuple(t)


def _set_transform(component, tx):
    """Set a 6-tuple affine transform on a GSComponent."""
    component.transform = tx


# ─────────────────────────────────────────────────────────────────────────────
# Anchor interpolation
# ─────────────────────────────────────────────────────────────────────────────

def _interpolate_anchors(anchors_a, anchors_b, t):
    map_b = {a.name: a for a in anchors_b}
    result = []
    for aa in anchors_a:
        if aa.name in map_b:
            ab = map_b[aa.name]
            anc = GSAnchor()
            anc.name = aa.name
            anc.position = (
                _lerp(aa.position.x, ab.position.x, t),
                _lerp(aa.position.y, ab.position.y, t),
            )
            result.append(anc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Per-layer shapes walk
# ─────────────────────────────────────────────────────────────────────────────

def _interpolate_layer_shapes(layer_a, layer_b, t):
    """
    Walk layer.shapes (GSPath and GSComponent objects in order) and
    interpolate each shape by type.

    Returns (paths, components) lists ready to append to the output layer.

    Strategy:
      - Collect shapes into typed buckets preserving order.
      - Paths are interpolated node-by-node.
      - Components (including corners) are interpolated transform-by-transform.
      - The shape *order* must be the same in both layers (standard Glyphs
        interpolation requirement).
    """
    shapes_a = list(layer_a.shapes)
    shapes_b = list(layer_b.shapes)

    if len(shapes_a) != len(shapes_b):
        raise ValueError(
            "Shape count mismatch: layer A has %d shape(s), layer B has %d. "
            "Both layers must be interpolation-compatible."
            % (len(shapes_a), len(shapes_b))
        )

    out_shapes = []  # single ordered list — preserves interleaving of paths and corners

    for idx, (sa, sb) in enumerate(zip(shapes_a, shapes_b)):
        type_a = type(sa).__name__
        type_b = type(sb).__name__

        if type_a != type_b:
            raise ValueError(
                "Shape type mismatch at index %d: '%s' vs '%s'."
                % (idx, type_a, type_b)
            )

        if isinstance(sa, GSPath):
            nodes_a = list(sa.nodes)
            nodes_b = list(sb.nodes)
            if len(nodes_a) != len(nodes_b):
                raise ValueError(
                    "Node count mismatch on path %d: %d vs %d nodes."
                    % (idx, len(nodes_a), len(nodes_b))
                )
            new_path = GSPath()
            new_path.closed = sa.closed
            for na, nb in zip(nodes_a, nodes_b):
                if str(na.type) != str(nb.type):
                    raise ValueError(
                        "Node type mismatch on path %d: '%s' vs '%s'."
                        % (idx, na.type, nb.type)
                    )
                node = GSNode()
                node.position = (
                    _lerp(na.position.x, nb.position.x, t),
                    _lerp(na.position.y, nb.position.y, t),
                )
                node.type = na.type
                new_path.nodes.append(node)
            out_shapes.append(new_path)

        elif isinstance(sa, GSComponent):
            if sa.componentName != sb.componentName:
                raise ValueError(
                    "Component name mismatch at shape %d: '%s' vs '%s'."
                    % (idx, sa.componentName, sb.componentName)
                )
            ta = _get_transform(sa)
            tb = _get_transform(sb)
            ti = tuple(_lerp(ta[i], tb[i], t) for i in range(6))
            new_comp = GSComponent(sa.componentName)
            _set_transform(new_comp, ti)
            try:
                new_comp.disableAlignment = sa.disableAlignment
            except Exception:
                pass
            out_shapes.append(new_comp)

    return out_shapes


# ─────────────────────────────────────────────────────────────────────────────
# Corner/cap hint interpolation
# ─────────────────────────────────────────────────────────────────────────────

# GSHint type constants
CORNER_TYPE = 16   # matches type=16 seen in debug output (CORNER)
CAP_TYPE    = 17   # CAP hints use the same structure

def _node_key(node):
    """Stable key for matching a node across two compatible layers by position."""
    return (round(node.position.x, 1), round(node.position.y, 1))


def _interpolate_hints(layer_a, layer_b, layer_out, t):
    """
    Copy CORNER and CAP hints from layer_a to layer_out, interpolating
    their scale between layer_a and layer_b.

    Matching between layers is done by (hint.name, originNode position) —
    the same corner on the same node in both layers.

    Hints are attached to nodes on layer_out by finding the output node
    at the same (interpolated) position.
    """
    from GlyphsApp import GSHint

    hints_a = [h for h in layer_a.hints if h.type in (CORNER_TYPE, CAP_TYPE)]
    if not hints_a:
        return

    # Build a lookup of layer_b hints by (name, node_pos) for scale matching
    hints_b_map = {}
    for h in layer_b.hints:
        if h.type in (CORNER_TYPE, CAP_TYPE) and h.originNode is not None:
            key = (h.name, _node_key(h.originNode))
            hints_b_map[key] = h

    # Build a lookup of output layer nodes by their interpolated position
    # so we can re-attach hints to the correct node
    out_nodes = {}
    for path in layer_out.paths:
        for node in path.nodes:
            out_nodes[_node_key(node)] = node

    for ha in hints_a:
        if ha.originNode is None:
            continue

        node_pos_a = _node_key(ha.originNode)

        # Find the matching hint in layer_b
        key = (ha.name, node_pos_a)
        hb = hints_b_map.get(key)

        # Interpolate scale — CGPoint with x and y
        scale_ax = ha.scale.x
        scale_ay = ha.scale.y
        if hb is not None:
            scale_bx = hb.scale.x
            scale_by = hb.scale.y
        else:
            # No match in B — keep A's scale unchanged
            scale_bx = scale_ax
            scale_by = scale_ay

        interp_sx = _lerp(scale_ax, scale_bx, t)
        interp_sy = _lerp(scale_ay, scale_by, t)

        # Find the corresponding node on the output layer.
        # The output node sits at the interpolated position of node_a.
        # We compute that position to look it up.
        if hb is not None:
            node_pos_b = _node_key(hb.originNode)
            interp_x = _lerp(ha.originNode.position.x, hb.originNode.position.x, t)
            interp_y = _lerp(ha.originNode.position.y, hb.originNode.position.y, t)
        else:
            interp_x = ha.originNode.position.x
            interp_y = ha.originNode.position.y

        out_node = out_nodes.get((round(interp_x, 1), round(interp_y, 1)))
        if out_node is None:
            # Fallback: nearest node by distance
            best_dist = float('inf')
            for nk, n in out_nodes.items():
                d = (nk[0] - interp_x) ** 2 + (nk[1] - interp_y) ** 2
                if d < best_dist:
                    best_dist = d
                    out_node = n

        if out_node is None:
            continue

        new_hint = GSHint()
        new_hint.type       = ha.type
        new_hint.name       = ha.name
        new_hint.originNode = out_node
        new_hint.options    = ha.options
        new_hint.horizontal = ha.horizontal
        new_hint.scale      = (interp_sx, interp_sy)

        layer_out.hints.append(new_hint)


# ─────────────────────────────────────────────────────────────────────────────
# Main interpolation routine
# ─────────────────────────────────────────────────────────────────────────────

def _interpolate_one(font, name_a, name_b, name_out, factor):
    """Interpolate a single pair and write to name_out."""
    glyph_a = font.glyphs[name_a]
    glyph_b = font.glyphs[name_b]
    if glyph_a is None:
        raise ValueError("Glyph not found: '%s'" % name_a)
    if glyph_b is None:
        raise ValueError("Glyph not found: '%s'" % name_b)

    glyph_out = font.glyphs[name_out]
    if glyph_out is None:
        glyph_out = GSGlyph(name_out)
        font.glyphs.append(glyph_out)

    for master in font.masters:
        layer_a = glyph_a.layers[master.id] or glyph_a.layers[0]
        layer_b = glyph_b.layers[master.id] or glyph_b.layers[0]

        # Interpolate all shapes in their original order (paths + components)
        out_shapes = _interpolate_layer_shapes(layer_a, layer_b, factor)

        # Anchors
        out_anchors = _interpolate_anchors(
            list(layer_a.anchors), list(layer_b.anchors), factor
        )

        # Advance width
        width = _lerp(float(layer_a.width), float(layer_b.width), factor)

        # Get or create output layer
        layer_out = glyph_out.layers[master.id]
        if layer_out is None:
            layer_out = GSLayer()
            layer_out.associatedMasterId = master.id
            glyph_out.layers.append(layer_out)

        layer_out.clear()
        layer_out.width = width

        for shape in out_shapes:
            layer_out.shapes.append(shape)
        for anchor in out_anchors:
            layer_out.anchors.append(anchor)

        # Copy corner/cap hints AFTER shapes are written so nodes exist to attach to
        _interpolate_hints(layer_a, layer_b, layer_out, factor)

    return name_out


# ─────────────────────────────────────────────────────────────────────────────
# Pair detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_pairs(selected_names, src_suffix):
    """
    From the selected glyph names, find every (base, base+src_suffix) pair.

    Returns:
        pairs   — list of (base_name, src_name)
        skipped — list of names with no matching partner
    """
    name_set = set(selected_names)
    sfx = src_suffix if src_suffix.startswith(".") else "." + src_suffix
    pairs  = []
    used   = set()
    skipped = []

    for name in sorted(selected_names):
        if name in used:
            continue
        if name.endswith(sfx):
            base = name[: -len(sfx)]
            if base in name_set:
                pairs.append((base, name))
                used.add(base)
                used.add(name)
            else:
                skipped.append(name)
                used.add(name)

    for name in selected_names:
        if name not in used:
            skipped.append(name)

    return pairs, skipped


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

class GlyphInterpolatorUI:

    W = 380
    H = 310

    def __init__(self):
        font = Glyphs.font
        if font is None:
            Message("Please open a font first.", "Glyph Interpolator")
            return
        self.font = font

        w, h     = self.W, self.H
        pad      = 20
        row_h    = 22
        label_w  = 130
        field_x  = pad + label_w + 8
        field_w  = w - field_x - pad
        y        = 20

        self.w = vanilla.FloatingWindow(
            (w, h), "Glyph Interpolator",
            closable=True, minSize=(w, h), maxSize=(w, h),
        )

        # ── Source suffix ──────────────────────────────────────────────────
        self.w.label_src = vanilla.TextBox(
            (pad, y + 3, label_w, row_h),
            "Source suffix (=100):", sizeStyle="small",
        )
        self.w.field_src = vanilla.EditText(
            (field_x, y, field_w, row_h), text=".ss01", sizeStyle="small",
        )
        y += row_h + 10

        # ── Output suffix ──────────────────────────────────────────────────
        self.w.label_out = vanilla.TextBox(
            (pad, y + 3, label_w, row_h), "Output suffix:", sizeStyle="small",
        )
        self.w.field_out = vanilla.EditText(
            (field_x, y, field_w, row_h), text=".ss02", sizeStyle="small",
        )
        y += row_h + 18

        # ── Factor slider ──────────────────────────────────────────────────
        self.w.label_factor = vanilla.TextBox(
            (pad, y + 3, label_w, row_h), "Factor:", sizeStyle="small",
        )
        slider_w = field_w - 52
        self.w.slider = vanilla.Slider(
            (field_x, y, slider_w, row_h),
            minValue=0, maxValue=100, value=50,
            callback=self._sliderChanged, sizeStyle="small",
        )
        self.w.factor_display = vanilla.TextBox(
            (field_x + slider_w + 6, y + 3, 46, row_h), "50", sizeStyle="small",
        )
        y += row_h + 18

        # ── Pair preview ───────────────────────────────────────────────────
        self.w.label_preview = vanilla.TextBox(
            (pad, y + 3, label_w, row_h), "Selected pairs:", sizeStyle="small",
        )
        self.w.preview = vanilla.TextBox(
            (field_x, y, field_w, row_h), "—", sizeStyle="small",
        )
        y += row_h + 6

        self.w.btn_refresh = vanilla.Button(
            (field_x, y, field_w, 18), "Refresh from selection",
            callback=self._refresh, sizeStyle="mini",
        )
        y += 24 + 6

        # ── Divider ────────────────────────────────────────────────────────
        self.w.divider = vanilla.HorizontalLine((pad, y, -pad, 1))
        y += 10

        # ── Status ─────────────────────────────────────────────────────────
        self.w.status = vanilla.TextBox(
            (pad, y, -pad, 46),
            "Select glyphs in the Font view, then press Interpolate.",
            sizeStyle="small",
        )
        y += 52

        # ── Button ─────────────────────────────────────────────────────────
        btn_w = 130
        self.w.btn = vanilla.Button(
            (w - pad - btn_w, y, btn_w, 22), "Interpolate",
            callback=self._interpolate,
        )

        self.w.open()
        self._refresh(None)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _selected_names(self):
        sel = self.font.selectedLayers
        if sel:
            return [layer.parent.name for layer in sel]
        return [g.name for g in self.font.glyphs if g.selected]

    def _get_suffixes(self):
        src = self.w.field_src.get().strip()
        out = self.w.field_out.get().strip()
        if src and not src.startswith("."):
            src = "." + src
        if out and not out.startswith("."):
            out = "." + out
        return src, out

    # ── Callbacks ──────────────────────────────────────────────────────────

    def _sliderChanged(self, sender):
        self.w.factor_display.set(str(int(round(sender.get()))))

    def _refresh(self, sender):
        src_sfx, _ = self._get_suffixes()
        names = self._selected_names()
        if not names:
            self.w.preview.set("(nothing selected)")
            return
        pairs, _ = detect_pairs(names, src_sfx)
        if pairs:
            self.w.preview.set("%d pair(s): %s" % (
                len(pairs), ", ".join(b for b, _ in pairs),
            ))
        else:
            self.w.preview.set("No pairs found for suffix '%s'" % src_sfx)

    def _interpolate(self, sender):
        try:
            src_sfx, out_sfx = self._get_suffixes()
            factor = self.w.slider.get() / 100.0

            if not src_sfx:
                self.w.status.set("⚠ Source suffix cannot be empty.")
                return
            if not out_sfx:
                self.w.status.set("⚠ Output suffix cannot be empty.")
                return
            if src_sfx == out_sfx:
                self.w.status.set("⚠ Source and output suffix must differ.")
                return

            names = self._selected_names()
            if not names:
                self.w.status.set("⚠ No glyphs selected in the Font view.")
                return

            pairs, skipped = detect_pairs(names, src_sfx)
            if not pairs:
                self.w.status.set(
                    "⚠ No base+variant pairs found.\n"
                    "Make sure both the base glyph and its '%s' variant are selected."
                    % src_sfx
                )
                return

            created = []
            errors  = []

            for base_name, src_name in pairs:
                out_name = base_name + out_sfx
                try:
                    _interpolate_one(self.font, base_name, src_name, out_name, factor)
                    created.append(out_name)
                except ValueError as e:
                    errors.append("%s: %s" % (base_name, e))

            Glyphs.redraw()

            lines = []
            if created:
                lines.append("✓ %d glyph(s) at %.0f%%: %s" % (
                    len(created), factor * 100, ", ".join(created)))
            if errors:
                lines.append("⚠ %d error(s):" % len(errors))
                for e in errors:
                    lines.append("  " + e)
            if skipped:
                lines.append("Skipped: " + ", ".join(skipped))

            self.w.status.set("\n".join(lines))

        except Exception:
            print(traceback.format_exc())
            self.w.status.set("⚠ Unexpected error — see Macro Window (⌥⌘M).")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

GlyphInterpolatorUI()
