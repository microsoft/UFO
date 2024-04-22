# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import win32api
import win32con
import win32gui
import win32ui


class TransparentBox:
    """
    A transparent box to draw on the screen.
    """
    def __init__(self, box_width=3):
        """
        Create a new TransparentBox.
        :param box_width: The width of the box.
        """
        
        self.desktop = win32gui.GetDesktopWindow()
        self.desktop_dc = win32gui.GetWindowDC(self.desktop)
        self.dc = win32ui.CreateDCFromHandle(self.desktop_dc)
        self.dc.SetMapMode(win32con.MM_TEXT)
        self.pen = win32ui.CreatePen(win32con.PS_SOLID, box_width, win32api.RGB(255, 0, 0))
        self.brush = win32ui.CreateBrush(win32con.BS_NULL, 0, 0)
        self.started = False
        self.box_width = box_width  # Store the width of the box

    def start_drawing(self, left, top, right, bottom, screenshot):
        """
        Start drawing the rectangle.
        :param left: The left coordinate of the rectangle.
        :param top: The top coordinate of the rectangle.
        :param right: The right coordinate of the rectangle.
        :param bottom: The bottom coordinate of the rectangle.
        :param screenshot: The screenshot to draw on.
        """
        if not self.started:
            self.left = left 
            self.top = top  
            self.right = right  
            self.bottom = bottom 
            # Capture a screenshot of the area where the rectangle will be drawn
            self.screenshot = screenshot
            self.dc.SelectObject(self.pen)
            self.dc.SelectObject(self.brush)
            self.dc.Rectangle((self.left + self.box_width // 2, self.top + self.box_width // 2, self.right- self.box_width // 2, self.bottom- self.box_width // 2))
            self.started = True

    def end_drawing(self):
        """
        End drawing the rectangle.
        """
        if self.started:
            win32gui.ReleaseDC(self.desktop, self.desktop_dc)
            self.dc = None
            self.started = False

            # Restore the screenshot to erase the rectangle
            screenshot_dc = self.screenshot.load()
            self.desktop_dc = win32gui.GetWindowDC(self.desktop)

            # Set the pixels for the top and bottom borders of the rectangle
            for x in range(self.left, self.right):
                for y in range(self.top, self.top + self.box_width):  # Iterate over the width of the box for the top border
                    color = screenshot_dc[x - self.left, y - self.top]
                    win32gui.SetPixel(self.desktop_dc, x, y, win32api.RGB(color[0], color[1], color[2]))
                for y in range(self.bottom - self.box_width, self.bottom):  # Iterate over the width of the box for the bottom border
                    color = screenshot_dc[x - self.left, y - self.top]
                    win32gui.SetPixel(self.desktop_dc, x, y, win32api.RGB(color[0], color[1], color[2]))

            # Set the pixels for the left and right borders of the rectangle
            for y in range(self.top, self.bottom):
                for x in range(self.left, self.left + self.box_width):  # Iterate over the width of the box for the left border
                    color = screenshot_dc[x - self.left, y - self.top]
                    win32gui.SetPixel(self.desktop_dc, x, y, win32api.RGB(color[0], color[1], color[2]))
                for x in range(self.right - self.box_width, self.right):  # Iterate over the width of the box for the right border
                    color = screenshot_dc[x - self.left, y - self.top]
                    win32gui.SetPixel(self.desktop_dc, x, y, win32api.RGB(color[0], color[1], color[2]))

            win32gui.ReleaseDC(self.desktop, self.desktop_dc)
