# The GPT-Explainer Project

## Introduction

Learning Software Development is hard. Especially when you can't understand the lecturer's presentations. Wouldn't it be nice to have someone explain them for you?

You are going to implement a Python script that explains Powerpoint presentations using the GPT-3.5 AI model. The script will take as input a presentation file, send the text from each slide to GPT, and save the results together in an output file.

Cool, right?

## Technologies and Libraries

The script uses these Libraries and Technologies:
1. `python-pptx`(https://pypi.org/project/python-pptx/) package. Used for parsing and extracting text from PowerPoint Presentations.
2. [OpenAI API](#integration-with-openai). To send requests to chat GPT 3.5's API and ask for explanations.
    To send requests you will need to create an OpenAI account on the [OpenAI website](https://platform.openai.com/overview). There is a "Sign up" button on the top-right.

    You will then need to [generate an API key](https://platform.openai.com/account/api-keys), that will be your identifier when using the API.
3. [`openai`](https://pypi.org/project/openai/). Instead of sending HTTP requests directly, use the openai package to do that for you.
4. [SQLite](https://www.sqlitetutorial.net/what-is-sqlite/) database 
    The DB has 2 tables:

    - Users - people who upload files for explanation.
    - Uploads - files uploaded by people, with metadata related to their processing.
5. `SQLAlchemy` package. Using ORM to access data from the DB.
6. `UUID` package. For generating a universal unique ID.
7. `Flask as Back end`. it has two endpoints:

    - Upload:
        1. Receives a POST request with an attached file.
        2. Generates a UID for the uploaded file.
        3. Saves the file in the `uploads` folder. The new filename should contain:
            - the original filename
            - a timestamp of the upload
            - the UID
        4. Returns a JSON object with the UID of the upload (`{uid: ...}`)
    - Status:
        1. Receives a GET request with a UID as a URL parameter.
        2. Returns a JSON object, with the following details:
            - `status`: status of the upload. There are 3 options:
                - `'done'` - the upload has been processed
                - `'pending'` - the upload has not yet been processed (still no output file)
                - `'not found'` - no upload exists with the given UID
            - `filename` - the original filename (without the UID and timestamp)
            - `timestamp` - the timestamp of the upload
            - `explanation` - the processed output for the upload, if it is done, or `None` if not
8. `requests` package. To handle Python CLient requests.
