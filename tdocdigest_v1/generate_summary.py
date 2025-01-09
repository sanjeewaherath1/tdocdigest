"""
This file handles summary generation for the TDoc Digest
"""
import logging
import requests
import zipfile
import io
import os
from openai import OpenAI
import docx2txt


def download_and_extract_tdoc(meetingid, tdocnumber, workingfolder):
    """
    Downloads the specified tdoc and extracts it into the specified workingfolder
    From the meeting id and tdocnumber, the url for downloading the tdoc is created
    The zip file may contain more than one file. Search through all extracted files to locate the tdoc
    :param meetingid (str): the meeting id of the tdoc
    :param tdocnumber (str): the tdoc number
    :param workingfolder (str): the folder where the tdoc will be extracted
    :return tdocfile (str): the extracted tdoc file name and empty string if no tdoc file was found
    :return err (str): error string (if any) otherwise an empty string
    """

    logging.debug(f'Download & extract: meeting#{meetingid},TDoc#{tdocnumber},working folder:{workingfolder}')

    # The url for the zip file in 3GPP site
    url_tdoc_zip_file = "https://www.3gpp.org/ftp/TSG_RAN/WG1_RL1/TSGR1_" + meetingid + "/Docs/" + tdocnumber + ".zip"

    err = ''

    try:
        # Send a GET request to the URL
        response = requests.get(url_tdoc_zip_file)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Create a ZipFile object from the content
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Extract all contents
            zip_ref.extractall(workingfolder)
            # Get the list of files in the ZIP
            files = zip_ref.namelist()

        # check if the provided tdoc number is a contribution or not
        # There are documents in the folder which are not TDoc.
        # They may be agreements, wayforwards etc
        # 3GPP TDoc name starts the docx file name with the tdoc number
        logging.debug(f'processing files {files}')
        tdocfile = ''
        for filename in files:
            if filename.lower().startswith((tdocnumber.lower())):

                logging.debug(f'Found a file name begins with tdoc number: {filename}')

                if filename.lower().endswith(('.docx')):
                    tdocfile = filename
                    err = ''
                    logging.debug(f'File found is a docx file: {tdocfile}')
                    break
                else:
                    logging.info(f'Not Found: {filename.lower()}, {tdocnumber.lower()}')
                    err = "File must be a Word document (.docx) format"

        # After iterating through all files, a docx file starting with tdoc number is not found
        if tdocfile == '':
            logging.warning(
                f'After iterating through all files, a docx file starting with tdoc number is not found: {filename.lower()}, {tdocnumber.lower()}')
            if err == '':
                err = f"After iterating through all files, a docx file starting with tdoc number is not found"
                logging.error(err)

        # return the file name
        return tdocfile, err

    except requests.exceptions.RequestException as e:
        err = f"Check if the meeting id and tdoc number are correct. Attempting to download the file: {e}"
        logging.error(err)
    except zipfile.BadZipFile:
        err = f"The file is not a zip file or is corrupted."
        logging.error(err)
    except Exception as e:
        err = f"An unexpected error occurred: {e}"
        logging.error(err)

    return [], err


def get_tdoc_content(filepath, userkey, callapi):
    """
    Generate text summary. If callapi is
    :param filepath (str): The full path to the file where input text is
    :param userkey (str): key to call gpt-4o API (prompt)
    :param callapi (bool): Whether to call the gpt-4o API (prompt) or not
    :return summary_generated (str): the summary generated from gpt-4o API
    :return inputtext (str): the text of the file
    :return err (str): any errors during the processing
    """
    if not filepath.lower().endswith(('.docx')):
        summary_generated = ''
        inputtext = ''
        err = "File must be a Word document (.docx) format"
        logging.error(err)
        return summary_generated, inputtext, err

    try:
        # Extract text from the specified file
        inputtext = docx2txt.process(filepath)
        err = ''
        logging.debug('Text extracted successfully')

        summary_generated, err = generate_text_summary(userkey, inputtext, callapi=callapi)
        logging.debug(f'Text summary generated successfully, APIcall:{callapi}')

        return summary_generated, inputtext, err

    except Exception as e:
        summary_generated = ''
        inputtext = ''
        err = Exception(f"Error in extracting text from tdoc {str(e)}")
        logging.error(err)
        return summary_generated, inputtext, err


# Generate the summary from AI model
def generate_text_summary(userkey, inputtext, callapi=False):
    """
    Generate text summary from input text.
    :param userkey (str): key to call gpt-4o API (prompt)
    :param inputtext (str): the text of the file (long original text)
    :param callapi (bool): Whether to call the gpt-4o API (prompt) or not:
    :return summary(str): The summary generated from gpt-4o API (prompt)
                          or first 2000 characters (for debugging purposes)
    :return err(str): any errors during the processing
    """

    # Generate a summary (return the first characters if callapi is False)
    if not callapi:
        summary = inputtext[0:2000]
        err = ''
        logging.debug(f'Text summary generation first characters APIcall:{callapi}')
    # Generate the summary from AI model (LLM)
    else:
        summary, err = generate_openai_summary(userkey, inputtext, temperature=0.1, model='gpt-4')
        logging.debug(f'Text summary generation openai APIcall:{callapi}')

    return summary, err


def generate_openai_summary(openAIkeyforUser, inputtext, temperature, model):
    """
    Generate text summary from input text using the gpt-4o API.
    :param openAIkeyforUser (str): key to call gpt-4o API (prompt)
    :param inputtext (str): the text of the file (long original text)
    :param temperature (float): the temperature of the gpt-4o API
    :param model (str): the gpt-4o model to generate summary from
    :return: summary(str): The summary generated from gpt-4o API (prompt)
    :return err(str): any errors during the processing
    """
    err = ''
    summarygenerated = ''

    logging.info(f"Open AI API {model}, {temperature}")

    # Get open AI key for the session
    openAIkeyforUser = os.getenv("OPENAI_API_KEY")

    # Generate summary using lower temperature, specific prompt and gpt-4o
    client = OpenAI(api_key=openAIkeyforUser)

    try:
        # Attempt to create a chat completion
        response_openai = client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": "You are acting as a 3GPP Standard Delegate specializing in the RAN (Radio Access "
                            "Network) Working Group 1 (WG1) for 5G/6G standardization. Generate a summary report from "
                            "the text using terms common in 3GPP."},
                {"role": "assistant",
                 "content": "Title of the summary is 'Document summary: Document title, document number. Include the "
                            "document title, meeting number, agenda item, document number, title, source, "
                            "document for, location information at the top of the summary. Some documents list "
                            "observations as items, for example, 'observation 1', 'observation 2' etc. If such "
                            "observations exists in the document, include such observations in the summary. If "
                            "explanations or reasons for such observation is described in the document, "
                            "provide a brief summary."},
                {"role": "system",
                 "content": "Some documents list proposals as items for example, 'proposal 1', 'proposal 2' etc. If "
                            "such proposals exists in the document, include such proposals in the summary."},
                {"role": "assistant",
                 "content": "An explanation for the proposal is usually provided. Include such explanation in the "
                            "summary."},
                {"role": "system",
                 "content": "Some documents list observations as items, for example, 'observation 1', 'observation 2' "
                            "etc. If such observations exists in the document, include such observations in the "
                            "summary."},
                {"role": "user", "content": inputtext}
            ],
            model=model,
            temperature=temperature,
        )

        # Retrieve and print the response if successful
        logging.info("OpenAI API call was successful.")

        # Extract the response content
        summarygenerated = response_openai.choices[0].message.content
        return summarygenerated, err

    except Exception as e:
        err = str(e)
        logging.error(f"OpenAI API returned an error: {err}")
        if "authentication" in err.lower():
            err = f"Authentication failed. Check your API key. {err}"
            logging.error(err)
        if "rate limit" in err.lower():
            err = f"Rate limit exceeded. Try again later. {err}"
            logging.error(err)
        if "invalid" in err.lower():
            err = f"The request was invalid. Check your parameters. {err}"
            logging.error(err)
        else:
            err = f"An unexpected OpenAI error occurred.{err}"
            logging.error(err)

        return summarygenerated, err
