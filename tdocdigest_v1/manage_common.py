"""
This file handles common functions for the TDoc Digest
"""
import os


def get_file_path(folder, filename):
    """
    Returns the full file path by combining the folder and filename.

    Args:
    folder (str): The path to the folder.
    filename (str): The name of the file.

    Returns:
    str: The full path to the file.
    """
    return os.path.join(folder, filename)
