"""
This file handles user authentication
"""
import os
import logging


# Get the user authenticated and return the respective key for the API
def authenticate_user():
    """
    Retrieve the openai API key from the environment
    :return userkey (str): openai api key
    :return err (str): error message (if API key is not set)
    """
    err = ''
    userkey = os.getenv("OPENAI_API_KEY")
    # Check if the API key is not found
    if not userkey:
        err = f"Error: OPENAI_API_KEY environment variable is not set."
        logging.error(err)
    else:
        logging.info("OPENAI_API_KEY successfully retrieved.")

    # return the API key and error
    return userkey, err
