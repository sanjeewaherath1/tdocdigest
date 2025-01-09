"""
This file handles data files for the TDoc Digest
"""
import os
import logging
from datetime import datetime
from manage_common import get_file_path
import pickle


def create_data_folder():
    """
    Creates a folder for data file saving
    :return data_folder (str): data folder name
    """
    # log folder path
    data_folder = './digestdata'
    try:
        os.makedirs(data_folder, exist_ok=True)
    except OSError as e:
        # Raise the error/exception
        raise e

    return data_folder


def create_data_file(datafolder, meetingid, tdocnumber, timestamp):
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

    datafilename = 'data_' + meetingid + '_' + tdocnumber + '_' + timestamp + '.pkl'
    datafilenamefull = get_file_path(datafolder, datafilename)

    # Log a message to confirm
    logging.debug(f"Data file created {datafilenamefull}")
    # Return the log file path for later use
    return datafilenamefull


def dump_data(data_filename, session, identifier):
    try:
        logging.info(f"Dump data in pickle file {identifier}: {data_filename}")
        with open(data_filename, "wb") as file:
            # Filter only non-Streamlit session keys
            session_data = {key: session[key] for key in session if not key.startswith("_")}
            pickle.dump(session_data, file)
            # pickle.dump(dict(session), file)

    except pickle.PicklingError as e:
        logging.info(f"Error serializing session {identifier}: {e}")
        for key, value in session.items():
            try:
                pickle.dumps(value)
            except pickle.PicklingError:
                logging.info(f"Key '{key}' contains non-serializable value: {value}")

