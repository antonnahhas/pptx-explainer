import requests
from datetime import datetime
from dataclasses import dataclass
import os
import re

NOT_FOUND = 404
ERROR = 400
OK = 200
DONE_STATUS = 'done'
STATUS_FIELD = 'status'
FILENAME_FIELD = 'filename'
TIMESTAMP_FIELD = 'timestamp'
FINISH_TIME_FIELD = 'finish_time'
EXPLANATION_FIELD = 'explanation'
UID_FIELD = 'uid'
EMAIL_FIELD = 'email'
NOT_FOUND_FIELD = 'not_found'
NO_DATA_RETRIEVED = "Please provide either UID or email and filename."
UPLOAD_COMPLETED_MESSAGE = "File upload is complete."
FILE_UPLOADING_MESSAGE = "File processing is still in progress."
BASE_URL = "http://localhost:5000"
FIRST_TASK_CHOOSER = "which task do you want to use? 'u' for uploading new files, 's' to get the status of a file, " \
                     "or 'q' to exit: "
UPLOAD_TASK = 'u'
STATUS_TASK = 's'
EXIT_TASK = 'q'
VALID_TASK_ERROR = "please enter a valid option."
PROVIDE_OPTIONAL_EMAIL_MESSAGE = "Please provide your email(optional, press enter for anonymous upload): "
VALID_EMAIL_ERROR = "Please provide a valid email."
PROVIDE_PATH_MESSAGE = "Enter a path for a powerpoint presentation: "
VALID_PATH_ERROR = "the path provided is not valid please provide a file on you computer."
SECOND_TASK_CHOOSER = "do you want to retrieve status by uid ('1') or by providing an email and a " \
                                "file_name('2'): "
EMAIL_AND_FILENAME_TASK = '2'
UID_TASK = '1'
PROVIDE_UID_MESSAGE = "Please enter the UID of the file to get its status: "
PROVIDE_EMAIL_MESSAGE = "Please enter an email: "
PROVIDE_FILENAME_MESSAGE = "Please enter the desired file_name: "
VALID_SECOND_TASK_ERROR = "please enter a valid option, '1' for uid, '2' for a file_name and email."


@dataclass
class Status:
    """
    This class uses dataclass decorator, has 4 members,
    Status:
    1) Pending - the file did not finish processing yet.
    2) Done - the file has finished processing.
    3) Not found - the UID provided does not exist in the uploads/processed files.
    Filename:
    1) no explanation file yet, then there is no name (when the status = pending).
    2) the filename of the explanation file or the file that has been processed ( when status = done).
    Timestamp: simply the time when the status has been changed.
    Explanation:
    1) None: if the status is pending
    2) the explanations of the slides if the status is done.
    """
    status: str
    filename: str
    timestamp: datetime
    finish_time: datetime
    explanation: str

    def is_done(self):
        """
        This method updates the status to done to indicate the file is done processing.
        :return: Returns True if the status is done, false otherwise.
        """
        return self.status == DONE_STATUS


def handle_response(response):
    """
    This method receives a response from the fetch, extracts the json data found in the response, creates a status
    object with all the desired data to display to the user.
    :param: response: response object
    :return: returns a status object with all details of the file.
    """
    json_data = response.json()
    return Status(
        status=json_data[STATUS_FIELD],
        filename=json_data[FILENAME_FIELD],
        timestamp=json_data[TIMESTAMP_FIELD],
        finish_time=json_data[FINISH_TIME_FIELD],
        explanation=json_data[EXPLANATION_FIELD]
    )


class PythonClient:
    """
    The class has two members, the base_url, which is the url and the port the web API is listening to,
    and error_messages which is a member that holds the error messages if there is any.
    The class has also two methods, upload and get status.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self._error_message = ""

    def upload(self, file_path, email):
        """
        The upload method receives a file_path which is the power-point presentation the user wants to be explained,
        as well as, an email, which is an optional way of identification for the user, if the email is None then the
        user will be anonymously added to the database.
        the method handles a POST fetch to the /upload end-point. The method as well uses the 'requests' module to
        attach the power-point Presentation, Handles the response which is the UID created by the web API. retrieves
        the uid of the file from the database to send back to the python client where it will be displayed to the user.
        :param: email: email of the user could be None or could be a String.
        :param: file_path: path of the power-point presentation (String)
        :return: UID created by web API (json)
        """

        if not email:
            email = ""

        url = self.base_url + f'/upload'
        params = {
            EMAIL_FIELD: email
        }
        files = {'file': open(file_path, 'rb')}
        response = requests.post(url, files=files, params=params)
        if response.ok:
            return response.json()[UID_FIELD]
        else:
            raise Exception(f"Upload failed. Status code: {response.status_code}")

    def status(self, uid=None, email=None, filename=None):
        """
        The status method retrieves the status based on either UID or email and filename.
        If UID is provided, it fetches the status using the UID.
        If email and filename are provided, it fetches the status using email and filename as parameters.
        :param: uid: UID of the file (optional)
        :param: email: Email of the file (optional)
        :param: filename: Filename of the file (optional)
        :return: Status object containing the status, filename, timestamp, finish upload time and explanation if any.
        """
        if uid:
            url = self.base_url + f'/status/{uid}'
            response = requests.get(url)
        elif email and filename:
            url = self.base_url + '/status'
            params = {
                EMAIL_FIELD: email,
                FILENAME_FIELD: filename
            }
            response = requests.get(url, params=params)
        else:
            self._error_message = NO_DATA_RETRIEVED
            return None
        if response.ok:
            return handle_response(response)
        elif response.status_code == NOT_FOUND:
            not_found_data = response.json()
            self._error_message = not_found_data[NOT_FOUND_FIELD]
            return None
        else:
            raise Exception(f"Status retrieval failed. Status code: {response.status_code}")

    @property
    def error_message(self):
        """
        Getter for the instance variable
        :return: returns an error message (String)
        """
        return self._error_message

    @error_message.setter
    def error_message(self, message):
        """
        Setter for the instance variable
        :param message: receives an error message (String)
        :return:
        """
        self._error_message = message


def is_email_format(email):
    """
    This method receives an email and using regular expressions it validates if the email is in the correct format.
    for instance if the email was a@gamil.com -> returns true if the email was aaaa -> returns false
    :param email: email provided by the user (String)
    :return: true if the string is in email format, false otherwise.
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    match = re.match(pattern, email)
    return match is not None


def print_status_results(status):
    """
    This function receives a status object and prints out all the required data to the user. It prints the
    status of the file, its name, upload time, finish time and finally the explanations of the file if there is any.
    :param: status: status object
    :return:
    """
    print(f"Status: {status.status}")
    print(f"Filename: {status.filename}")
    print(f"Upload Time: {status.timestamp}")
    print(f"Finish upload Time: {status.finish_time}")

    if status.is_done():
        print(UPLOAD_COMPLETED_MESSAGE)
        print(f"Explanation: {status.explanation}")
    else:
        print(FILE_UPLOADING_MESSAGE)


def main():
    """
    Implemented a main function that runs in an infinite loop that asks the user for which operation he wants to
    perform, depending on the operation, the user is required to provide an input. The method creates an object of
    PythonClient which initiates the connection with the server.

    ADDED TO THE MAIN FUNCTION:
    the ability for the user to optionally provide his email when uploading a file, and the ability to ask for
    the status of a file using an email and a file name instead of the uid.
    :return:
    """
    client = PythonClient(BASE_URL)

    while True:
        task = input(FIRST_TASK_CHOOSER).strip()
        if not task.lower() == UPLOAD_TASK and not task.lower() == STATUS_TASK and not task.lower() == EXIT_TASK:
            print(VALID_TASK_ERROR)
            continue
        elif task.lower() == UPLOAD_TASK:
            user_email = input(PROVIDE_OPTIONAL_EMAIL_MESSAGE).strip()
            if user_email:
                if not is_email_format(user_email):
                    print(VALID_EMAIL_ERROR)
                    continue

            powerpoint_path = input(PROVIDE_PATH_MESSAGE).strip()
            if not os.path.exists(powerpoint_path):
                print(VALID_PATH_ERROR)
                continue

            powerpoint_UID = client.upload(powerpoint_path, user_email)
            print(f"Uploaded file with UID: {powerpoint_UID}, please save the UID so you can get the status of the "
                  f"file when needed.")
        elif task.lower() == STATUS_TASK:
            status_task = input(SECOND_TASK_CHOOSER).strip()
            if status_task == UID_TASK:
                powerpoint_UID = input(PROVIDE_UID_MESSAGE).strip()
                status = client.status(uid=str(powerpoint_UID))
                if status is None:
                    print(client.error_message)
                else:
                    print_status_results(status)
            elif status_task == EMAIL_AND_FILENAME_TASK:
                email = input(PROVIDE_EMAIL_MESSAGE)
                if not is_email_format(email):
                    print(VALID_EMAIL_ERROR)
                    continue
                file_name = input(PROVIDE_FILENAME_MESSAGE)
                status = client.status(email=email, filename=file_name)
                if status is None:
                    print(client.error_message)
                else:
                    print_status_results(status)
            else:
                print(VALID_SECOND_TASK_ERROR)
                continue

        elif task.lower() == EXIT_TASK:
            break


if __name__ == "__main__":
    main()
