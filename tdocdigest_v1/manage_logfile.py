"""
This file handles log files for the TDoc Digest
"""
import os
import logging
from datetime import datetime
from manage_common import get_file_path


def create_log_folder(meeting_id):
    """
    Creates a folder for log file saving using the specified meeting_id
    :param meeting_id (str):
    :return log_folder (str): log folder name
    """
    # log folder path
    log_folder = './log_' + meeting_id
    try:
        os.makedirs(log_folder, exist_ok=True)
    except OSError as e:
        # Raise the error/exception
        raise e

    return log_folder


def create_log_file(meetingid, tdocnumber, workingfolder):
    """
    Creates a log file in the folder specified by workingfolder
    log file format is log_<meetingid>_<tdocnumber>_<timestamp>.log>
    Example: log_118_R1-2405963_20241112_094854.log
    :param meetingid (str): meeting id
    :param tdocnumber (str): tdoc number
    :param workingfolder (str): working folder
    :return logfilenamefull (str): log file full path
    """
    # String used for the log file name based on time
    time_stamp_format = '%Y%m%d_%H%M%S'
    file_time_stamp = datetime.now().strftime(time_stamp_format)

    logfilename = 'log_' + meetingid + '_' + tdocnumber + '_' + file_time_stamp + '.log'
    logfilenamefull = get_file_path(workingfolder, logfilename)

    # Configure the log file
    logging.basicConfig(filename=logfilenamefull,  # Log file name
                        level=logging.DEBUG,  # Log level
                        format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
                        force=True
                        )
    # Log a message to confirm
    logging.debug(f"Log file created {logfilenamefull}")
    # Return the log file path for later use
    return logfilenamefull, file_time_stamp
