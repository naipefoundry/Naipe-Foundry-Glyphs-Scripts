# MenuTitle: Apply Italic Shear (Live Preview)
# -*- coding: utf-8 -*-
__doc__ = """
Two-parameter italic shear tool with 2D control pad.

  Drag left / right   →   horizontal shear  (−20° … +20°)
  Drag down           →   vertical shear    (0° … −10°)
  Double-click        →   reset both to zero

Selection behaviour
───────────────────
  Nodes selected   →  only those nodes transform (pivot = selection centre)
  Nothing selected →  all nodes transform (pivot = glyph centre)

Install
───────
  ~/Library/Application Support/Glyphs 3/Scripts/
  Script → Refresh Scripts  (⌥⌘⇧Y)
"""

import sys
import objc
import math
import traceback
from AppKit import (
    NSView, NSColor, NSBezierPath,
    NSFont, NSFontAttributeName, NSForegroundColorAttributeName,
    NSApp,
)
from Foundation import NSObject, NSString
from GlyphsApp import Glyphs, OFFCURVE, Message

try:
    from vanilla import FloatingWindow, TextBox, EditText, Button, HorizontalLine, Group
except ImportError:
    Message("This script requires vanilla.\nInstall via Glyphs > Plugin Manager.", "Missing module")
    raise


# ── 2D pad ────────────────────────────────────────────────────────────────────
#
# The Python class is stored in sys.modules under a private key.
# sys.modules is a plain Python dict that persists for the entire process
# lifetime — it survives script re-runs and is not subject to ObjC memory
# management, making it the most reliable cache available.

_CACHE_KEY = "_italic_transform_composer_pad_class_v2"

def _make_pad_class():
    # Return cached Python class if it exists
    cached = sys.modules.get(_CACHE_KEY)
    if cached is not None:
        return cached

    class TwoDPadView(NSView):
        """
        Asymmetric 2D shear control pad.

        H axis  →  horizontal shear, ±h_range°, zero at horizontal centre.
        V axis  →  vertical shear,   v_max (0°) at top, v_min (−10°) at bottom.

        Axis ranges are written to instance variables directly after alloc/init.
        """

        def initWithFrame_(self, frame):
            self = objc.super(TwoDPadView, self).initWithFrame_(frame)
            if self is not None:
                self._hval     = 0.0
                self._vval     = 0.0
                self._callback = None
                self._h_range  = 20.0
                self._v_min    = -10.0
                self._v_max    =  0.0
                self._live     = False
                self._focused  = False
            return self

        # ── Drawing ───────────────────────────────────────────────────────

        def drawRect_(self, dirtyRect):
            b  = self.bounds()
            w  = b.size.width
            h  = b.size.height
            HR = self._h_range
            VM = self._v_min
            VX = self._v_max

            NSColor.controlBackgroundColor().setFill()
            NSBezierPath.fillRect_(b)

            # Grid
            NSColor.separatorColor().setStroke()
            grid = NSBezierPath.bezierPath()
            grid.setLineWidth_(0.5)
            for deg in (-HR / 2.0, HR / 2.0):
                xg = (deg + HR) / (HR * 2.0) * w
                grid.moveToPoint_((xg, 0))
                grid.lineToPoint_((xg, h))
            v_mid = (VX + VM) / 2.0
            yg = (1.0 - (v_mid - VX) / (VM - VX)) * h
            grid.moveToPoint_((0, yg))
            grid.lineToPoint_((w, yg))
            grid.stroke()

            # H zero line
            NSColor.tertiaryLabelColor().setStroke()
            hline = NSBezierPath.bezierPath()
            hline.setLineWidth_(1.0)
            hline.moveToPoint_((w / 2.0, 0))
            hline.lineToPoint_((w / 2.0, h))
            hline.stroke()

            # V zero line at bottom (V=0 = no shear = resting position)
            vline = NSBezierPath.bezierPath()
            vline.setLineWidth_(1.0)
            vline.moveToPoint_((0,   0.5))
            vline.lineToPoint_((w,   0.5))
            vline.stroke()

            # Axis labels
            attrs = {
                NSFontAttributeName:            NSFont.systemFontOfSize_(9),
                NSForegroundColorAttributeName: NSColor.tertiaryLabelColor(),
            }
            NSString.stringWithString_("H").drawAtPoint_withAttributes_(
                (w - 14, h / 2.0 + 3), attrs)
            NSString.stringWithString_("V").drawAtPoint_withAttributes_(
                (w / 2.0 + 3, 2), attrs)

            # Dot position
            px   = (self._hval + HR) / (HR * 2.0) * w
            norm = (self._vval - VX) / (VM - VX)
            py   = norm * h              # 0 at bottom (V=0), h at top (V=-10)

            # Spoke from bottom-centre (zero point) to dot
            NSColor.secondaryLabelColor().setStroke()
            spoke = NSBezierPath.bezierPath()
            spoke.setLineWidth_(1.0)
            spoke.moveToPoint_((w / 2.0, 0))
            spoke.lineToPoint_((px, py))
            spoke.stroke()

            # Dot
            r = 6.0
            NSColor.controlAccentColor().setFill()
            NSBezierPath.bezierPathWithOvalInRect_(
                ((px - r, py - r), (r * 2.0, r * 2.0))
            ).fill()

            # Border — accent-colored and thicker when live
            if self._live:
                NSColor.controlAccentColor().setStroke()
                border = NSBezierPath.bezierPathWithRect_(b)
                border.setLineWidth_(2.0)
                border.stroke()
                # "LIVE" badge in top-left corner
                badge_attrs = {
                    NSFontAttributeName: NSFont.boldSystemFontOfSize_(9),
                    NSForegroundColorAttributeName: NSColor.controlAccentColor(),
                }
                NSString.stringWithString_("LIVE").drawAtPoint_withAttributes_(
                    (5, h - 14), badge_attrs)
            else:
                NSColor.separatorColor().setStroke()
                NSBezierPath.bezierPathWithRect_(b).stroke()

            # Focus ring — dashed inner border when pad has keyboard focus
            if self._focused:
                NSColor.keyboardFocusIndicatorColor().setStroke()
                ring = NSBezierPath.bezierPathWithRect_(
                    ((2, 2), (w - 4, h - 4))
                )
                ring.setLineWidth_(1.5)
                ring.setLineDash_count_phase_([4.0, 3.0], 2, 0.0)
                ring.stroke()

        # ── Mouse handling ────────────────────────────────────────────────

        @objc.python_method
        def _update_from_point(self, pt):
            b  = self.bounds()
            w  = b.size.width
            h  = b.size.height
            HR = self._h_range
            VM = self._v_min
            VX = self._v_max

            px = max(0.0, min(w, pt.x))
            py = max(0.0, min(h, pt.y))

            self._hval = (px / w) * (HR * 2.0) - HR
            norm       = py / h                    # 0 at bottom, 1 at top
            self._vval = VX + norm * (VM - VX)     # 0 at bottom, -10 at top

            self.setNeedsDisplay_(True)
            if self._callback:
                self._callback(self)

        def mouseDown_(self, event):
            # Claim keyboard focus on click so arrow keys work immediately
            self.window().makeFirstResponder_(self)
            if event.clickCount() >= 2:
                self._hval = 0.0
                self._vval = 0.0
                self.setNeedsDisplay_(True)
                if self._callback:
                    self._callback(self)
            else:
                pt = self.convertPoint_fromView_(event.locationInWindow(), None)
                self._update_from_point(pt)

        def mouseDragged_(self, event):
            pt = self.convertPoint_fromView_(event.locationInWindow(), None)
            self._update_from_point(pt)

        def acceptsFirstMouse_(self, event):
            return True

        def acceptsFirstResponder(self):
            return True

        def becomeFirstResponder(self):
            self._focused = True
            self.setNeedsDisplay_(True)
            return True

        def resignFirstResponder(self):
            self._focused = False
            self.setNeedsDisplay_(True)
            return True

        def keyDown_(self, event):
            # Arrow key codes: left=123, right=124, down=125, up=126
            code = event.keyCode()
            HR   = self._h_range
            VM   = self._v_min
            VX   = self._v_max

            if code == 123:   # left  → H more negative
                self._hval = max(-HR, self._hval - 1.0)
            elif code == 124: # right → H more positive
                self._hval = min(HR,  self._hval + 1.0)
            elif code == 126: # up    → V more shear (more negative internally)
                self._vval = max(VM,  self._vval - 1.0)
            elif code == 125: # down  → V less shear (toward zero)
                self._vval = min(VX,  self._vval + 1.0)
            else:
                # Pass unhandled keys up the responder chain
                self.interpretKeyEvents_([event])
                return

            self.setNeedsDisplay_(True)
            if self._callback:
                self._callback(self)

        # ── Python accessors ──────────────────────────────────────────────

        @objc.python_method
        def hValue(self):
            return self._hval

        @objc.python_method
        def vValue(self):
            return self._vval

        @objc.python_method
        def setCallback(self, cb):
            self._callback = cb

        @objc.python_method
        def setLive(self, live):
            self._live = live
            self.setNeedsDisplay_(True)

        @objc.python_method
        def setValues(self, h, v):
            self._hval = max(-self._h_range, min(self._h_range, h))
            self._vval = max(self._v_min,    min(self._v_max,    v))
            self.setNeedsDisplay_(True)

    sys.modules[_CACHE_KEY] = TwoDPadView
    return TwoDPadView


TwoDPadView = _make_pad_class()


# ── Field delegate (arrow-key stepping) ───────────────────────────────────────
#
# NSTextField doesn't expose arrow-key events through vanilla's callback.
# Setting a delegate and implementing control:textView:doCommandBySelector_
# intercepts those commands before the field handles them, letting us
# increment/decrement the value without subclassing NSTextField.

_DELEGATE_CACHE_KEY = "_italic_transform_composer_field_delegate"

def _make_delegate_class():
    cached = sys.modules.get(_DELEGATE_CACHE_KEY)
    if cached is not None:
        return cached

    class FieldStepDelegate(NSObject):
        """
        NSTextField delegate that intercepts up/down arrow keys and
        calls a Python step callback with +1 or -1.

        The callback is stored as a plain instance attribute so it
        survives the sys.modules cache across script re-runs.
        """

        def init(self):
            self = objc.super(FieldStepDelegate, self).init()
            if self is not None:
                self._step_cb = None
            return self

        def control_textView_doCommandBySelector_(self, control, textView, sel):
            if sel == "moveUp:":
                if self._step_cb:
                    self._step_cb(1.0)
                return True
            if sel == "moveDown:":
                if self._step_cb:
                    self._step_cb(-1.0)
                return True
            return False

    sys.modules[_DELEGATE_CACHE_KEY] = FieldStepDelegate
    return FieldStepDelegate


FieldStepDelegate = _make_delegate_class()


# ── Geometry helpers ──────────────────────────────────────────────────────────

def centre_of_nodes(nodes):
    oncurve = [n for n in nodes if n.type != OFFCURVE]
    sample  = oncurve if oncurve else nodes
    if not sample:
        return 0.0, 0.0
    return (
        sum(n.position.x for n in sample) / len(sample),
        sum(n.position.y for n in sample) / len(sample),
    )

def all_nodes(layer):
    return [n for path in layer.paths for n in path.nodes]

def selected_nodes(layer):
    return [n for n in all_nodes(layer) if n.selected]


# ── Transform ─────────────────────────────────────────────────────────────────

# ── Transform ─────────────────────────────────────────────────────────────────

# Tolerance (in font units) for deciding whether a handle is "horizontal".
# A handle whose Y differs from its on-curve anchor by less than this amount
# is treated as horizontal and its anchor is considered a vertical extreme.
# 1 unit covers rounding and tiny optical nudges on well-drawn extremes.
_HORIZ_THRESHOLD = 1.0

# Blend weight assigned to on-curve nodes at vertical extremes.
# Controls how far the x position of an exempt extreme deviates from the
# pure horizontal shear (w=0, uses tan_h) toward the stress-axis correction
# (w=1, uses tan_v).
#
# The derivation for w=1 assumed the extreme sits at the parametric endpoint
# of its cubic segment (t=1).  In practice it sits closer to the arc midpoint
# (t≈0.5), so 0.5 gives a more proportionate correction.  Handles on either
# side inherit proportional weights automatically through the interpolation in
# _node_weights, so no other values need changing.
#
# Range: 0.0 (no x correction, pure horizontal shear)
#        0.5 (half correction — default, recommended for most italics)
#        1.0 (full correction as previously)
_EXTREME_WEIGHT = 0.4

def _exempt_indices(path):
    """
    Return a set of node indices that should be exempted from vertical shear.

    A node is exempt when it sits at a vertical extreme — defined as an
    on-curve point whose neighbouring off-curve handles are both horizontal
    (Y within _HORIZ_THRESHOLD of the on-curve Y).  The handles themselves
    are also exempt so the tangent direction is preserved.

    Horizontal straight-line segments (two on-curve nodes at the same Y
    connected directly without handles) are also exempt.

    Why exempt the handles too?
    If only the on-curve node is held in place but its handles are sheared,
    the tangent at the extreme tilts — the curve no longer has a horizontal
    tangent there, and the extreme drifts away from the node visually.
    Keeping the handles at the same Y as the on-curve node preserves the
    horizontal tangent exactly.
    """
    nodes = list(path.nodes)
    n     = len(nodes)
    exempt = set()

    for i, node in enumerate(nodes):
        if node.type == OFFCURVE:
            continue

        ny   = node.position.y
        prev = nodes[(i - 1) % n]
        nxt  = nodes[(i + 1) % n]

        prev_horiz = (
            prev.type == OFFCURVE and
            abs(prev.position.y - ny) <= _HORIZ_THRESHOLD
        )
        next_horiz = (
            nxt.type == OFFCURVE and
            abs(nxt.position.y - ny) <= _HORIZ_THRESHOLD
        )

        # Straight-line neighbours: no handle between two on-curve nodes
        prev_line = prev.type != OFFCURVE and abs(prev.position.y - ny) <= _HORIZ_THRESHOLD
        next_line = nxt.type  != OFFCURVE and abs(nxt.position.y  - ny) <= _HORIZ_THRESHOLD

        if (prev_horiz or prev_line) and (next_horiz or next_line):
            exempt.add(i)
            if prev_horiz:
                exempt.add((i - 1) % n)
            if next_horiz:
                exempt.add((i + 1) % n)

    return exempt


def _node_weights(path, exempt_indices):
    """
    Assign a blend weight w ∈ [0, 1] to every node in the path.

    w = 0  →  full shear  (non-exempt on-curve nodes)
    w = 1  →  exempt      (vertical extreme on-curve nodes)

    Off-curve handles receive a weight that is linearly interpolated at
    their parametric position along the cubic segment:
      exit handle  (t ≈ 1/3 from P0):  w = 2/3·w_P0 + 1/3·w_P3
      entry handle (t ≈ 2/3 from P0):  w = 1/3·w_P0 + 2/3·w_P3

    This means a handle bridging a non-exempt node (w=0) and an exempt
    extreme (w=1) is blended smoothly rather than snapping between the
    two transforms.  The blended transform applied to all four control
    points of a cubic produces a valid smooth curve — no bumps.
    """
    nodes = list(path.nodes)
    n     = len(nodes)

    # On-curve weights
    oc_w = {
        i: (_EXTREME_WEIGHT if i in exempt_indices else 0.0)
        for i, nd in enumerate(nodes)
        if nd.type != OFFCURVE
    }

    def prev_on(i):
        for d in range(1, n):
            j = (i - d) % n
            if nodes[j].type != OFFCURVE:
                return j

    def next_on(i):
        for d in range(1, n):
            j = (i + d) % n
            if nodes[j].type != OFFCURVE:
                return j

    weights = {}
    for i, node in enumerate(nodes):
        if node.type != OFFCURVE:
            weights[i] = oc_w[i]
        else:
            p  = prev_on(i)
            q  = next_on(i)
            wp = oc_w.get(p, 0.0)
            wq = oc_w.get(q, 0.0)
            # Exit handle: previous node is on-curve → t = 1/3 from P0
            if nodes[(i - 1) % n].type != OFFCURVE:
                weights[i] = (2.0 / 3.0) * wp + (1.0 / 3.0) * wq
            else:
                # Entry handle → t = 2/3 from P0
                weights[i] = (1.0 / 3.0) * wp + (2.0 / 3.0) * wq

    return weights


def _enforce_colinearity(path, any_selected, exempt):
    """
    Post-transform pass: re-enforce colinearity at smooth on-curve nodes.

    Two cases:
      - Exempt (vertical extreme): enforce horizontality — both handles are
        snapped to the same Y as the on-curve point, X distance preserved.
      - Non-exempt smooth node: average the two handle directions and
        re-project both handles onto that axis at their original lengths.
    """
    nodes = list(path.nodes)
    n     = len(nodes)

    for i, node in enumerate(nodes):
        if node.type == OFFCURVE:
            continue
        if not node.smooth:
            continue
        if any_selected and not node.selected:
            continue

        prev = nodes[(i - 1) % n]
        nxt  = nodes[(i + 1) % n]

        if prev.type != OFFCURVE or nxt.type != OFFCURVE:
            continue

        px, py = node.position.x, node.position.y

        if i in exempt:
            # Vertical extreme: both handles must stay at the same Y.
            # Preserve X distance so handle lengths are maintained.
            prev.position = (prev.position.x, py)
            nxt.position  = (nxt.position.x,  py)
            continue

        # Non-exempt smooth node: average handle directions.
        ax, ay = px - prev.position.x, py - prev.position.y
        bx, by = nxt.position.x - px,  nxt.position.y - py

        len_a = math.hypot(ax, ay)
        len_b = math.hypot(bx, by)

        if len_a < 1e-6 or len_b < 1e-6:
            continue

        uax, uay = ax / len_a, ay / len_a
        ubx, uby = bx / len_b, by / len_b

        mx, my = uax + ubx, uay + uby
        mag = math.hypot(mx, my)
        if mag < 1e-6:
            continue

        mx, my = mx / mag, my / mag

        prev.position = (px - len_a * mx, py - len_a * my)
        nxt.position  = (px + len_b * mx, py + len_b * my)


def transform_layer(layer, h_deg, v_deg):
    """
    Apply the blended shear transform to all (or selected) nodes,
    then re-enforce colinearity at smooth nodes.
    """
    if h_deg == v_deg == 0:
        return

    tan_h = math.tan(math.radians(h_deg))
    tan_v = math.tan(math.radians(v_deg))

    sel          = selected_nodes(layer)
    any_selected = bool(sel)
    cx, cy       = centre_of_nodes(sel if any_selected else all_nodes(layer))

    for path in layer.paths:
        nodes   = list(path.nodes)
        exempt  = _exempt_indices(path)
        weights = _node_weights(path, exempt)

        for i, node in enumerate(nodes):
            if any_selected and not node.selected:
                continue
            x, y = node.position.x, node.position.y
            w    = weights[i]
            tx   = tan_h * (1.0 - w) + tan_v * w
            x1   = x  + (y  - cy) * tx
            y1   = y  + (x1 - cx) * tan_v * (1.0 - w)
            node.position = (x1, y1)

        # Re-enforce colinearity at smooth nodes after the blended transform
        _enforce_colinearity(path, any_selected, exempt)


# ── Main window ───────────────────────────────────────────────────────────────

class ItalicTransformComposer:

    W        = 280
    P        = 14
    PAD_SIZE = 252

    def __init__(self):
        self.font = Glyphs.font
        if not self.font:
            Message("No font is open.", "Italic Transform Composer")
            return

        self._snapshots = {}
        self._previewed = False

        W, P, S = self.W, self.P, self.PAD_SIZE
        y = P

        self.w = FloatingWindow((W, 350), "Italic Transform Composer")

        self.w.pad_group = Group((P, y, S, S))
        y += S + 10

        # ── H / V input fields ────────────────────────────────────────────
        # Each field has a short static label and an editable number box.
        # Pressing Tab or Return commits the typed value to the pad.
        lw = 20   # label width
        fw = (W - 2 * P - 8 - lw * 2) // 2   # field width

        self.w.h_label = TextBox(
            (P, y + 3, lw, 16), "H:", sizeStyle="small")
        self.w.h_field = EditText(
            (P + lw, y, fw, 22), "0.0",
            sizeStyle="small", callback=self._on_field)

        ox = P + lw + fw + 8   # x offset for V pair
        self.w.v_label = TextBox(
            (ox, y + 3, lw, 16), "V:", sizeStyle="small")
        self.w.v_field = EditText(
            (ox + lw, y, fw, 22), "0.0",
            sizeStyle="small", callback=self._on_field)

        y += 22 + 10

        self.w.sep = HorizontalLine((P, y, -P, 1))
        y += 12
        BW = 76
        self.w.preview_btn = Button(
            (P,          y, BW, 22), "Preview", callback=self._preview)
        self.w.reset_btn   = Button(
            (P + BW + 8, y, BW, 22), "Reset",   callback=self._reset)
        self.w.apply_btn   = Button(
            (W - P - BW, y, BW, 22), "Apply",   callback=self._apply)

        self.w.open()

        # ── Attach arrow-key delegates to input fields ─────────────────────
        self._h_delegate = FieldStepDelegate.alloc().init()
        self._h_delegate._step_cb = lambda d: self._step_field('h', d)
        self.w.h_field._nsObject.setDelegate_(self._h_delegate)

        self._v_delegate = FieldStepDelegate.alloc().init()
        self._v_delegate._step_cb = lambda d: self._step_field('v', d)
        self.w.v_field._nsObject.setDelegate_(self._v_delegate)

        # ── Embed pad NSView ───────────────────────────────────────────────
        pad_ns    = self.w.pad_group._nsObject
        self._pad = TwoDPadView.alloc().initWithFrame_(((0, 0), (S, S)))
        self._pad._h_range  = 20.0
        self._pad._v_min    = -10.0
        self._pad._v_max    =  0.0
        self._pad._hval     = 0.0
        self._pad._vval     = 0.0
        self._pad._live     = False
        self._pad._focused  = False
        self._pad._callback = self._on_pad
        pad_ns.addSubview_(self._pad)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _set_previewed(self, state):
        self._previewed    = state
        self._pad._live    = state
        self._pad.setNeedsDisplay_(True)
        self.w.preview_btn.setTitle(
            "■ Stop preview" if state else "Preview"
        )

    def _undo_manager(self):
        """
        Try every known path to the font document's NSUndoManager.

        Glyphs 3 exposes it via the window controller's document, not
        directly on the font object.  We try several paths so that if
        one changes between Glyphs versions, others still work.
        """
        candidates = [
            lambda: self.font.parent.undoManager(),
            lambda: NSApp.mainWindow().windowController().document().undoManager(),
            lambda: NSApp.keyWindow().windowController().document().undoManager(),
            lambda: self.font.document.undoManager(),
        ]
        for fn in candidates:
            try:
                um = fn()
                if um is not None:
                    return um
            except Exception:
                pass
        return None

    def _without_undo(self, fn):
        """
        Call fn() with undo registration disabled, guaranteed to re-enable
        even if fn() raises.  This prevents the undo manager getting stuck
        in a disabled state if something goes wrong mid-restore.
        """
        um = self._undo_manager()
        if um is not None:
            um.disableUndoRegistration()
        try:
            fn()
        finally:
            if um is not None:
                um.enableUndoRegistration()

    def _update_readouts(self):
        self.w.h_field.set("%d" % round(self._pad._hval))
        self.w.v_field.set("%d" % round(abs(self._pad._vval)))

    def _on_field(self, sender):
        try:
            h = float(self.w.h_field.get())
        except ValueError:
            h = self._pad._hval
        try:
            v_abs = float(self.w.v_field.get())
        except ValueError:
            v_abs = abs(self._pad._vval)

        h     = round(max(-self._pad._h_range, min(self._pad._h_range, h)))
        v_abs = round(max(0.0, min(abs(self._pad._v_min), v_abs)))

        self._pad._hval = float(h)
        self._pad._vval = float(-v_abs)
        self._pad.setNeedsDisplay_(True)

        if self._previewed:
            layers = self._layers()
            self._without_undo(lambda: (self._restore(layers), self._apply_transform(layers)))
            Glyphs.redraw()

    def _step_field(self, axis, delta):
        if axis == 'h':
            new_h = round(self._pad._hval + delta)
            new_h = max(-self._pad._h_range, min(self._pad._h_range, new_h))
            self._pad._hval = float(new_h)
            self.w.h_field.set("%d" % new_h)
        else:
            v_abs = round(abs(self._pad._vval) + delta)
            v_abs = max(0.0, min(abs(self._pad._v_min), v_abs))
            self._pad._vval = float(-v_abs)
            self.w.v_field.set("%d" % v_abs)

        self._pad.setNeedsDisplay_(True)

        if self._previewed:
            layers = self._layers()
            self._without_undo(lambda: (self._restore(layers), self._apply_transform(layers)))
            Glyphs.redraw()

    def _layers(self):
        return list(self.font.selectedLayers)

    def _snapshot(self, layers):
        self._snapshots = {}
        for layer in layers:
            key = (layer.parent.name, layer.layerId)
            self._snapshots[key] = [
                [(n.position.x, n.position.y) for n in path.nodes]
                for path in layer.paths
            ]

    def _restore(self, layers):
        for layer in layers:
            key = (layer.parent.name, layer.layerId)
            if key not in self._snapshots:
                continue
            saved = self._snapshots[key]
            for pi, path in enumerate(layer.paths):
                if pi >= len(saved):
                    continue
                for ni, node in enumerate(path.nodes):
                    if ni < len(saved[pi]):
                        node.position = (saved[pi][ni][0], saved[pi][ni][1])

    def _apply_transform(self, layers):
        for layer in layers:
            transform_layer(layer, self._pad._hval, self._pad._vval)

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _on_pad(self, sender):
        try:
            self._update_readouts()
            if self._previewed:
                layers = self._layers()
                self._without_undo(lambda: (self._restore(layers), self._apply_transform(layers)))
                Glyphs.redraw()
        except Exception:
            print(traceback.format_exc())
            Message("Unexpected error — see Macro Window (⌥⌘M).", "Italic Shear")

    def _preview(self, sender):
        try:
            layers = self._layers()
            if self._previewed:
                self._without_undo(lambda: self._restore(layers))
                self._set_previewed(False)
            else:
                self._snapshot(layers)
                self._set_previewed(True)
                self._without_undo(lambda: self._apply_transform(layers))
            Glyphs.redraw()
        except Exception:
            print(traceback.format_exc())
            Message("Unexpected error — see Macro Window (⌥⌘M).", "Italic Shear")

    def _reset(self, sender):
        if not self._snapshots:
            return
        self._without_undo(lambda: self._restore(self._layers()))
        self._set_previewed(False)
        self._pad._hval = 0.0
        self._pad._vval = 0.0
        self._pad.setNeedsDisplay_(True)
        self._update_readouts()
        Glyphs.redraw()

    def _apply(self, sender):
        try:
            layers = self._layers()
            if self._previewed:
                # Silently restore to original so the undo manager sees only
                # the clean original → final delta when we re-apply below.
                self._without_undo(lambda: self._restore(layers))
            # Apply with undo enabled — Glyphs records this as one action.
            self._apply_transform(layers)
            self._snapshots = {}
            self._set_previewed(False)
            self._pad._hval = 0.0
            self._pad._vval = 0.0
            self._pad.setNeedsDisplay_(True)
            self._update_readouts()
            Glyphs.redraw()
        except Exception:
            print(traceback.format_exc())
            Message("Unexpected error — see Macro Window (⌥⌘M).", "Italic Shear")


# ── Entry point ───────────────────────────────────────────────────────────────

ItalicTransformComposer()
