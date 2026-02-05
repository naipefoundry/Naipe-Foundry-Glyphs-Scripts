#MenuTitle: Italic Comparison String
# -*- coding: utf-8 -*-
"""
Opens a small window with two buttons in Glyphs App
Button 1: Draws red H glyph in viewport
Button 2: Disables the visualization
"""

from vanilla import Window, Button, FloatingWindow, CheckBox
from AppKit import NSColor, NSBezierPath, NSAffineTransform

class TwoButtonWindow:
    def __init__(self):
        # Window dimensions
        window_width = 300
        window_height = 160
        margin = 20
        button_height = 30
        button_spacing = 10
        
        # Initialize reporter delegate
        self.reporterDelegate = None
        
        # Create the window
        self.w = FloatingWindow(
            (window_width, window_height),
            "Italic Comparison String",
            minSize=(250, 140),
            maxSize=(500, 240)
        )
        
        # Set close callback
        self.w.bind("close", self.windowWillClose)
        
        # Calculate button width (both buttons share available width)
        button_width = (window_width - (2 * margin) - button_spacing) / 2
        
        # Create first button
        self.w.button1 = Button(
            (margin, margin, button_width, button_height),
            "Show Comparison String",
            callback=self.button1Callback
        )
        
        # Create second button
        self.w.button2 = Button(
            (margin + button_width + button_spacing, margin, button_width, button_height),
            "Hide Comparison String",
            callback=self.button2Callback
        )
        
        # Create checkbox for black color option
        self.w.blackColorCheckbox = CheckBox(
            (margin, margin + button_height + 15, window_width - 2 * margin, 20),
            "Show all glyphs in black",
            callback=self.checkboxCallback,
            value=False
        )
        
        # Open the window
        self.w.open()
    
    def button1Callback(self, sender):
        """Enable red H glyph visualization"""
        print("Enabling italic comparison string")
        
        # Remove existing delegate if any
        if self.reporterDelegate:
            Glyphs.removeCallback(self.reporterDelegate.drawBackground, DRAWBACKGROUND)
        
        # Create and register new delegate
        self.reporterDelegate = RedHReporter()
        Glyphs.addCallback(self.reporterDelegate.drawBackground, DRAWBACKGROUND)
        
        # Refresh the view
        Glyphs.redraw()
    
    def button2Callback(self, sender):
        """Disable red H glyph visualization"""
        print("Disabling italic comparison string")
        
        # Remove the delegate
        if self.reporterDelegate:
            Glyphs.removeCallback(self.reporterDelegate.drawBackground, DRAWBACKGROUND)
            self.reporterDelegate = None
        
        # Refresh the view
        Glyphs.redraw()
    
    def checkboxCallback(self, sender):
        """Handle checkbox state change"""
        if self.reporterDelegate:
            # Update the delegate's color setting
            self.reporterDelegate.use_black_color = sender.get()
            # Refresh the view
            Glyphs.redraw()
    
    def windowWillClose(self, sender):
        """Clean up when window is closed"""
        print("Window closing, disabling visualization")
        
        # Remove the delegate
        if self.reporterDelegate:
            Glyphs.removeCallback(self.reporterDelegate.drawBackground, DRAWBACKGROUND)
            self.reporterDelegate = None
        
        # Refresh the view
        Glyphs.redraw()


class RedHReporter:
    """Reporter plugin to draw red H glyph in viewport"""
    
    def __init__(self):
        self.use_black_color = False
    
    def drawBackground(self, layer, info):
        """Draw the red H glyph next to the current glyph"""
        try:
            # Get the current font
            font = layer.parent.parent
            
            # Get the H glyph
            h_glyph = font.glyphs["H"]
            if not h_glyph:
                print("H glyph not found in font")
                return
            
            # Get the current master
            master = layer.master
            h_layer = h_glyph.layers[master.id]
            
            if not h_layer:
                print("H layer not found for current master")
                return
            
            # Get H width for positioning
            h_width = h_layer.width
            
            # Get the bezierPath for H (we'll reuse this)
            bezierPath = h_layer.completeBezierPath
            
            # Get the current glyph to check for second layer
            current_glyph = layer.parent
            second_layer = None
            second_layer_width = 0
            
            if current_glyph:
                # Get all layers for the current master
                master_layers = [l for l in current_glyph.layers if l.layerId == master.id or l.associatedMasterId == master.id]
                
                # Check if there's a second layer for this master
                if len(master_layers) > 1:
                    second_layer = master_layers[1]
                    if second_layer and second_layer.paths:
                        second_layer_width = second_layer.width
            
            # Draw second layer to the left of the leftmost H (if it exists)
            if second_layer and second_layer.paths:
                second_layer_offset = -h_width - second_layer_width
                
                # Set color for the second layer
                if self.use_black_color:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
                else:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 1.0, 0.0, 0.5).set()
                
                # Draw the second layer
                second_bezierPath = second_layer.completeBezierPath
                transform_second = NSAffineTransform.transform()
                transform_second.translateXBy_yBy_(second_layer_offset, 0)
                
                transformedPathSecond = second_bezierPath.copy()
                transformedPathSecond.transformUsingAffineTransform_(transform_second)
                transformedPathSecond.fill()
                
                # Draw another H to the left of the second layer
                leftmost_h_offset = second_layer_offset - h_width
                
                # Set color for the leftmost H
                if self.use_black_color:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
                else:
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.5).set()
                
                transform_leftmost = NSAffineTransform.transform()
                transform_leftmost.translateXBy_yBy_(leftmost_h_offset, 0)
                
                transformedPathLeftmost = bezierPath.copy()
                transformedPathLeftmost.transformUsingAffineTransform_(transform_leftmost)
                transformedPathLeftmost.fill()
            
            # Draw H to the left of the current glyph
            left_h_offset = -h_width
            
            # Set color for the left H
            if self.use_black_color:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.5).set()
            
            # Draw the left H glyph
            transform_left = NSAffineTransform.transform()
            transform_left.translateXBy_yBy_(left_h_offset, 0)
            
            transformedPathLeft = bezierPath.copy()
            transformedPathLeft.transformUsingAffineTransform_(transform_left)
            transformedPathLeft.fill()
            
            # Get current glyph width to position H beside it
            current_width = layer.width
            
            # Draw a copy of the current glyph right after the original
            current_glyph_copy_offset = current_width
            
            # Set color for the current glyph copy
            if self.use_black_color:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0.5, 0.5, 0.5).set()
            
            # Draw the current glyph copy
            current_bezierPath = layer.completeBezierPath
            transform_current = NSAffineTransform.transform()
            transform_current.translateXBy_yBy_(current_glyph_copy_offset, 0)
            
            transformedPathCurrent = current_bezierPath.copy()
            transformedPathCurrent.transformUsingAffineTransform_(transform_current)
            transformedPathCurrent.fill()
            
            # Position H right after the current glyph copy
            offset_x = current_width + current_width
            
            # Set color for the H
            if self.use_black_color:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.5).set()
            
            # Draw the H glyph
            # Create transform to position the H
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(offset_x, 0)
            
            # Apply transform and draw
            transformedPath = bezierPath.copy()
            transformedPath.transformUsingAffineTransform_(transform)
            transformedPath.fill()
            
            # Now draw the third layer of the current glyph to the right of H
            current_glyph = layer.parent
            if current_glyph:
                # Get all layers for the current master
                master_layers = [l for l in current_glyph.layers if l.layerId == master.id or l.associatedMasterId == master.id]
                
                # Check if there's a third layer for this master
                if len(master_layers) > 2:
                    third_layer = master_layers[2]
                    
                    if third_layer and third_layer.paths:
                        # Position third layer right after H (H width already includes sidebearings)
                        h_width = h_layer.width
                        third_layer_offset = offset_x + h_width
                        
                        # Set color for the third layer
                        if self.use_black_color:
                            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
                        else:
                            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 1.0, 0.5).set()
                        
                        # Draw the third layer
                        third_bezierPath = third_layer.completeBezierPath
                        transform2 = NSAffineTransform.transform()
                        transform2.translateXBy_yBy_(third_layer_offset, 0)
                        
                        transformedPath2 = third_bezierPath.copy()
                        transformedPath2.transformUsingAffineTransform_(transform2)
                        transformedPath2.fill()
                        
                        # Draw another H to the right of the third layer
                        third_layer_width = third_layer.width
                        second_h_offset = third_layer_offset + third_layer_width
                        
                        # Set color for the final H
                        if self.use_black_color:
                            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0).set()
                        else:
                            NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.5).set()
                        
                        # Draw the second H
                        transform3 = NSAffineTransform.transform()
                        transform3.translateXBy_yBy_(second_h_offset, 0)
                        
                        transformedPath3 = bezierPath.copy()
                        transformedPath3.transformUsingAffineTransform_(transform3)
                        transformedPath3.fill()
            
        except Exception as e:
            print("Error drawing string: %s" % str(e))


# Run the script
TwoButtonWindow()