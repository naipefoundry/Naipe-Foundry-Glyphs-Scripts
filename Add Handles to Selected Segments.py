# MenuTitle: Add Handles to Selected Segments
# -*- coding: utf-8 -*-
__doc__ = """Adds handles to all selected straight segments."""

from GlyphsApp import LINE, CURVE, OFFCURVE, GSNode

def addHandlesToNode(node):
	"""node is the on-curve node that ends a straight (LINE) segment."""
	path = node.parent
	nodes = path.nodes
	index = node.index

	# Open paths: index 0 has no incoming segment, skip it.
	if index == 0 and not path.closed:
		return False

	prevNode = nodes[(index - 1) % len(nodes)]

	x0, y0 = prevNode.position.x, prevNode.position.y
	x1, y1 = node.position.x, node.position.y

	h1x = x0 + (x1 - x0) / 3.0
	h1y = y0 + (y1 - y0) / 3.0
	h2x = x0 + (x1 - x0) * 2.0 / 3.0
	h2y = y0 + (y1 - y0) * 2.0 / 3.0

	h1 = GSNode()
	h1.position = (h1x, h1y)
	h1.type = OFFCURVE

	h2 = GSNode()
	h2.position = (h2x, h2y)
	h2.type = OFFCURVE

	# Insert the two off-curves right before the end node,
	# then turn the end node's segment type into a curve.
	nodes.insert(index, h2)
	nodes.insert(index, h1)
	node.type = CURVE

	return True


def run():
	font = Glyphs.font
	if font is None:
		Glyphs.showMacroWindow()
		print("No font open.")
		return

	Glyphs.font.disableUpdateInterface()
	try:
		for layer in font.selectedLayers:
			# Collect selected nodes that end a straight segment.
			candidates = [
				n for n in layer.selection
				if isinstance(n, GSNode) and n.type == LINE
			]

			# Process each path's nodes from highest index to lowest so
			# earlier insertions don't invalidate later indices.
			candidates.sort(key=lambda n: n.index, reverse=True)

			for node in candidates:
				addHandlesToNode(node)
	finally:
		Glyphs.font.enableUpdateInterface()


run()
