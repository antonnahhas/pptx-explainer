import uuid
import os
from flask import Flask, request, jsonify
import json
from handle_db import User, Upload, engine
from sqlalchemy.orm import Session

webAPI = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
OUTPUT_FOLDER = 'outputs'
webAPI.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
webAPI.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
webAPI.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
ERROR = 400
NOT_FOUND = 404
OK = 200
INTERNAL_ERROR = 500
PENDING = 'pending'
PROCESSING = 'processing'
DONE = 'done'
NONE = 'None'
TIME_FORMAT = '%Y%m%d%H%M%S'
NOT_FOUND_MESSAGE = "not found"
NO_FILE_ATTACHED = "No file attached"
EMPTY_FILENAME = "Empty filename"
NO_EXPLANATION_FILE = "No explanation file"
ERROR_FIELD = 'error'
EMAIL_FIELD = 'email'
FILE_FIELD = 'file'
UID_FIELD = 'uid'
STATUS_FIELD = 'status'
FILENAME_FIELD = 'filename'
TIMESTAMP_FIELD = 'timestamp'
FINISH_TIME_FIELD = 'finish_time'
EXPLANATION_FIELD = 'explanation'
NOT_FOUND_FIELD = 'not_found'
READ_FILE_MODE = 'r'
UID_NOT_FOUND = 'uid not found'
EMAIL_FILENAME_NOT_FOUND = 'file name or email not found'


def create_folder_if_not_exists(folder_path):
    """
    This method receives a folder path and checks if the path is already created, if not it creates a new one.
    :param: folder_path: a path of a folder (String)
    :return:
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


@webAPI.route("/upload", methods=['POST'])
def upload_file():
    """
    This end-point handles the '/upload' route that receives post requests to upload new files. The end-point firstly
    extracts the attached file from the request, verifies it, generates a universal unique ID, adds a time-stamp and
     the ID to the file-name, uploads the file to the 'uploads' folder and finally returns the UID as a response
     with a status code 'OK'

     ADDED:
     The end-point also receives an email with its parameters, the email could be empty. The endpoint firstly checks
     if there is an email, if so, it checks if the user is already found in the database, if so it adds a new upload
     to his uploads, if not it creates a new user for that email, and if the email is empty it creates a new
     anonymous user.
    :return: UID as a json responser (code: 200), or error with the error message as a json response (code 404)
    """
    email = request.args.get(EMAIL_FIELD)
    try:
        if FILE_FIELD not in request.files:
            return jsonify({ERROR_FIELD: NO_FILE_ATTACHED}), ERROR

        file = request.files[FILE_FIELD]
        if file.filename == '':
            return jsonify({ERROR_FIELD: EMPTY_FILENAME}), ERROR

        create_folder_if_not_exists(webAPI.config['UPLOAD_FOLDER'])

        uid = str(uuid.uuid4())

        original_filename, file_extension = os.path.splitext(file.filename)

        new_filename = f"{uid}{file_extension}"
        file.save(os.path.join(webAPI.config['UPLOAD_FOLDER'], new_filename))
        with Session(engine) as session:
            if email:
                user = session.query(User).filter_by(email=email).first()
                if user is None:
                    user = User(email=email)
                    session.add(user)
                    session.commit()
                    upload = Upload(file_name=new_filename, status=PENDING, uid=uid, user_id=user.id)
                else:
                    upload = Upload(file_name=new_filename, status=PENDING, uid=uid, user_id=user.id)
            else:
                upload = Upload(file_name=new_filename, status=PENDING, uid=uid)

            session.add(upload)
            session.commit()

        return jsonify({UID_FIELD: uid}), OK
    except Exception as e:
        return jsonify({ERROR_FIELD: str(e)}), INTERNAL_ERROR


@webAPI.route('/status', methods=['GET'])
def get_status_by_email_and_filename():
    """
    This endpoint handles the /status get requests but only when an email and a filename is provided. The endpoint
    initiates a session, finds the required file using sql queries according to the email and filename provided.
    If there is a file it returns its metadata, if not it says that the email or filename provided were not found.
    :return: returns a json object of the metadata if a file was found, or a json object with status code 404
    saying that the file was not found due to incorrect data provided.
    """
    email = request.args.get(EMAIL_FIELD)
    file_name = request.args.get(FILENAME_FIELD)

    try:
        with Session(engine) as session:
            file = session.query(Upload).join(User).filter(User.email == email, Upload.file_name == file_name,
                                                           User.id == Upload.user_id).order_by(
                Upload.upload_time.desc()).first()
            if file:
                return generate_response(file, OK)

            return jsonify({NOT_FOUND_FIELD: EMAIL_FILENAME_NOT_FOUND}), NOT_FOUND

    except Exception as e:
        return jsonify({ERROR_FIELD: str(e)}), INTERNAL_ERROR


@webAPI.route("/status/<string:uid>", methods=['GET'])
def get_status_by_uid(uid):
    """
    This end-point handles the '/status' route that receives a get request with the uid as a part of the parameters.
    The end-point firstly uses sql queries to find the required file according to the uid provided by the user.
    If the uid is not a valid one (not found in pending nor processed files) then return status code not found
    Other than that the endpoint uses the metadata of the file to return a suitable json object
    :param: uid: wanted unique ID (string)
    :return:
    """
    try:
        with Session(engine) as session:
            file = session.query(Upload).filter_by(uid=uid).first()
            if file:
                return generate_response(file, OK)

            return jsonify({NOT_FOUND_FIELD: UID_NOT_FOUND}), NOT_FOUND

    except Exception as e:
        return jsonify({ERROR_FIELD: str(e)}), INTERNAL_ERROR


def generate_response(file, status_code):
    """
    This method handles the return response for the get_status end-point, it receives a status, filename, timestamp
    and the explanations. Possible values of each of those:
    if the file is still processing:
    status is pending, filename: indicative message telling the user there is not output file name yet, timestamp:
    current time, explanations: None
    if the file finished processing:
    status: done, filename: the name of the explanations file, timestamp: current time, explanations: the explained
    content of the power-point.

    ADDED:
    a new field for the finish time of an uploaded file.
    :return: json with all the metadata of a file
    """
    return jsonify({
        STATUS_FIELD: file.status,
        FILENAME_FIELD: file.file_name,
        TIMESTAMP_FIELD: file.upload_time,
        FINISH_TIME_FIELD: file.finish_time,
        EXPLANATION_FIELD: retrieve_explanations(file)
    }), status_code


def retrieve_explanations(file):
    """
    This method receives a file object, and uses the file's status to know how to update the explanation field.
    if the status is pending then there's no explanations yet. If the status is done then it reads the explanations
    and returns the data.
    :param: file: Upload object that has all the metadata of a file.
    :return: json object of each slide and its explanations.
    """
    if file.status == PENDING or file.status == PROCESSING:
        return NONE

    with open(os.path.join(OUTPUT_FOLDER, file.uid + ".json"), READ_FILE_MODE) as f:
        json_data = f.read()
        data = json.loads(json_data)
        return data


if __name__ == "__main__":
    webAPI.run(debug=True)
