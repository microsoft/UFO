#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
PDF Reader MCP Server
Provides MCP server for PDF text extraction operations.
"""

import platform
import sys

# Platform check - this module requires Windows (uses PyPDF2 which is Windows-only)
if platform.system() != "Windows":
    import logging

    logging.warning(
        f"pdf_reader_mcp_server.py requires Windows platform. Current: {platform.system()}. Skipping module initialization."
    )
    # Exit module loading gracefully
    sys.exit(0)

import os
import subprocess
import time
import random
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import PyPDF2
from fastmcp import FastMCP
from fastmcp.client import Client
from pydantic import Field

from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.config import get_config

# Get config
configs = get_config()


@MCPRegistry.register_factory_decorator("PDFReaderExecutor")
def create_pdf_reader_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the PDF Reader MCP server instance.
    :return: FastMCP instance for PDF operations.
    """

    def _extract_text_from_pdf(pdf_path: str, simulate_human: bool = True) -> str:
        """
        Extract text content from a single PDF file with optional human simulation.
        :param pdf_path: Path to the PDF file.
        :param simulate_human: Whether to simulate human-like behavior (open, wait, close).
        :return: Extracted text content.
        """
        pdf_process = None
        try:
            if simulate_human:
                # 模拟人工操作：打开PDF文件
                print(f"🔍 Opening PDF file: {os.path.basename(pdf_path)}")
                try:
                    # 尝试用默认程序打开PDF（通常是Adobe Reader或浏览器）
                    pdf_process = subprocess.Popen(["start", "", pdf_path], shell=True)

                    # 模拟人工查看时间：随机等待2-5秒
                    wait_time = random.uniform(2.0, 5.0)
                    print(
                        f"👁️  Simulating human reading... waiting {wait_time:.1f} seconds"
                    )
                    time.sleep(wait_time)

                except Exception as e:
                    print(f"⚠️  Could not open PDF with default application: {e}")
                    print("📄 Proceeding with text extraction...")

            # 提取文本内容
            print(f"📝 Extracting text from: {os.path.basename(pdf_path)}")
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n"
                    text_content += page_text

                    if simulate_human and len(pdf_reader.pages) > 1:
                        # 模拟人工翻页等待时间
                        page_wait = random.uniform(0.5, 1.5)
                        print(
                            f"📖 Processing page {page_num + 1}... waiting {page_wait:.1f}s"
                        )
                        time.sleep(page_wait)

            if simulate_human:
                print(f"✅ Text extraction completed for: {os.path.basename(pdf_path)}")

            return text_content.strip()

        except Exception as e:
            return f"Error reading PDF {pdf_path}: {str(e)}"
        finally:
            if simulate_human and pdf_process:
                try:

                    print(f"🔒 Closing PDF file: {os.path.basename(pdf_path)}")

                    time.sleep(0.5)
                    print(f"📄 PDF closed: {os.path.basename(pdf_path)}")

                except Exception as e:
                    print(f"⚠️  Could not close PDF application: {e}")

    def _extract_text_from_pdf_batch(
        pdf_paths: List[str], simulate_human: bool = True
    ) -> Dict[str, str]:
        """
        Extract text from multiple PDF files with human simulation.
        :param pdf_paths: List of PDF file paths.
        :param simulate_human: Whether to simulate human-like behavior.
        :return: Dictionary mapping filenames to extracted text.
        """
        results = {}
        total_files = len(pdf_paths)

        if simulate_human:
            print(f"📚 Starting batch processing of {total_files} PDF files...")
            print("🤖 Simulating human-like document review process...")

        for i, pdf_path in enumerate(pdf_paths, 1):
            file_name = os.path.basename(pdf_path)

            if simulate_human:
                print(f"\n📂 Processing file {i}/{total_files}: {file_name}")

                # 模拟人工在文件间的停顿
                if i > 1:
                    between_files_wait = random.uniform(1.0, 3.0)
                    print(
                        f"⏳ Taking a brief break between files... {between_files_wait:.1f}s"
                    )
                    time.sleep(between_files_wait)

            text_content = _extract_text_from_pdf(pdf_path, simulate_human)
            results[file_name] = text_content

            if simulate_human:
                print(f"✅ Completed: {file_name}")

        if simulate_human:
            print(f"\n🎉 Batch processing completed! Processed {total_files} files.")

        return results

    def _get_pdf_files_in_directory(directory_path: str) -> List[str]:
        """
        Get all PDF files in the specified directory.
        :param directory_path: Path to the directory.
        :return: List of PDF file paths.
        """
        try:
            pdf_files = []
            directory = Path(directory_path)

            if not directory.exists():
                return []

            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == ".pdf":
                    pdf_files.append(str(file_path))

            return sorted(pdf_files)
        except Exception as e:
            print(f"Error scanning directory {directory_path}: {str(e)}")
            return []

    mcp = FastMCP("UFO PDF Reader MCP Server")

    @mcp.tool(tags={"PDF"})
    def extract_pdf_text(
        pdf_path: Annotated[
            str,
            Field(description="The full path to the PDF file to extract text from."),
        ],
        simulate_human: Annotated[
            bool,
            Field(
                description="Whether to simulate human-like behavior (opening, reading, closing PDF). Default: True"
            ),
        ] = True,
    ) -> Annotated[
        str,
        Field(description="The extracted text content from the PDF file."),
    ]:
        """
        Extract text content from a single PDF file with optional human simulation.
        When simulate_human is True, the process will:
        1. Open the PDF file with default application
        2. Wait for a realistic reading time (2-5 seconds)
        3. Extract text with page-by-page delays
        4. Close the PDF file
        This simulates a human manually reviewing the document.
        """
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at {pdf_path}"

        if not pdf_path.lower().endswith(".pdf"):
            return f"Error: File {pdf_path} is not a PDF file"

        return _extract_text_from_pdf(pdf_path, simulate_human)

    @mcp.tool(tags={"PDF"})
    def list_pdfs_in_directory(
        directory_path: Annotated[
            str,
            Field(description="The directory path to scan for PDF files."),
        ],
    ) -> Annotated[
        List[str],
        Field(description="A list of PDF file paths found in the directory."),
    ]:
        """
        List all PDF files in the specified directory.
        Returns a list of full paths to PDF files found in the directory.
        """
        if not os.path.exists(directory_path):
            return []

        if not os.path.isdir(directory_path):
            return []

        return _get_pdf_files_in_directory(directory_path)

    @mcp.tool(tags={"PDF"})
    def extract_all_pdfs_text(
        directory_path: Annotated[
            str,
            Field(
                description="The directory path containing PDF files to extract text from."
            ),
        ],
        simulate_human: Annotated[
            bool,
            Field(
                description="Whether to simulate human-like behavior for each PDF. Default: True"
            ),
        ] = True,
    ) -> Annotated[
        Dict[str, str],
        Field(
            description="A dictionary mapping PDF file paths to their extracted text content."
        ),
    ]:
        """
        Extract text content from all PDF files in the specified directory with human simulation.
        When simulate_human is True, the process will simulate a human reviewing each document:
        - Opening each PDF file
        - Taking realistic reading time
        - Taking breaks between files
        - Closing each PDF file
        Returns a dictionary where keys are PDF file paths and values are the extracted text content.
        """
        if not os.path.exists(directory_path):
            return {"error": f"Directory not found: {directory_path}"}

        if not os.path.isdir(directory_path):
            return {"error": f"Path is not a directory: {directory_path}"}

        pdf_files = _get_pdf_files_in_directory(directory_path)

        if not pdf_files:
            return {"message": f"No PDF files found in directory: {directory_path}"}

        # 使用新的批处理函数
        return _extract_text_from_pdf_batch(pdf_files, simulate_human)

    return mcp


async def main():
    """
    Main function to run the PDF Reader MCP server and test with the specified directory.
    """
    mcp_server = create_pdf_reader_mcp_server()

    async with Client(mcp_server) as client:
        print("Starting PDF Reader MCP server...")
        tool_list = await client.list_tools()
        for tool in tool_list:
            print(f"Available tool: {tool.name} - {tool.description}")

        # Test directory path - using current directory for testing
        test_directory = r""

        # Fallback to test_pdfs directory if the original doesn't exist
        if not os.path.exists(test_directory):
            current_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            test_directory = os.path.join(current_dir, "test_pdfs")
            if not os.path.exists(test_directory):
                test_directory = os.path.abspath("test_pdfs")
            print(
                f"⚠️  Original directory not accessible, using test directory: {test_directory}"
            )

        print(f"\n🔍 Testing with directory: {test_directory}")

        # Test 1: List PDF files in the directory
        print("\n1. Listing PDF files in directory...")
        result = await client.call_tool(
            "list_pdfs_in_directory", arguments={"directory_path": test_directory}
        )
        print(f"Found PDF files: {result.data}")

        # Test 2: Extract text from all PDFs in the directory
        print("\n2. Extracting text from all PDF files...")
        result = await client.call_tool(
            "extract_all_pdfs_text", arguments={"directory_path": test_directory}
        )

        if isinstance(result.data, dict):
            print(f"Successfully extracted text from {len(result.data)} files:")
            for filename, content in result.data.items():
                content_preview = (
                    content[:200] + "..." if len(content) > 200 else content
                )
                print(f"  📄 {filename}: {content_preview}")
        else:
            print(f"Result: {result.data}")

        # Test 3: Extract text from a single PDF (if any exists)
        pdf_files = await client.call_tool(
            "list_pdfs_in_directory", arguments={"directory_path": test_directory}
        )

        if pdf_files.data and len(pdf_files.data) > 0:
            first_pdf = pdf_files.data[0]
            print(
                f"\n3. Extracting text from single PDF: {os.path.basename(first_pdf)}"
            )
            result = await client.call_tool(
                "extract_pdf_text", arguments={"pdf_path": first_pdf}
            )
            content_preview = (
                result.data[:300] + "..." if len(result.data) > 300 else result.data
            )
            print(f"Text content preview: {content_preview}")


if __name__ == "__main__":
    import asyncio

    # Run the main function in the event loop
    asyncio.run(main())
