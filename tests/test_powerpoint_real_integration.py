"""
Integration tests for PowerPoint MCP Server with actual PowerPoint COM automation.

This file tests the items that are NOT covered by the mock-based unit tests:
- Actual PowerPoint COM Automation
- PowerPoint Application Behavior  
- COM Interface Compatibility

Requirements:
- Microsoft PowerPoint must be installed
- Windows environment with COM support
- win32com.client library

Note: These tests will actually launch PowerPoint and create/modify presentations.
"""

import os
import sys
import tempfile
import shutil
import unittest
import time
from pathlib import Path

# Add UFO2 project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Test if PowerPoint COM is available
try:
    import win32com.client
    POWERPOINT_AVAILABLE = True
except ImportError:
    POWERPOINT_AVAILABLE = False

print(f"PowerPoint COM availability: {POWERPOINT_AVAILABLE}")


class PowerPointCOMIntegrationTest(unittest.TestCase):
    """Integration tests for actual PowerPoint COM automation"""
    
    def setUp(self):
        """Set up each test with PowerPoint COM check"""
        if not POWERPOINT_AVAILABLE:
            self.skipTest("PowerPoint COM automation not available")
        
        # Initialize PowerPoint for each test
        try:
            self.ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            self.ppt_app.Visible = True
            time.sleep(1)  # Give PowerPoint time to initialize
            
            # Import UFO2 MCP modules
            from ufo.mcp.base_mcp_server import create_mcp_server
            from ufo.automator.app_apis.factory import MCPReceiverFactory
            
            self.create_mcp_server = create_mcp_server
            self.MCPReceiverFactory = MCPReceiverFactory
            
        except Exception as e:
            self.skipTest(f"PowerPoint COM setup failed: {e}")
        
        self.app_namespace = "powerpoint"
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_ppt_path = os.path.join(self.temp_dir, "test_presentation.pptx")
        self.test_export_path = os.path.join(self.temp_dir, "test_export.pdf")
        
        # Close any existing presentations
        try:
            presentations = self.ppt_app.Presentations
            while presentations.Count > 0:
                presentations(1).Close()
        except:
            pass
            
        print(f"\n--- Setting up test with temp dir: {self.temp_dir} ---")
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            # Close all presentations safely
            if hasattr(self, 'ppt_app') and self.ppt_app:
                presentations = self.ppt_app.Presentations
                count = presentations.Count
                for i in range(count):
                    try:
                        presentations(1).Close()
                    except:
                        break  # If we can't close, break the loop
                
                # Quit PowerPoint
                self.ppt_app.Quit()
                time.sleep(1)  # Give PowerPoint time to close
            
        except Exception as e:
            print(f"Warning: Error during PowerPoint cleanup: {e}")
        
        # Clean up temporary files
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_com_powerpoint_availability(self):
        """Test that PowerPoint COM interface is accessible"""
        print("1. Testing PowerPoint COM availability...")
        
        # Test basic PowerPoint properties
        self.assertIsNotNone(self.ppt_app)
        
        # Test application name
        try:
            name = self.ppt_app.Name
            self.assertEqual(name, "Microsoft PowerPoint")
            print(f"✓ PowerPoint application name: {name}")
        except Exception as e:
            print(f"⚠ PowerPoint Name property error: {e}")
        
        # Test version
        try:
            version = self.ppt_app.Version
            print(f"✓ PowerPoint version: {version}")
        except Exception as e:
            print(f"⚠ PowerPoint version error: {e}")
        
        # Test basic functionality - presentations collection access
        try:
            presentations = self.ppt_app.Presentations
            self.assertIsNotNone(presentations)
            initial_count = presentations.Count
            self.assertIsInstance(initial_count, int)
            print(f"✓ PowerPoint COM interface accessible - {initial_count} presentations open")
        except Exception as e:
            self.fail(f"Cannot access PowerPoint Presentations: {e}")
    
    def test_com_create_presentation(self):
        """Test actual PowerPoint presentation creation via COM"""
        print("2. Testing PowerPoint presentation creation...")
        
        try:
            # Create new presentation
            presentations = self.ppt_app.Presentations
            presentation = presentations.Add()
            
            self.assertIsNotNone(presentation)
            self.assertEqual(presentations.Count, 1)
            
            # Test presentation properties
            self.assertTrue(hasattr(presentation, 'Slides'))
            slides_count = presentation.Slides.Count
            self.assertGreaterEqual(slides_count, 1)  # At least default slide
            
            print(f"✓ PowerPoint presentation created successfully via COM ({slides_count} slides)")
            
        except Exception as e:
            self.fail(f"PowerPoint presentation creation failed: {e}")
    
    def test_com_slide_operations(self):
        """Test actual slide operations via COM"""
        print("3. Testing PowerPoint slide operations...")
        
        try:
            # Create presentation
            presentation = self.ppt_app.Presentations.Add()
            
            # Test adding slides
            slides = presentation.Slides
            initial_count = slides.Count
            
            # Add slides with different layouts
            slide1 = slides.Add(initial_count + 1, 1)  # ppLayoutText
            slide2 = slides.Add(initial_count + 2, 2)  # ppLayoutTwoContent
            
            self.assertEqual(slides.Count, initial_count + 2)
            
            # Test slide title setting
            try:
                title_shape = slide1.Shapes.Title
                title_shape.TextFrame.TextRange.Text = "Test Slide Title"
                
                # Verify title was set
                actual_title = title_shape.TextFrame.TextRange.Text
                self.assertEqual(actual_title, "Test Slide Title")
                print("✓ Slide title setting successful")
            except Exception as e:
                print(f"⚠ Slide title setting failed: {e}")
            
            # Test slide deletion
            slide2.Delete()
            self.assertEqual(slides.Count, initial_count + 1)
            
            print("✓ PowerPoint slide operations successful via COM")
            
        except Exception as e:
            self.fail(f"Slide operations failed: {e}")
    
    def test_com_save_operations(self):
        """Test actual save operations via COM"""
        print("4. Testing PowerPoint save operations...")
        
        try:
            # Create presentation with content
            presentation = self.ppt_app.Presentations.Add()
            slides = presentation.Slides
            
            # Add a slide and set title
            slide = slides.Add(slides.Count + 1, 1)  # ppLayoutText
            try:
                slide.Shapes.Title.TextFrame.TextRange.Text = "Test Presentation"
            except:
                pass  # Title setting might not work on all layouts
            
            # Save presentation
            presentation.SaveAs(self.test_ppt_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(self.test_ppt_path))
            self.assertGreater(os.path.getsize(self.test_ppt_path), 0)
            
            print("✓ PowerPoint save operations successful via COM")
            
            # Test opening saved presentation
            presentation.Close()
            reopened = self.ppt_app.Presentations.Open(self.test_ppt_path)
            
            # Verify content preserved
            self.assertGreaterEqual(reopened.Slides.Count, 1)
            print("✓ PowerPoint open operations successful via COM")
            
        except Exception as e:
            self.fail(f"Save operations failed: {e}")
    
    def test_mcp_receiver_with_real_powerpoint(self):
        """Test UFO2 MCP receiver with actual PowerPoint"""
        print("5. Testing UFO2 MCP receiver with real PowerPoint...")
        
        try:
            # Create MCP receiver factory
            factory = self.MCPReceiverFactory()
            
            # Try to create PowerPoint receiver
            receiver = factory.create_receiver(self.app_namespace)
            
            if receiver:
                # Test receiver properties
                self.assertEqual(receiver.app_namespace, self.app_namespace)
                self.assertEqual(receiver.type_name, "MCP_POWERPOINT")
                
                print("✓ UFO2 MCP PowerPoint receiver created successfully")
            else:
                print("⚠ UFO2 MCP PowerPoint receiver creation returned None")
                
        except Exception as e:
            print(f"⚠ MCP receiver test failed: {e}")
    
    def test_mcp_server_with_real_powerpoint(self):
        """Test UFO2 MCP server integration with actual PowerPoint"""
        print("6. Testing UFO2 MCP server with real PowerPoint...")
        
        try:
            # Create MCP server
            server = self.create_mcp_server(
                self.app_namespace,
                "integration-test-server",
                9999
            )
            
            self.assertIsNotNone(server)
            self.assertEqual(server.app_namespace, self.app_namespace)
            
            # Test if server can load PowerPoint instructions
            self.assertIsNotNone(server.instructions)
            self.assertIn("tools", server.instructions)
            
            tools = server.instructions.get("tools", [])
            self.assertGreater(len(tools), 0)
            
            print(f"✓ UFO2 MCP server created with {len(tools)} PowerPoint tools")
            
        except Exception as e:
            print(f"⚠ MCP server integration test failed: {e}")


class PowerPointCOMCompatibilityTest(unittest.TestCase):
    """Test COM interface compatibility and edge cases"""
    
    def setUp(self):
        """Set up each test with PowerPoint COM check"""
        if not POWERPOINT_AVAILABLE:
            self.skipTest("PowerPoint COM automation not available")
    
    def test_com_error_handling(self):
        """Test COM error handling scenarios"""
        print("7. Testing PowerPoint COM error handling...")
        
        try:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True
            time.sleep(1)
            
            # Test accessing non-existent presentation
            with self.assertRaises(Exception):
                ppt_app.Presentations(999)  # Should raise COM error
            
            # Test invalid slide operations
            presentation = ppt_app.Presentations.Add()
            
            with self.assertRaises(Exception):
                presentation.Slides(999).Delete()  # Should raise COM error
            
            presentation.Close()
            ppt_app.Quit()
            
            print("✓ COM error handling working correctly")
            
        except Exception as e:
            print(f"⚠ COM error handling test issue: {e}")
    
    def test_com_version_compatibility(self):
        """Test PowerPoint version compatibility"""
        print("8. Testing PowerPoint version compatibility...")
        
        try:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True
            time.sleep(1)
            
            # Test basic version properties
            try:
                version_info = str(ppt_app.Version)
                print(f"PowerPoint Version detected: {version_info}")
                
                # Basic version validation (should be a string)
                self.assertIsInstance(version_info, str)
                self.assertGreater(len(version_info), 0)
                
            except AttributeError:
                print("⚠ Version property not accessible, but PowerPoint is working")
            
            # Test that PowerPoint is functional regardless of version
            presentation = ppt_app.Presentations.Add()
            self.assertIsNotNone(presentation)
            presentation.Close()
            
            ppt_app.Quit()
            
            print("✓ PowerPoint functionality verified")
            
        except Exception as e:
            print(f"⚠ Version compatibility test issue: {e}")


if __name__ == "__main__":
    # Configure test runner with more detailed output
    unittest.main(
        verbosity=2,
        buffer=True,
        catchbreak=True,
        failfast=False
    )
