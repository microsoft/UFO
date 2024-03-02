# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os

def find_files_with_extension(directory, extension):
    """
    Find files with the given extension in the given directory.
    :param directory: The directory to search.
    :param extension: The extension to search for.
    :return: The list of matching files.
    """
    matching_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matching_files.append(os.path.join(root, file))
    
    return matching_files



def find_files_with_extension_list(directory, extensions):
    """
    Find files with the given extensions in the given directory.
    :param directory: The directory to search.
    :param extensions: The list of extensions to search for.
    :return: The list of matching files.
    """
    matching_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(tuple(extensions)):
                matching_files.append(os.path.join(root, file))
    
    return matching_files

