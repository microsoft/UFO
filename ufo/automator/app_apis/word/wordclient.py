# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from typing import Dict, Type

from ufo.automator.app_apis.basic import WinCOMCommand, WinCOMReceiverBasic
from ufo.automator.basic import CommandBasic


class WordWinCOMReceiver(WinCOMReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def get_object_from_process_name(self) -> None:
        """
        Get the object from the process name.
        :return: The matched object.
        """
        object_name_list = [doc.Name for doc in self.client.Documents]
        matched_object = self.app_match(object_name_list)

        for doc in self.client.Documents:
            if doc.Name == matched_object:
                return doc

        return None

    def insert_table(self, rows: int, columns: int) -> object:
        """
        Insert a table at the end of the document.
        :param rows: The number of rows.
        :param columns: The number of columns.
        :return: The inserted table.
        """

        # Get the range at the end of the document
        end_range = self.com_object.Range()
        end_range.Collapse(0)  # Collapse the range to the end

        # Insert a paragraph break (optional)
        end_range.InsertParagraphAfter()
        table = self.com_object.Tables.Add(end_range, rows, columns)
        table.Borders.Enable = True

        return table

    def select_text(self, text: str) -> None:
        """
        Select the text in the document.
        :param text: The text to be selected.
        """
        finder = self.com_object.Range().Find
        finder.Text = text

        if finder.Execute():
            finder.Parent.Select()
            return f"Text {text} is selected."
        else:
            return f"Text {text} is not found."

    def select_paragraph(
        self, start_index: int, end_index: int, non_empty: bool = True
    ) -> None:
        """
        Select a paragraph in the document.
        :param start_index: The start index of the paragraph.
        :param end_index: The end index of the paragraph, if ==-1, select to the end of the document.
        :param non_empty: Whether to select the non-empty paragraphs only.
        """
        paragraphs = self.com_object.Paragraphs

        start_index = max(1, start_index)

        if non_empty:
            paragraphs = [p for p in paragraphs if p.Range.Text.strip()]

        para_start = paragraphs[start_index - 1].Range.Start

        # Select to the end of the document if end_index == -1
        if end_index == -1:
            para_end = self.com_object.Range().End
        else:
            para_end = paragraphs[end_index - 1].Range.End

        self.com_object.Range(para_start, para_end).Select()

    def select_table(self, number: int) -> None:
        """
        Select a table in the document.
        :param number: The number of the table.
        """
        tables = self.com_object.Tables
        if not number or number < 1 or number > tables.Count:
            return f"Table number {number} is out of range."

        tables(number).Select()
        return f"Table {number} is selected."

    def set_font(self, font_name: str = None, font_size: int = None) -> None:
        """
        Set the font of the selected text in the active Word document.

        :param font_name: The name of the font (e.g., "Arial", "Times New Roman", "宋体").
                        If None, the font name will not be changed.
        :param font_size: The font size (e.g., 12).
                        If None, the font size will not be changed.
        """
        selection = self.client.Selection

        if selection.Type == 0:  # wdNoSelection

            return "No text is selected to set the font."

        font = selection.Range.Font

        message = ""

        if font_name:
            font.Name = font_name
            message += f"Font is set to {font_name}."

        if font_size:
            font.Size = font_size
            message += f" Font size is set to {font_size}."

        print(message)
        return message

    def save_as(
        self, file_dir: str = "", file_name: str = "", file_ext: str = ""
    ) -> None:
        """
        Save the document to PDF.
        :param file_dir: The directory to save the file.
        :param file_name: The name of the file without extension.
        :param file_ext: The extension of the file.
        """

        ext_to_fileformat = {
            ".doc": 0,  # Word 97-2003 Document
            ".dot": 1,  # Word 97-2003 Template
            ".txt": 2,  # Plain Text (ASCII)
            ".rtf": 6,  # Rich Text Format (RTF)
            ".unicode.txt": 7,  # Unicode Text (custom extension, for clarity)
            ".htm": 8,  # Web Page (HTML)
            ".html": 8,  # Web Page (HTML)
            ".mht": 9,  # Single File Web Page (MHT)
            ".xml": 11,  # Word 2003 XML Document
            ".docx": 12,  # Word Document (default)
            ".docm": 13,  # Word Macro-Enabled Document
            ".dotx": 14,  # Word Template (no macros)
            ".dotm": 15,  # Word Macro-Enabled Template
            ".pdf": 17,  # PDF File
            ".xps": 18,  # XPS File
        }

        if not file_dir:
            file_dir = os.path.dirname(self.com_object.FullName)
        if not file_name:
            file_name = os.path.splitext(os.path.basename(self.com_object.FullName))[0]
        if not file_ext:
            file_ext = ".pdf"

        file_path = os.path.join(file_dir, file_name + file_ext)

        try:
            self.com_object.SaveAs(
                file_path, FileFormat=ext_to_fileformat.get(file_ext, 17)
            )
            return f"Document is saved to {file_path}."
        except Exception as e:
            return f"Failed to save the document to {file_path}. Error: {e}"

    def create_document(self, template_path: str = None) -> str:
        """
        Create a new Word document.
        :param template_path: Path to template file (optional)
        :return: Success message with document name
        """
        try:
            if template_path and os.path.exists(template_path):
                document = self.client.Documents.Add(Template=template_path)
            else:
                document = self.client.Documents.Add()
            return f"Document created successfully: {document.Name}"
        except Exception as e:
            return f"Failed to create document. Error: {e}"

    def open_document(
        self, file_path: str, read_only: bool = False, password: str = None
    ) -> str:
        """
        Open an existing Word document.
        :param file_path: Path to the Word file
        :param read_only: Whether to open in read-only mode
        :param password: Password for protected files
        :return: Success message
        """
        try:
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"

            if password:
                document = self.client.Documents.Open(
                    file_path, ReadOnly=read_only, PasswordDocument=password
                )
            else:
                document = self.client.Documents.Open(file_path, ReadOnly=read_only)
            return f"Document opened successfully: {document.Name}"
        except Exception as e:
            return f"Failed to open document. Error: {e}"

    def close_document(self, save_changes: bool = True, document_name: str = None) -> str:
        """
        Close the active or specified document.
        :param save_changes: Whether to save changes before closing
        :param document_name: Name of specific document to close (optional)
        :return: Success message
        """
        try:
            if document_name:
                document = self.client.Documents(document_name)
            else:
                document = self.com_object

            document.Close(SaveChanges=1 if save_changes else 0)
            return f"Document closed successfully"
        except Exception as e:
            return f"Failed to close document. Error: {e}"

    def insert_text(self, text: str, position: str = "end") -> str:
        """
        Insert text at specified position.
        :param text: Text to insert
        :param position: Position to insert (start, end, cursor)
        :return: Success message
        """
        try:
            if position == "start":
                range_obj = self.com_object.Range(0, 0)
            elif position == "cursor":
                range_obj = self.client.Selection.Range
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)  # Collapse to end

            range_obj.InsertAfter(text)
            return f"Text inserted successfully at {position}"
        except Exception as e:
            return f"Failed to insert text. Error: {e}"

    def replace_text(self, find_text: str, replace_text: str, replace_all: bool = True) -> str:
        """
        Replace text in the document.
        :param find_text: Text to find
        :param replace_text: Text to replace with
        :param replace_all: Whether to replace all occurrences
        :return: Success message with count
        """
        try:
            find_obj = self.com_object.Range().Find
            find_obj.ClearFormatting()
            find_obj.Text = find_text
            find_obj.Replacement.ClearFormatting()
            find_obj.Replacement.Text = replace_text

            if replace_all:
                count = find_obj.Execute(Replace=2)  # wdReplaceAll
                return f"Replaced {count} occurrences of '{find_text}' with '{replace_text}'"
            else:
                success = find_obj.Execute(Replace=1)  # wdReplaceOne
                return f"Replaced first occurrence: {success}"
        except Exception as e:
            return f"Failed to replace text. Error: {e}"

    def format_text(
        self,
        text: str = None,
        font_name: str = None,
        font_size: int = None,
        bold: bool = None,
        italic: bool = None,
        underline: bool = None,
        font_color: str = None,
    ) -> str:
        """
        Format selected text or specific text.
        :param text: Specific text to format (if None, formats selected text)
        :param font_name: Font name
        :param font_size: Font size
        :param bold: Bold formatting
        :param italic: Italic formatting
        :param underline: Underline formatting
        :param font_color: Font color (hex)
        :return: Success message
        """
        try:
            if text:
                # Find and select the specific text first
                self.select_text(text)

            selection = self.client.Selection
            if selection.Type == 0:  # wdNoSelection
                return "No text is selected to format."

            font_obj = selection.Range.Font

            if font_name:
                font_obj.Name = font_name
            if font_size:
                font_obj.Size = font_size
            if bold is not None:
                font_obj.Bold = bold
            if italic is not None:
                font_obj.Italic = italic
            if underline is not None:
                font_obj.Underline = 1 if underline else 0
            if font_color:
                font_obj.Color = int(font_color.replace("#", ""), 16)

            return "Text formatted successfully"
        except Exception as e:
            return f"Failed to format text. Error: {e}"

    def insert_heading(self, text: str, level: int = 1, position: str = "end") -> str:
        """
        Insert a heading with specified level.
        :param text: Heading text
        :param level: Heading level (1-9)
        :param position: Position to insert
        :return: Success message
        """
        try:
            if position == "start":
                range_obj = self.com_object.Range(0, 0)
            elif position == "cursor":
                range_obj = self.client.Selection.Range
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)

            range_obj.InsertAfter(text)
            range_obj.Style = f"Heading {level}"
            range_obj.InsertParagraphAfter()

            return f"Heading level {level} inserted: {text}"
        except Exception as e:
            return f"Failed to insert heading. Error: {e}"

    def insert_paragraph(self, text: str = "", position: str = "end") -> str:
        """
        Insert a new paragraph.
        :param text: Text for the paragraph
        :param position: Position to insert
        :return: Success message
        """
        try:
            if position == "start":
                range_obj = self.com_object.Range(0, 0)
            elif position == "cursor":
                range_obj = self.client.Selection.Range
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)

            range_obj.InsertParagraphAfter()
            if text:
                range_obj.InsertAfter(text)

            return "Paragraph inserted successfully"
        except Exception as e:
            return f"Failed to insert paragraph. Error: {e}"

    def insert_page_break(self, position: str = "cursor") -> str:
        """
        Insert a page break.
        :param position: Position to insert (cursor, end)
        :return: Success message
        """
        try:
            if position == "cursor":
                self.client.Selection.InsertBreak(7)  # wdPageBreak
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)
                range_obj.InsertBreak(7)

            return "Page break inserted successfully"
        except Exception as e:
            return f"Failed to insert page break. Error: {e}"

    def insert_image(
        self,
        image_path: str,
        position: str = "cursor",
        width: float = None,
        height: float = None,
    ) -> str:
        """
        Insert an image into the document.
        :param image_path: Path to the image file
        :param position: Position to insert
        :param width: Image width in points
        :param height: Image height in points
        :return: Success message
        """
        try:
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"

            if position == "cursor":
                range_obj = self.client.Selection.Range
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)

            shape = range_obj.InlineShapes.AddPicture(image_path)

            if width:
                shape.Width = width
            if height:
                shape.Height = height

            return f"Image inserted successfully: {image_path}"
        except Exception as e:
            return f"Failed to insert image. Error: {e}"

    def format_table(
        self, table_number: int, style: str = None, border_style: int = None, border_width: float = None
    ) -> str:
        """
        Format a table in the document.
        :param table_number: Table number to format
        :param style: Table style name
        :param border_style: Border style
        :param border_width: Border width in points
        :return: Success message
        """
        try:
            if table_number < 1 or table_number > self.com_object.Tables.Count:
                return f"Table number {table_number} is out of range"

            table = self.com_object.Tables(table_number)

            if style:
                table.Style = style

            if border_style is not None:
                table.Borders.OutsideLineStyle = border_style
                table.Borders.InsideLineStyle = border_style

            if border_width is not None:
                table.Borders.OutsideLineWidth = border_width
                table.Borders.InsideLineWidth = border_width

            return f"Table {table_number} formatted successfully"
        except Exception as e:
            return f"Failed to format table. Error: {e}"

    def insert_hyperlink(self, text: str, url: str, position: str = "cursor") -> str:
        """
        Insert a hyperlink.
        :param text: Display text for the hyperlink
        :param url: URL to link to
        :param position: Position to insert
        :return: Success message
        """
        try:
            if position == "cursor":
                range_obj = self.client.Selection.Range
            else:  # end
                range_obj = self.com_object.Range()
                range_obj.Collapse(0)

            self.com_object.Hyperlinks.Add(
                Anchor=range_obj, Address=url, TextToDisplay=text
            )

            return f"Hyperlink inserted: {text} -> {url}"
        except Exception as e:
            return f"Failed to insert hyperlink. Error: {e}"

    def set_page_margins(
        self, top: float = None, bottom: float = None, left: float = None, right: float = None
    ) -> str:
        """
        Set page margins (in points).
        :param top: Top margin
        :param bottom: Bottom margin
        :param left: Left margin
        :param right: Right margin
        :return: Success message
        """
        try:
            page_setup = self.com_object.PageSetup

            if top is not None:
                page_setup.TopMargin = top
            if bottom is not None:
                page_setup.BottomMargin = bottom
            if left is not None:
                page_setup.LeftMargin = left
            if right is not None:
                page_setup.RightMargin = right

            return "Page margins set successfully"
        except Exception as e:
            return f"Failed to set page margins. Error: {e}"

    def set_page_orientation(self, orientation: str) -> str:
        """
        Set page orientation.
        :param orientation: 'portrait' or 'landscape'
        :return: Success message
        """
        try:
            page_setup = self.com_object.PageSetup

            if orientation.lower() == "portrait":
                page_setup.Orientation = 0  # wdOrientPortrait
            elif orientation.lower() == "landscape":
                page_setup.Orientation = 1  # wdOrientLandscape
            else:
                return f"Invalid orientation: {orientation}. Use 'portrait' or 'landscape'"

            return f"Page orientation set to {orientation}"
        except Exception as e:
            return f"Failed to set page orientation. Error: {e}"

    def insert_header_footer(
        self, text: str, header: bool = True, first_page_different: bool = False
    ) -> str:
        """
        Insert header or footer.
        :param text: Text to insert
        :param header: True for header, False for footer
        :param first_page_different: Whether first page should be different
        :return: Success message
        """
        try:
            section = self.com_object.Sections(1)

            if first_page_different:
                section.PageSetup.DifferentFirstPageHeaderFooter = True

            if header:
                if first_page_different:
                    header_footer = section.Headers(2)  # wdHeaderFooterFirstPage
                else:
                    header_footer = section.Headers(1)  # wdHeaderFooterPrimary
                location = "header"
            else:
                if first_page_different:
                    header_footer = section.Footers(2)  # wdHeaderFooterFirstPage
                else:
                    header_footer = section.Footers(1)  # wdHeaderFooterPrimary
                location = "footer"

            header_footer.Range.Text = text

            return f"{location.capitalize()} inserted successfully"
        except Exception as e:
            return f"Failed to insert {location}. Error: {e}"

    def track_changes(self, enable: bool = True) -> str:
        """
        Enable or disable track changes.
        :param enable: Whether to enable track changes
        :return: Success message
        """
        try:
            self.com_object.TrackRevisions = enable
            status = "enabled" if enable else "disabled"
            return f"Track changes {status}"
        except Exception as e:
            return f"Failed to toggle track changes. Error: {e}"

    def accept_all_changes(self) -> str:
        """
        Accept all tracked changes in the document.
        :return: Success message
        """
        try:
            self.com_object.Revisions.AcceptAll()
            return "All changes accepted"
        except Exception as e:
            return f"Failed to accept all changes. Error: {e}"

    def reject_all_changes(self) -> str:
        """
        Reject all tracked changes in the document.
        :return: Success message
        """
        try:
            self.com_object.Revisions.RejectAll()
            return "All changes rejected"
        except Exception as e:
            return f"Failed to reject all changes. Error: {e}"

    def export_document(self, file_path: str, export_format: str) -> str:
        """
        Export document to different format.
        :param file_path: Output file path
        :param export_format: Export format (pdf, xps, html, etc.)
        :return: Success message
        """
        try:
            format_map = {
                "pdf": 17,  # wdExportFormatPDF
                "xps": 18,  # wdExportFormatXPS
                "html": 8,  # wdFormatHTML
                "rtf": 6,  # wdFormatRTF
                "txt": 2,  # wdFormatText
            }

            if export_format.lower() in ["pdf", "xps"]:
                self.com_object.ExportAsFixedFormat(
                    OutputFileName=file_path, ExportFormat=format_map[export_format.lower()]
                )
            else:
                self.com_object.SaveAs2(
                    FileName=file_path, FileFormat=format_map.get(export_format.lower(), 17)
                )

            return f"Document exported to {file_path}"
        except Exception as e:
            return f"Failed to export document. Error: {e}"

    def get_document_info(self) -> dict:
        """
        Get information about the current document.
        :return: Dictionary with document information
        """
        try:
            info = {
                "name": self.com_object.Name,
                "full_name": self.com_object.FullName,
                "saved": self.com_object.Saved,
                "page_count": self.com_object.ComputeStatistics(2),  # wdStatisticPages
                "word_count": self.com_object.ComputeStatistics(0),  # wdStatisticWords
                "character_count": self.com_object.ComputeStatistics(3),  # wdStatisticCharacters
                "paragraph_count": self.com_object.ComputeStatistics(4),  # wdStatisticParagraphs
                "table_count": self.com_object.Tables.Count,
                "revision_count": self.com_object.Revisions.Count,
                "track_changes": self.com_object.TrackRevisions,
            }
            return info
        except Exception as e:
            return f"Failed to get document info. Error: {e}"

    def get_word_count(self) -> int:
        """
        Get the word count of the document.
        :return: Word count
        """
        try:
            return self.com_object.ComputeStatistics(0)  # wdStatisticWords
        except Exception as e:
            return f"Failed to get word count. Error: {e}"

    def spell_check(self) -> str:
        """
        Run spell check on the document.
        :return: Success message with error count
        """
        try:
            # Check spelling and grammar
            self.com_object.CheckSpelling()

            # Count spelling errors
            error_count = 0
            for error in self.com_object.SpellingErrors:
                error_count += 1

            if error_count == 0:
                return "No spelling errors found"
            else:
                return f"Spell check completed. {error_count} errors found"
        except Exception as e:
            return f"Failed to run spell check. Error: {e}"

    def save_document(self, file_path: str = None, format: str = "docx") -> str:
        """
        Save the current document.
        :param file_path: Path where to save the document (optional if already saved)
        :param format: File format (docx, pdf, rtf, etc.)
        :return: Success message
        """
        try:
            if file_path:
                # Format mapping for different file formats
                format_map = {
                    "docx": 12,  # Word Document (default)
                    "doc": 0,   # Word 97-2003 Document
                    "pdf": 17,  # PDF File
                    "rtf": 6,   # Rich Text Format
                    "txt": 2,   # Plain Text
                    "html": 8,  # HTML format
                    "xml": 11,  # Word 2003 XML Document
                    "docm": 13, # Word Macro-Enabled Document
                    "dotx": 14, # Word Template
                    "xps": 18   # XPS File
                }
                
                file_format = format_map.get(format.lower(), 12)  # Default to docx
                
                if format.lower() in ["pdf", "xps"]:
                    self.com_object.ExportAsFixedFormat(
                        OutputFileName=file_path, 
                        ExportFormat=file_format
                    )
                else:
                    self.com_object.SaveAs2(FileName=file_path, FileFormat=file_format)
                
                return f"Document saved to {file_path} in {format} format"
            else:
                # Save to current location if no path specified
                self.com_object.Save()
                return f"Document saved to current location: {self.com_object.FullName}"
        except Exception as e:
            return f"Failed to save document. Error: {e}"

    @property
    def type_name(self):
        return "COM/WORD"

    @property
    def xml_format_code(self) -> int:
        return 11


@WordWinCOMReceiver.register
class InsertTableCommand(WinCOMCommand):
    """
    The command to insert a table.
    """

    def execute(self):
        """
        Execute the command to insert a table.
        :return: The inserted table.
        """
        return self.receiver.insert_table(
            self.params.get("rows"), self.params.get("columns")
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "insert_table"


@WordWinCOMReceiver.register
class SelectTextCommand(WinCOMCommand):
    """
    The command to select text.
    """

    def execute(self):
        """
        Execute the command to select text.
        :return: The selected text.
        """
        return self.receiver.select_text(self.params.get("text"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_text"


@WordWinCOMReceiver.register
class SelectTableCommand(WinCOMCommand):
    """
    The command to select a table.
    """

    def execute(self):
        """
        Execute the command to select a table in the document.
        :return: The selected table.
        """
        return self.receiver.select_table(self.params.get("number"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_table"


@WordWinCOMReceiver.register
class SelectParagraphCommand(WinCOMCommand):
    """
    The command to select a paragraph.
    """

    def execute(self):
        """
        Execute the command to select a paragraph in the document.
        :return: The selected paragraph.
        """
        return self.receiver.select_paragraph(
            self.params.get("start_index"),
            self.params.get("end_index"),
            self.params.get("non_empty"),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_paragraph"


@WordWinCOMReceiver.register
class SaveAsCommand(WinCOMCommand):
    """
    The command to save the document to PDF.
    """

    def execute(self):
        """
        Execute the command to save the document to PDF.
        :return: The saved PDF file path.
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


@WordWinCOMReceiver.register
class SetFontCommand(WinCOMCommand):
    """
    The command to set the font of the selected text.
    """

    def execute(self):
        """
        Execute the command to set the font of the selected text.
        :return: The message of the font setting.
        """
        return self.receiver.set_font(
            self.params.get("font_name"), self.params.get("font_size")
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "set_font"


@WordWinCOMReceiver.register
class CreateDocumentCommand(WinCOMCommand):
    """Command to create a new document."""
    
    def execute(self):
        return self.receiver.create_document(
            template_path=self.params.get("template_path")
        )
    
    @classmethod
    def name(cls) -> str:
        return "create_document"


@WordWinCOMReceiver.register
class OpenDocumentCommand(WinCOMCommand):
    """Command to open an existing document."""
    
    def execute(self):
        return self.receiver.open_document(
            file_path=self.params.get("file_path"),
            read_only=self.params.get("read_only", False),
            password=self.params.get("password")
        )
    
    @classmethod
    def name(cls) -> str:
        return "open_document"


@WordWinCOMReceiver.register
class CloseDocumentCommand(WinCOMCommand):
    """Command to close a document."""
    
    def execute(self):
        return self.receiver.close_document(
            save_changes=self.params.get("save_changes", True),
            document_name=self.params.get("document_name")
        )
    
    @classmethod
    def name(cls) -> str:
        return "close_document"


@WordWinCOMReceiver.register
class InsertTextCommand(WinCOMCommand):
    """Command to insert text."""
    
    def execute(self):
        return self.receiver.insert_text(
            text=self.params.get("text"),
            position=self.params.get("position", "end")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_text"


@WordWinCOMReceiver.register
class ReplaceTextCommand(WinCOMCommand):
    """Command to replace text."""
    
    def execute(self):
        return self.receiver.replace_text(
            find_text=self.params.get("find_text"),
            replace_text=self.params.get("replace_text"),
            replace_all=self.params.get("replace_all", True)
        )
    
    @classmethod
    def name(cls) -> str:
        return "replace_text"


@WordWinCOMReceiver.register
class FormatTextCommand(WinCOMCommand):
    """Command to format text."""
    
    def execute(self):
        return self.receiver.format_text(
            text=self.params.get("text"),
            font_name=self.params.get("font_name"),
            font_size=self.params.get("font_size"),
            bold=self.params.get("bold"),
            italic=self.params.get("italic"),
            underline=self.params.get("underline"),
            font_color=self.params.get("font_color")
        )
    
    @classmethod
    def name(cls) -> str:
        return "format_text"


@WordWinCOMReceiver.register
class InsertHeadingCommand(WinCOMCommand):
    """Command to insert heading."""
    
    def execute(self):
        return self.receiver.insert_heading(
            text=self.params.get("text"),
            level=self.params.get("level", 1),
            position=self.params.get("position", "end")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_heading"


@WordWinCOMReceiver.register
class InsertParagraphCommand(WinCOMCommand):
    """Command to insert paragraph."""
    
    def execute(self):
        return self.receiver.insert_paragraph(
            text=self.params.get("text", ""),
            position=self.params.get("position", "end")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_paragraph"


@WordWinCOMReceiver.register
class InsertPageBreakCommand(WinCOMCommand):
    """Command to insert page break."""
    
    def execute(self):
        return self.receiver.insert_page_break(
            position=self.params.get("position", "cursor")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_page_break"


@WordWinCOMReceiver.register
class InsertImageCommand(WinCOMCommand):
    """Command to insert image."""
    
    def execute(self):
        return self.receiver.insert_image(
            image_path=self.params.get("image_path"),
            position=self.params.get("position", "cursor"),
            width=self.params.get("width"),
            height=self.params.get("height")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_image"


@WordWinCOMReceiver.register
class FormatTableCommand(WinCOMCommand):
    """Command to format table."""
    
    def execute(self):
        return self.receiver.format_table(
            table_number=self.params.get("table_number"),
            style=self.params.get("style"),
            border_style=self.params.get("border_style"),
            border_width=self.params.get("border_width")
        )
    
    @classmethod
    def name(cls) -> str:
        return "format_table"


@WordWinCOMReceiver.register
class InsertHyperlinkCommand(WinCOMCommand):
    """Command to insert hyperlink."""
    
    def execute(self):
        return self.receiver.insert_hyperlink(
            text=self.params.get("text"),
            url=self.params.get("url"),
            position=self.params.get("position", "cursor")
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_hyperlink"


@WordWinCOMReceiver.register
class SetPageMarginsCommand(WinCOMCommand):
    """Command to set page margins."""
    
    def execute(self):
        return self.receiver.set_page_margins(
            top=self.params.get("top"),
            bottom=self.params.get("bottom"),
            left=self.params.get("left"),
            right=self.params.get("right")
        )
    
    @classmethod
    def name(cls) -> str:
        return "set_page_margins"


@WordWinCOMReceiver.register
class SetPageOrientationCommand(WinCOMCommand):
    """Command to set page orientation."""
    
    def execute(self):
        return self.receiver.set_page_orientation(
            orientation=self.params.get("orientation")
        )
    
    @classmethod
    def name(cls) -> str:
        return "set_page_orientation"


@WordWinCOMReceiver.register
class InsertHeaderFooterCommand(WinCOMCommand):
    """Command to insert header/footer."""
    
    def execute(self):
        return self.receiver.insert_header_footer(
            text=self.params.get("text"),
            header=self.params.get("header", True),
            first_page_different=self.params.get("first_page_different", False)
        )
    
    @classmethod
    def name(cls) -> str:
        return "insert_header_footer"


@WordWinCOMReceiver.register
class TrackChangesCommand(WinCOMCommand):
    """Command to enable/disable track changes."""
    
    def execute(self):
        return self.receiver.track_changes(
            enable=self.params.get("enable", True)
        )
    
    @classmethod
    def name(cls) -> str:
        return "track_changes"


@WordWinCOMReceiver.register
class AcceptAllChangesCommand(WinCOMCommand):
    """Command to accept all changes."""
    
    def execute(self):
        return self.receiver.accept_all_changes()
    
    @classmethod
    def name(cls) -> str:
        return "accept_all_changes"


@WordWinCOMReceiver.register
class RejectAllChangesCommand(WinCOMCommand):
    """Command to reject all changes."""
    
    def execute(self):
        return self.receiver.reject_all_changes()
    
    @classmethod
    def name(cls) -> str:
        return "reject_all_changes"


@WordWinCOMReceiver.register
class ExportDocumentCommand(WinCOMCommand):
    """Command to export document."""
    
    def execute(self):
        return self.receiver.export_document(
            file_path=self.params.get("file_path"),
            export_format=self.params.get("export_format")
        )
    
    @classmethod
    def name(cls) -> str:
        return "export_document"


@WordWinCOMReceiver.register
class GetDocumentInfoCommand(WinCOMCommand):
    """Command to get document info."""
    
    def execute(self):
        return self.receiver.get_document_info()
    
    @classmethod
    def name(cls) -> str:
        return "get_document_info"


@WordWinCOMReceiver.register
class GetWordCountCommand(WinCOMCommand):
    """Command to get word count."""
    
    def execute(self):
        return self.receiver.get_word_count()
    
    @classmethod
    def name(cls) -> str:
        return "get_word_count"


@WordWinCOMReceiver.register
class SpellCheckCommand(WinCOMCommand):
    """Command to run spell check."""
    
    def execute(self):
        return self.receiver.spell_check()
    
    @classmethod
    def name(cls) -> str:
        return "spell_check"


@WordWinCOMReceiver.register
class SaveDocumentCommand(WinCOMCommand):
    """Command to save document."""
    
    def execute(self):
        return self.receiver.save_document(
            file_path=self.params.get("file_path"),
            format=self.params.get("format", "docx")
        )
    
    @classmethod
    def name(cls) -> str:
        return "save_document"
