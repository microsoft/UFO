import shutil
import datetime
import os

def copy_file(source_file_path,destination_file_path=None):
    """
    Copy a file from one location to another.
    :param source_file_path: The full path to the file you want to copy.
    :param destination_file_path: The full path to the location where you want to copy the file.
    """
    if not destination_file_path:
        destination_file_path = source_file_path + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    
    copy_file_path = destination_file_path

    try:
        shutil.copy(source_file_path, destination_file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        copy_file_path = None

    return copy_file_path


def delete_file(file_path):
    """
    Delete a file from the file system.
    :param file_path: The full path to the file you want to delete.
    """
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True