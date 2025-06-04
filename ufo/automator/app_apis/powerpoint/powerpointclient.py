# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Dict, Type, List

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class PowerPointWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :return: The matched object.
        """

        object_name_list = [
            presentation.Name for presentation in self.client.Presentations
        ]
        matched_object = self.app_match(object_name_list)

        for presentation in self.client.Presentations:
            if presentation.Name == matched_object:
                return presentation

        return None

    def set_background_color(self, color: str, slide_index: List[int] = None) -> str:
        """
        Set the background color of the slide(s).
        :param color: The hex color code (in RGB format) to set the background color.
        :param slide_index: The list of slide indexes to set the background color. If None, set the background color for all slides.
        :return: The result of setting the background color.
        """

        if not slide_index:
            slide_index = range(1, self.com_object.Slides.Count + 1)

        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
        bgr_hex = (blue << 16) + (green << 8) + red

        try:
            for index in slide_index:
                if index < 1 or index > self.com_object.Slides.Count:
                    continue
                slide = self.com_object.Slides(index)
                slide.FollowMasterBackground = False
                slide.Background.Fill.Visible = True
                slide.Background.Fill.Solid()
                slide.Background.Fill.ForeColor.RGB = bgr_hex # PowerPoint uses BGR format
        except Exception as e:
            return f"Failed to set the background color. Error: {e}"

        return f"Successfully Set the background color to {color} for slide(s) {slide_index}."

    def save_as(
        self, file_dir: str = "", file_name: str = "", file_ext: str = "", current_slide_only: bool = False
    ) -> None:
        """
        Save the document to other formats.
        :param file_dir: The directory to save the file.
        :param file_name: The name of the file without extension.
        :param file_ext: The extension of the file.
        """

        ppt_ext_to_fileformat = {
            ".pptx": 24,  # PowerPoint Presentation (OpenXML)
            ".ppt": 0,  # PowerPoint 97-2003 Presentation
            ".pdf": 32,  # PDF file
            ".xps": 33,  # XPS file
            ".potx": 25,  # PowerPoint Template (OpenXML)
            ".pot": 5,  # PowerPoint 97-2003 Template
            ".ppsx": 27,  # PowerPoint Show (OpenXML)
            ".pps": 1,  # PowerPoint 97-2003 Show
            ".odp": 35,  # OpenDocument Presentation
            ".jpg": 17,  # JPG images (slides exported as .jpg)
            ".png": 18,  # PNG images
            ".gif": 19,  # GIF images
            ".bmp": 20,  # BMP images
            ".tif": 21,  # TIFF images
            ".tiff": 21,  # TIFF images
            ".rtf": 6,  # Outline RTF
            ".html": 12,  # Single File Web Page
            ".mp4": 39,  # MPEG-4 video (requires PowerPoint 2013+)
            ".wmv": 38,  # Windows Media Video
            ".xml": 10,  # PowerPoint 2003 XML Presentation
        }

        ppt_ext_to_formatstr = {
            ".jpg": "JPG",  # JPG images (slides exported as .jpg)
            ".png": "PNG",  # PNG images
            ".gif": "GIF",  # GIF images
            ".bmp": "BMP",  # BMP images
            ".tif": "TIF",  # TIFF images
            ".tiff": "TIF",  # TIFF images
        }

        if not file_dir:
            file_dir = os.path.dirname(self.com_object.FullName)
        if not file_name:
            file_name = os.path.splitext(os.path.basename(self.com_object.FullName))[0]
        if not file_ext:
            file_ext = ".pptx"

        file_path = os.path.join(file_dir, file_name + file_ext)

        try:
            if self.com_object.Slides.Count == 1 and file_ext in ppt_ext_to_formatstr.keys():
                self.com_object.Slides(1).Export(
                    file_path, ppt_ext_to_formatstr.get(file_ext, "PNG")
                )
            elif current_slide_only and file_ext in ppt_ext_to_formatstr.keys():
                current_slide_idx = self.com_object.SlideShowWindow.View.Slide.SlideIndex
                self.com_object.Slides(current_slide_idx).Export(
                    file_path, ppt_ext_to_formatstr.get(file_ext, "PNG")
                )
            else:
                self.com_object.SaveAs(
                    file_path, FileFormat=ppt_ext_to_fileformat.get(file_ext, 24)
                )
            return f"Document is saved to {file_path}."
        except Exception as e:
            return f"Failed to save the document to {file_path}. Error: {e}"

    def create_presentation(self, title: str = None, template_path: str = None) -> str:
        """
        Create a new PowerPoint presentation.
        :param title: Title for the new presentation
        :param template_path: Path to template file (optional)
        :return: Success message with presentation name
        """
        try:
            if template_path and os.path.exists(template_path):
                presentation = self.client.Presentations.Open(template_path)
            else:
                presentation = self.client.Presentations.Add()
            
            if title and presentation.Slides.Count > 0:
                # Set title on the first slide if it exists
                first_slide = presentation.Slides(1)
                for shape in first_slide.Shapes:
                    if shape.HasTextFrame and shape.TextFrame.HasText:
                        if "title" in shape.Name.lower():
                            shape.TextFrame.TextRange.Text = title
                            break
            
            return f"Presentation created successfully: {presentation.Name}"
        except Exception as e:
            return f"Failed to create presentation. Error: {e}"

    def open_presentation(self, file_path: str) -> str:
        """
        Open an existing PowerPoint presentation.
        :param file_path: Path to the PowerPoint file to open
        :return: Success message
        """
        try:
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            
            presentation = self.client.Presentations.Open(file_path)
            return f"Presentation opened successfully: {presentation.Name}"
        except Exception as e:
            return f"Failed to open presentation. Error: {e}"

    def save_presentation(self, file_path: str = None, file_format: str = "pptx") -> str:
        """
        Save the current presentation.
        :param file_path: Path where to save the presentation (optional if already saved)
        :param file_format: File format (pptx, pdf, etc.)
        :return: Success message
        """
        try:
            if file_path:
                format_map = {
                    'pptx': 24,  # ppSaveAsOpenXMLPresentation
                    'ppt': 0,    # ppSaveAsPresentation
                    'pdf': 32,   # ppSaveAsPDF
                    'xps': 33,   # ppSaveAsXPS
                    'jpg': 17,   # ppSaveAsJPG
                    'png': 18    # ppSaveAsPNG
                }
                
                self.com_object.SaveAs(file_path, FileFormat=format_map.get(file_format.lower(), 24))
                return f"Presentation saved to {file_path}"
            else:
                self.com_object.Save()
                return "Presentation saved successfully"
        except Exception as e:
            return f"Failed to save presentation. Error: {e}"

    def add_slide(self, layout: str = "content", position: int = None) -> str:
        """
        Add a new slide to the presentation.
        :param layout: Slide layout type (title, content, blank, etc.)
        :param position: Position where to insert the slide (optional, defaults to end)
        :return: Success message with slide number
        """
        try:
            layout_map = {
                'title': 1,          # ppLayoutTitle
                'content': 2,        # ppLayoutText
                'blank': 7,          # ppLayoutBlank
                'title_content': 2,  # ppLayoutText
                'section_header': 3, # ppLayoutObject
                'comparison': 4,     # ppLayoutChart
                'title_only': 5,     # ppLayoutTitleOnly
                'picture': 6         # ppLayoutObject
            }
            
            layout_id = layout_map.get(layout.lower(), 2)
            
            if position is None:
                position = self.com_object.Slides.Count + 1
            
            slide = self.com_object.Slides.Add(position, layout_id)
            return f"Slide added successfully at position {position} (Slide ID: {slide.SlideID})"
        except Exception as e:
            return f"Failed to add slide. Error: {e}"

    def delete_slide(self, slide_index: int) -> str:
        """
        Delete a slide from the presentation.
        :param slide_index: Index of the slide to delete (1-based)
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            self.com_object.Slides(slide_index).Delete()
            return f"Slide {slide_index} deleted successfully"
        except Exception as e:
            return f"Failed to delete slide. Error: {e}"

    def set_slide_title(self, slide_index: int, title: str) -> str:
        """
        Set the title of a specific slide.
        :param slide_index: Index of the slide (1-based)
        :param title: Title text to set
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            slide = self.com_object.Slides(slide_index)
            
            # Find the title placeholder
            for shape in slide.Shapes:
                if shape.HasTextFrame:
                    if shape.PlaceholderFormat.Type == 1:  # ppPlaceholderTitle
                        shape.TextFrame.TextRange.Text = title
                        return f"Title set for slide {slide_index}: {title}"
            
            # If no title placeholder found, try to find any text shape with "title" in name
            for shape in slide.Shapes:
                if shape.HasTextFrame and "title" in shape.Name.lower():
                    shape.TextFrame.TextRange.Text = title
                    return f"Title set for slide {slide_index}: {title}"
            
            return f"No title placeholder found on slide {slide_index}"
        except Exception as e:
            return f"Failed to set slide title. Error: {e}"

    def add_text_to_slide(self, slide_index: int, text: str, placeholder_index: int = None) -> str:
        """
        Add text content to a slide.
        :param slide_index: Index of the slide (1-based)
        :param text: Text content to add
        :param placeholder_index: Index of the text placeholder (optional)
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            slide = self.com_object.Slides(slide_index)
            
            if placeholder_index:
                # Use specific placeholder
                if placeholder_index <= slide.Shapes.Count:
                    shape = slide.Shapes(placeholder_index)
                    if shape.HasTextFrame:
                        shape.TextFrame.TextRange.Text = text
                        return f"Text added to slide {slide_index}, placeholder {placeholder_index}"
                return f"Placeholder {placeholder_index} not found or invalid"
            else:
                # Find content placeholder or first available text shape
                for shape in slide.Shapes:
                    if shape.HasTextFrame:
                        if hasattr(shape, 'PlaceholderFormat'):
                            if shape.PlaceholderFormat.Type in [2, 7]:  # ppPlaceholderBody or ppPlaceholderObject
                                shape.TextFrame.TextRange.Text = text
                                return f"Text added to slide {slide_index}"
                
                # If no content placeholder, add as new text box
                text_box = slide.Shapes.AddTextbox(
                    Orientation=1,  # msoTextOrientationHorizontal
                    Left=100, Top=100, Width=400, Height=200
                )
                text_box.TextFrame.TextRange.Text = text
                return f"Text added to slide {slide_index} as new text box"
                
        except Exception as e:
            return f"Failed to add text to slide. Error: {e}"

    def add_image_to_slide(self, slide_index: int, image_path: str, left: float = None, 
                          top: float = None, width: float = None, height: float = None) -> str:
        """
        Add an image to a slide.
        :param slide_index: Index of the slide (1-based)
        :param image_path: Path to the image file
        :param left: Left position in inches
        :param top: Top position in inches
        :param width: Width in inches
        :param height: Height in inches
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"
            
            slide = self.com_object.Slides(slide_index)
            
            # Convert inches to points (1 inch = 72 points)
            left_pts = (left * 72) if left else 100
            top_pts = (top * 72) if top else 100
            width_pts = (width * 72) if width else None
            height_pts = (height * 72) if height else None
            
            if width_pts and height_pts:
                picture = slide.Shapes.AddPicture(
                    FileName=image_path,
                    LinkToFile=False,
                    SaveWithDocument=True,
                    Left=left_pts,
                    Top=top_pts,
                    Width=width_pts,
                    Height=height_pts
                )
            else:
                picture = slide.Shapes.AddPicture(
                    FileName=image_path,
                    LinkToFile=False,
                    SaveWithDocument=True,
                    Left=left_pts,
                    Top=top_pts
                )
            
            return f"Image added to slide {slide_index}: {image_path}"
        except Exception as e:
            return f"Failed to add image to slide. Error: {e}"

    def add_chart_to_slide(self, slide_index: int, chart_type: str, data: dict) -> str:
        """
        Add a chart to a slide.
        :param slide_index: Index of the slide (1-based)
        :param chart_type: Type of chart (column, line, pie, etc.)
        :param data: Chart data in appropriate format
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            slide = self.com_object.Slides(slide_index)
            
            # Chart type mapping
            chart_types = {
                'column': 3,    # xlColumnClustered
                'line': 4,      # xlLine
                'pie': 5,       # xlPie
                'bar': 57,      # xlBarClustered
                'area': 1,      # xlArea
                'scatter': 74   # xlXYScatter
            }
            
            chart_type_id = chart_types.get(chart_type.lower(), 3)
            
            # Add chart shape
            chart_shape = slide.Shapes.AddChart2(
                Style=-1,
                Type=chart_type_id,
                Left=100, Top=100, Width=400, Height=300
            )
            
            # Set chart data if provided
            if data and 'categories' in data and 'values' in data:
                chart = chart_shape.Chart
                chart_data = chart.ChartData
                chart_data.Activate()
                
                # This is a simplified data setting - full implementation would handle various data formats
                workbook = chart_data.Workbook
                worksheet = workbook.Worksheets(1)
                
                # Clear existing data
                worksheet.Cells.Clear()
                
                # Set categories and values
                categories = data['categories']
                values = data['values']
                
                for i, category in enumerate(categories, 1):
                    worksheet.Cells(i + 1, 1).Value = category
                
                for i, value in enumerate(values, 1):
                    worksheet.Cells(i + 1, 2).Value = value
            
            return f"Chart added to slide {slide_index}: {chart_type}"
        except Exception as e:
            return f"Failed to add chart to slide. Error: {e}"

    def format_text(self, slide_index: int, text_range: dict, font_name: str = None,
                   font_size: int = None, bold: bool = None, italic: bool = None,
                   color: str = None) -> str:
        """
        Format text in a text box or placeholder.
        :param slide_index: Index of the slide (1-based)
        :param text_range: Text range to format (shape index, start, length)
        :param font_name: Font name
        :param font_size: Font size
        :param bold: Bold formatting
        :param italic: Italic formatting
        :param color: Font color (hex or name)
        :return: Success message
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            slide = self.com_object.Slides(slide_index)
            
            shape_index = text_range.get('shape_index', 1)
            start_pos = text_range.get('start', 1)
            length = text_range.get('length', -1)  # -1 means to end
            
            if shape_index > slide.Shapes.Count:
                return f"Shape index {shape_index} is out of range"
            
            shape = slide.Shapes(shape_index)
            if not shape.HasTextFrame:
                return f"Shape {shape_index} does not contain text"
            
            text_frame = shape.TextFrame.TextRange
            if length == -1:
                format_range = text_frame.Characters(start_pos)
            else:
                format_range = text_frame.Characters(start_pos, length)
            
            font_obj = format_range.Font
            
            if font_name:
                font_obj.Name = font_name
            if font_size:
                font_obj.Size = font_size
            if bold is not None:
                font_obj.Bold = bold
            if italic is not None:
                font_obj.Italic = italic
            if color:
                if color.startswith('#'):
                    # Convert hex to RGB
                    rgb_val = int(color[1:], 16)
                    font_obj.Color.RGB = rgb_val
                else:
                    # Named color or direct RGB value
                    font_obj.Color.RGB = color
            
            return f"Text formatted successfully on slide {slide_index}"
        except Exception as e:
            return f"Failed to format text. Error: {e}"

    def start_slideshow(self, from_slide: int = 1) -> str:
        """
        Start the slideshow presentation.
        :param from_slide: Starting slide index (optional)
        :return: Success message
        """
        try:
            if from_slide < 1 or from_slide > self.com_object.Slides.Count:
                return f"Starting slide {from_slide} is out of range"
            
            self.com_object.SlideShowSettings.StartingSlide = from_slide
            self.com_object.SlideShowSettings.EndingSlide = self.com_object.Slides.Count
            slideshow = self.com_object.SlideShowSettings.Run()
            
            return f"Slideshow started from slide {from_slide}"
        except Exception as e:
            return f"Failed to start slideshow. Error: {e}"

    def export_presentation(self, output_path: str, export_format: str, quality: str = "high") -> str:
        """
        Export presentation to different formats.
        :param output_path: Output file path
        :param export_format: Export format (pdf, images, video, etc.)
        :param quality: Export quality (high, medium, low)
        :return: Success message
        """
        try:
            format_map = {
                'pdf': 32,      # ppSaveAsPDF
                'xps': 33,      # ppSaveAsXPS
                'jpg': 17,      # ppSaveAsJPG
                'png': 18,      # ppSaveAsPNG
                'gif': 16,      # ppSaveAsGIF
                'bmp': 19,      # ppSaveAsBMP
                'tiff': 21,     # ppSaveAsTIFF
                'wmv': 38,      # ppSaveAsWMV
                'mp4': 39       # ppSaveAsMP4
            }
            
            file_format = format_map.get(export_format.lower(), 32)
            
            if export_format.lower() in ['pdf', 'xps']:
                self.com_object.ExportAsFixedFormat(
                    Path=output_path,
                    FixedFormatType=file_format,
                    Quality=1 if quality.lower() == 'high' else 0  # ppFixedFormatIntentPrint or ppFixedFormatIntentScreen
                )
            elif export_format.lower() in ['jpg', 'png', 'gif', 'bmp', 'tiff']:
                # Export all slides as images
                for i in range(1, self.com_object.Slides.Count + 1):
                    slide = self.com_object.Slides(i)
                    file_name = f"{os.path.splitext(output_path)[0]}_slide_{i}.{export_format.lower()}"
                    slide.Export(file_name, export_format.upper())
            else:
                self.com_object.SaveAs(output_path, FileFormat=file_format)
            
            return f"Presentation exported to {output_path} in {export_format} format"
        except Exception as e:
            return f"Failed to export presentation. Error: {e}"

    def get_slide_count(self) -> int:
        """
        Get the total number of slides in the presentation.
        :return: Number of slides
        """
        try:
            return self.com_object.Slides.Count
        except Exception as e:
            return f"Failed to get slide count. Error: {e}"

    def get_slide_content(self, slide_index: int) -> dict:
        """
        Get the content of a specific slide.
        :param slide_index: Index of the slide (1-based)
        :return: Dictionary with slide content information
        """
        try:
            if slide_index < 1 or slide_index > self.com_object.Slides.Count:
                return f"Slide index {slide_index} is out of range"
            
            slide = self.com_object.Slides(slide_index)
            content = {
                'slide_number': slide_index,
                'slide_id': slide.SlideID,
                'layout': slide.Layout,
                'shapes_count': slide.Shapes.Count,
                'title': '',
                'text_content': [],
                'images': [],
                'charts': []
            }
            
            # Extract content from shapes
            for i in range(1, slide.Shapes.Count + 1):
                shape = slide.Shapes(i)
                
                if shape.HasTextFrame:
                    text = shape.TextFrame.TextRange.Text.strip()
                    if text:
                        if hasattr(shape, 'PlaceholderFormat'):
                            if shape.PlaceholderFormat.Type == 1:  # Title placeholder
                                content['title'] = text
                            else:
                                content['text_content'].append(text)
                        else:
                            content['text_content'].append(text)
                
                elif shape.Type == 13:  # Picture type
                    content['images'].append({
                        'name': shape.Name,
                        'left': shape.Left,
                        'top': shape.Top,
                        'width': shape.Width,
                        'height': shape.Height
                    })
                
                elif shape.Type == 3:  # Chart type
                    content['charts'].append({
                        'name': shape.Name,
                        'chart_type': shape.Chart.ChartType if hasattr(shape, 'Chart') else 'Unknown'
                    })
            
            return content
        except Exception as e:
            return f"Failed to get slide content. Error: {e}"

    @property
    def type_name(self):
        return "COM/POWERPOINT"

    @property
    def xml_format_code(self) -> int:
        return 10


@PowerPointWinCOMReceiver.register
class SetBackgroundColorCommand(WinCOMCommand):
    """
    The command to set the background color of the slide(s).
    """

    def execute(self):
        """
        Execute the command to set the background color of the slide(s).
        :return: The result of setting the background color.
        """
        return self.receiver.set_background_color(
            self.params.get("color", ""), self.params.get("slide_index", [])
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "set_background_color"


@PowerPointWinCOMReceiver.register
class SaveAsCommand(WinCOMCommand):
    """
    The command to save the document to PDF.
    """

    def execute(self):
        """
        Execute the command to save the document to PDF.
        :return: The result of saving the document to PDF.
        """
        return self.receiver.save_as(
            self.params.get("file_dir"),
            self.params.get("file_name"),
            self.params.get("file_ext"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "save_as"
