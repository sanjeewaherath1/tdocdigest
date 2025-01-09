# Import the packages needed
import streamlit as st
import logging

from manage_logfile import create_log_folder, create_log_file
from handle_datafiles import create_data_file, create_data_folder, dump_data
from manage_workingfolder import create_working_folder, delete_working_folder
from manage_common import get_file_path
from calculate_scores import calculate_semantic_score
from generate_summary import get_tdoc_content, download_and_extract_tdoc
from user_authentication import authenticate_user

st.header('**TDocDigest V3.0**')

# Initialize session state for storing inputs
if "step" not in st.session_state:
    st.session_state['step'] = 1  # Step 1: Input tdoc_number and meeting id
    st.session_state['tdoc_number'] = ''
    st.session_state['meeting_id'] = ''
    st.session_state['tdoc_summary_txt'] = ''
    st.session_state['error'] = ''
    st.session_state['score'] = ''
    st.session_state['log_path'] = ''


def check_input_format(tdoc_number):
    # Check for errors in the user input
    error_tdoc = ''
    if tdoc_number.strip().startswith('R1-'):
        tdoc_number = tdoc_number.strip()
        logging.info(f"Processing request {tdoc_number}")
    elif tdoc_number.strip().lower().startswith('r1-'):
        tdoc_number = tdoc_number.strip().replace('r1-', 'R1-')
        logging.info(f"Processing request {tdoc_number}")
    else:
        tdoc_number = tdoc_number
        error_tdoc = 'Wrong input TDoc number:' + tdoc_number + '. RAN1 TDoc has the format R1-<Numeric>.'
        logging.error(error_tdoc)

    return tdoc_number, error_tdoc


def handle_summary_form_submit():
    meetingid = st.session_state.get("first_meeting_id", "").strip()
    tdocnumber = st.session_state.get("first_tdoc_number", "").strip()

    if not meetingid:
        st.warning("Meeting ID cannot be empty.")
        return
    if not tdocnumber:
        st.warning("TDoc Number cannot be empty.")
        return

    st.session_state["meeting_id"] = meetingid
    st.session_state["tdoc_number"] = tdocnumber

    # Create a folder to save the log files
    log_folder = create_log_folder(meetingid)
    log_path, filetimestamp = create_log_file(meetingid, tdocnumber, log_folder)
    logging.info(f"Loging file created at:{log_path}")
    logging.info(f"Summarization request: meeting:{meetingid},Tdoc:{tdocnumber}")

    st.session_state["log_path"] = log_path

    tdocnumber, error_tdoc = check_input_format(tdocnumber)

    # Create a folder to work (download/extract the tdoc)
    # This folder is deleted at the end
    working_folder = create_working_folder(meetingid)
    logging.info(f"Working folder created at: {working_folder}")

    logging.info(f"Processing request: meeting id:{meetingid},TDoc#:{tdocnumber}")

    # No errors found on the TDoc number
    if error_tdoc == '':
        # Download the tdoc from 3GPP FTP server, extract the zip file and find the word (.docx) file
        # .docx file is saved in the working folder

        tdoc_file_name, err = download_and_extract_tdoc(meetingid, tdocnumber, working_folder)
        if err != '':
            logging.error(f"Download/extract error: {err}")
            st.session_state["error"] = err

        else:
            logging.info(f"Download success:{tdoc_file_name}")
            # TDoc (.docx) file path
            file_path = get_file_path(working_folder, tdoc_file_name)

            # call_api is used for controlling the gpt-4o api call
            # gpt-4o api calls bills based on the number of requests/tokens.
            # When developer debugging other functional blocks, call_api = False does not call gpt-4o prompt.
            # If call_api = False, only first 2000 characters of the extracted TDoc is returned
            # If call_api = True, gpt-4o prompt is called (billed)
            call_api = False  # True  #

            # Get the user authenticated and get an API key
            # Set the OPENAI_API_KEY environment variable
            user_key = authenticate_user()

            # Generate the text summary
            tdoc_summary_txt, tdoc_txt, err_summary_gen = get_tdoc_content(file_path, user_key, call_api)
            if err_summary_gen != '':
                logging.error(f"error:', {err_summary_gen}")
                st.session_state["error"] = err_summary_gen
                # error_message = err_summary_gen
            else:
                logging.info(f"Summary generated:'{err_summary_gen}")
                st.session_state["tdoc_summary_txt"] = tdoc_summary_txt
                # text_summary = tdoc_summary_txt
                # print('content:', tdoc_summary_txt)

            # p_mean, r_mean, f1_mean = calculate_bert_score(tdoc_summary_txt, tdoc_txt)
            # logging.info(f"BERTScore: Precision:{p_mean}, Recall: {r_mean}, F1 Score: {f1_mean}")

            if call_api:
                logging.info(f"Semantic score from API")
                rating_summary, err_score_cal = calculate_semantic_score(tdoc_summary_txt, tdoc_txt, user_key,
                                                                         model='gpt-4')

                # If score calculation is successful,show to the user
                if err_score_cal == '':
                    logging.info(f"Semantic score {rating_summary}")

                    # Split the string into lines and find the line that starts with "Overall"
                    for line in rating_summary.splitlines():
                        if line.startswith("Overall:"):
                            overall_score = line.split(": ")[1]
                            logging.info(f"Overall score: {overall_score}")
                            st.session_state["score"] = overall_score
                else:
                    # This error is not set to the session as this error is not required to show to the user
                    logging.error(f"Semantic score calculation error {err_score_cal}")
            else:
                st.session_state["score"] = 'Not calculated'

            data_folder = create_data_folder()
            data_filename = create_data_file(data_folder, meetingid, tdocnumber, filetimestamp)
            logging.info(f"Data pickle file {data_filename}")

            # Store data_filename in the session
            st.session_state["data_filename"] = data_filename
            logging.info(f"Data file name saved to session")

            # Dump data to the data file using identifier 1
            dump_data(data_filename, st.session_state, 1)
            logging.info(f"Data dumped 1")

        # Remove the working folder
        delete_working_folder(working_folder)

    else:
        st.session_state["error"] = error_tdoc

    st.session_state['step'] = 2
    logging.info(f"Changing session step {st.session_state['step']}")


def handle_score_form_submit():
    userscore = st.session_state.get("user_score", "")

    if not userscore:
        st.warning("User score cannot be empty.")
        return

    logging.info(f"User Rating is {userscore}")

    st.session_state["user_score"] = userscore

    # Get the data file name (already written in first session, override here with rating)
    data_filename = st.session_state["data_filename"]

    # Dump data to the data file using identifier 2
    dump_data(data_filename, st.session_state, 2)
    st.session_state['step'] = 1
    logging.info(f"Changing session step {st.session_state['step']}")
    # st.success(f"Processed score form")


def go_back():
    st.session_state['step'] = 1

    # st.success(f"Processed score form")


# Display summary form
if st.session_state.step == 1:
    st.session_state['error'] = ''
    with st.form("first_form"):
        st.text_input("Meeting ID:", key="first_meeting_id")
        st.text_input("TDoc Number:", key="first_tdoc_number")
        first_form_submit = st.form_submit_button("Generate Summary", on_click=handle_summary_form_submit)

# Display second form
if st.session_state.step == 2:
    # st.write(f"Meeting ID: {st.session_state['meeting_id']}")
    # st.write(f"TDoc Number: {st.session_state['tdoc_number']}")

    with st.container():
            if st.session_state.get("error") != '':
                with st.form("second_form"):
                    st.write(f":red[**Error processing the request (Meeting ID:{st.session_state['meeting_id']}, TDoc Number:{st.session_state['tdoc_number']}), Error: {st.session_state.get("error")}**]")
                    logging.info(f"Handle error Changing session step {st.session_state['step']}")
                    go_back_submit = st.form_submit_button("Go back", on_click=go_back)
            else:
                with st.form("second_form"):
                    st.write(f" :blue[**Generated summary (Meeting ID:{st.session_state['meeting_id']}, TDoc Number:{st.session_state['tdoc_number']}):**]")
                    st.write(st.session_state["tdoc_summary_txt"])
                    st.write(f" :blue[**Semantic score:{st.session_state["score"]}**]")
                    go_back_submit = st.form_submit_button("Go back", on_click=go_back)
                with st.form("score_form"):
                    # st.text_input("My score:", key="user_score")

                    st.slider('Enter your score:', min_value=1, max_value=10, value=5, key="user_score")
                    second_form_submit = st.form_submit_button("Submit my score", on_click=handle_score_form_submit)



# @st.cache_data
# def handle_summary_form(meetingid, tdocnumber):
#     # Validate inputs
#     if not tdocnumber.strip():
#         # st.session_state["error"] = "Error: TDoc Number cannot be empty."
#         st.warning("TDoc Number cannot be empty.")
#         return
#
#     if not meetingid.strip():
#         # st.session_state["error"] = "Error: Meeting ID cannot be empty."
#         st.warning("Meeting ID cannot be empty.")
#         return
#
#     # if (tdocnumber.strip() == st.session_state["meeting_id"]) and (tdocnumber.strip() == st.session_state["tdoc_number"]):
#     #     if st.session_state['log_file'] != '':
#     #         logging.info(f"Request came:meeting id {st.session_state["meeting_id"]}, tdoc {st.session_state["tdoc_number"]}, {log_path}")
#     #
#     #     return
#
#     st.session_state["meeting_id"] = meetingid
#     st.session_state["tdoc_number"] = tdocnumber
#
#     # Create a folder to save the log files
#     log_folder = create_log_folder(meeting_id)
#     log_path, filetimestamp = create_log_file(meetingid, tdocnumber, log_folder)
#     logging.info(f"Loging file created at:{log_path}")
#     logging.info(f"Summarization request: meeting:{meetingid},Tdoc:{tdocnumber}")
#
#     st.session_state["log_path"] = log_path
#
#     tdocnumber, error_tdoc = check_input_format(tdocnumber)
#
#     # Create a folder to work (download/extract the tdoc)
#     # This folder is deleted at the end
#     working_folder = create_working_folder(meetingid)
#     logging.info(f"Working folder created at: {working_folder}")
#
#     logging.info(f"Processing request: meeting id:{meetingid},TDoc#:{tdocnumber}")
#
#     # No errors found on the TDoc number
#     if error_tdoc == '':
#         # Download the tdoc from 3GPP FTP server, extract the zip file and find the word (.docx) file
#         # .docx file is saved in the working folder
#
#         tdoc_file_name, err = download_and_extract_tdoc(meetingid, tdocnumber, working_folder)
#         if err != '':
#             logging.error(f"Download/extract error: {err}")
#             st.session_state["error"] = err
#
#         else:
#             logging.info(f"Download success:{tdoc_file_name}")
#             # TDoc (.docx) file path
#             file_path = get_file_path(working_folder, tdoc_file_name)
#
#             # call_api is used for controlling the gpt-4o api call
#             # gpt-4o api calls bills based on the number of requests/tokens.
#             # When developer debugging other functional blocks, call_api = False does not call gpt-4o prompt.
#             # If call_api = False, only first 2000 characters of the extracted TDoc is returned
#             # If call_api = True, gpt-4o prompt is called (billed)
#             call_api = False  # True  #
#
#             # Get the user authenticated and get an API key
#             # Set the OPENAI_API_KEY environment variable
#             user_key = authenticate_user()
#
#             # Generate the text summary
#             tdoc_summary_txt, tdoc_txt, err_summary_gen = get_tdoc_content(file_path, user_key, call_api)
#             if err_summary_gen != '':
#                 logging.error(f"error:', {err_summary_gen}")
#                 st.session_state["error"] = err_summary_gen
#                 # error_message = err_summary_gen
#             else:
#                 logging.info(f"Summary generated:'{err_summary_gen}")
#                 st.session_state["tdoc_summary_txt"] = tdoc_summary_txt
#                 # text_summary = tdoc_summary_txt
#                 # print('content:', tdoc_summary_txt)
#
#             # p_mean, r_mean, f1_mean = calculate_bert_score(tdoc_summary_txt, tdoc_txt)
#             # logging.info(f"BERTScore: Precision:{p_mean}, Recall: {r_mean}, F1 Score: {f1_mean}")
#
#             if call_api:
#                 logging.info(f"Semantic score from API")
#                 rating_summary, err_score_cal = calculate_semantic_score(tdoc_summary_txt, tdoc_txt, user_key,
#                                                                          model='gpt-4')
#
#                 # If score calculation is successful,show to the user
#                 if err_score_cal == '':
#                     logging.info(f"Semantic score {rating_summary}")
#
#                     # Split the string into lines and find the line that starts with "Overall"
#                     for line in rating_summary.splitlines():
#                         if line.startswith("Overall:"):
#                             overall_score = line.split(": ")[1]
#                             logging.info(f"Overall score: {overall_score}")
#                             st.session_state["score"] = overall_score
#                 else:
#                     logging.error(f"Semantic score calculation error {err_score_cal}")
#             else:
#                 st.session_state["score"] = 'Not calculated'
#                 # enable_user_rating = 'True'
#
#             data_folder = create_data_folder()
#             data_filename = create_data_file(data_folder, meeting_id, tdoc_number, filetimestamp)
#             logging.info(f"Data pickle file {data_filename}")
#
#             # Store values in the session
#             st.session_state["data_filename"] = data_filename
#             logging.info(f"Data file name saved to session")
#
#             # Dump data to the data file using identifier 1
#             dump_data(data_filename, st.session_state, 1)
#             logging.info(f"Data dumped 1")
#
#         # Remove the working folder
#         # delete_working_folder(working_folder)
#
#     else:
#         st.session_state["error"] = error_tdoc
#         # st.write(f" :red[{error_tdoc}]")
#
#     st.session_state['step'] = 2
#     logging.info(f"Changing session step {st.session_state['step']}")


# def handle_score_form(userscore):
#     if not userscore.strip():
#         # st.session_state["error"] = "Error: TDoc Number cannot be empty."
#         st.warning("User score cannot be empty.")
#         return
#
#     logging.info(f"User Rating is {userscore}")
#
#     st.session_state["user_score"] = userscore
#
#     # Get the data file name (already written in first session, override here with rating)
#     data_filename = st.session_state["data_filename"]
#
#     # Dump data to the data file using identifier 2
#     dump_data(data_filename, st.session_state, 2)
#     st.session_state['step'] = 1
#     logging.info(f"Changing session step {st.session_state['step']}")
#     st.success(f"Processed score form")


# if st.session_state['step'] == 1:
#
#     if st.session_state["log_path"] != '':
#         st.write("Step 1 logpath not empty")
#         logging.info(f"Step 1 {st.session_state['step']}, {st.session_state["meeting_id"]}, "
#                      f"{st.session_state["tdoc_number"]}, {st.session_state.get("error")}, {st.session_state["log_path"]},"
#                      f"{st.session_state["data_filename"]}")
#     else:
#         st.write("Step 1 logpath empty")
#
#     with st.form("input_form"):
#         meeting_id = st.text_input("Meeting ID:")
#         tdoc_number = st.text_input("TDoc Number:")
#
#         generate_summary_submit = st.form_submit_button('Generate Summary',
#                                                         on_click=handle_summary_form(meeting_id, tdoc_number))


# if st.session_state.get("step") == 2:
#
#     st.write(f"Meeting ID: {st.session_state["meeting_id"]}")
#     st.write(f"TDoc Number: {st.session_state["tdoc_number"]}")
#     st.write(f"Generated summary:")
#
#     logging.info(f"Step 2 {st.session_state['step']}, {st.session_state["meeting_id"]}, "
#                  f"{st.session_state["tdoc_number"]}, {st.session_state.get("error")}, {st.session_state["log_path"]},"
#                  f"{st.session_state["data_filename"]}")
#
#     if st.session_state.get("error") != '':
#         st.write(f" :red[{st.session_state.get("error")}]")
#     else:
#         st.write(st.session_state["tdoc_summary_txt"])
#         st.write(f" :blue[Semantic score:{st.session_state["score"]}]")
#
#         with st.form("score_form"):
#             if st.session_state["tdoc_summary_txt"] is not None:
#                 st.write('Please rate the generated summary')
#                 # second_number = st.number_input("Enter the score:", step=1, format="%d")
#                 # user_score = st.slider('Enter the score:', 1, 10)
#                 user_score = st.text_input("Enter the score:")
#                 submit_score = st.form_submit_button('Submit Score', on_click=handle_score_form(user_score))
