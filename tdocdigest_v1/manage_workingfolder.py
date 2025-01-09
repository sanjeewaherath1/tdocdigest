import os
import logging
import shutil
from manage_common import get_file_path

"""
This file handles working folder for the TDoc Digest
"""

def create_working_folder(meeting_id):
    """
    Creates a folder using the specified meeting_id
    :param meeting_id (str): meeting id
    :return (str): folder path
    """
    # Create working_folder folder
    working_folder = './download_' + meeting_id
    try:
        os.makedirs(working_folder, exist_ok=True)
    except OSError as e:
        # Raise the error/exception
        raise e

    return working_folder


def delete_working_folder(folderpath):
    """
    Deletes the specified folder
    :param folderpath (str): folder path to be deleted
    :return: None
    """
    try:
        # Check if the folder exists
        if os.path.exists(folderpath):
            try:
                shutil.rmtree(folderpath)
                logging.info(f"Folder '{folderpath}' and all its contents have been deleted.")
            except OSError as e:
                logging.error(f"Error deleting the folder {folderpath} : {e}")
        else:
            logging.info(f"Folder '{folderpath}' does not exist.")
    except Exception as e:
        logging.error(f"Error in handling the folder {folderpath} : {e}")

