# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import win32com.client as win32
import time

from ael.config.config import Config
configs = Config.get_instance().config_data

BACKEND = configs["CONTROL_BACKEND"]

class AppControl:
    def __init__(self,app_root_name) -> None:
        self.file_instance = None
        self.app_root_name = app_root_name
        # Start the specified application
        self.app_instance = win32.gencache.EnsureDispatch(self.app_root_name)
        self.app_window = None
        self.file_path = None
        
    def quit(self):
        """
        Quit the application.
        """
        # close all dialog
        try:
            # close_word_dialogs()
            if self.file_instance:
                self.file_instance.Close()
                self.file_instance = None
            self.file_path = None
        except Exception as e:
            print("Error while closing dialogs:", e)
        finally:
            self.app_instance.Quit()
            self.app_instance = None
            time.sleep(configs["SLEEP_TIME"])
    
 
    def open_file_with_app(self,file_path):
        """
        This function attempts to open a file using a specified application.
        
        :param file_path: The full path to the file you want to open.
        :param app_name: The ProgID of the application you want to use to open the file.
        """
        self.app_instance = win32.gencache.EnsureDispatch(self.app_root_name)
        time.sleep(configs["SLEEP_TIME"])
        self.file_path = file_path

        try:

            # Make the application visible
            self.app_instance.Visible = True  

            # Close all previously opened documents if supported
            if hasattr(self.app_instance, 'Documents'):
                for doc in self.app_instance.Documents:
                    doc.Close(False)  # Argument False indicates not to save changes
            
            # Different applications have different methods for opening files
            if self.app_root_name == 'Word.Application':
                self.file_instance = self.app_instance.Documents.Open(file_path)
                self.app_instance.WindowState = win32.constants.wdWindowStateMaximize
            elif self.app_root_name == 'Excel.Application':
                self.file_instance = self.app_instance.Workbooks.Open(file_path)
            # Add more cases here for different applications
            else:
                print(f"Application '{self.app_root_name}' is not supported by this function.")
                self.quit(save=False)

        except Exception as e:
            print(f"An error occurred: {e}")