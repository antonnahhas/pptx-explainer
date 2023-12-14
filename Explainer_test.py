import unittest
import subprocess

from PythonClient import PythonClient

#"C:\Users\User\Desktop\bigDataSeminar\recommendationSystems.pptx"
class SystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        This method starts a subprocess to run both the webAPI and the pptxApp files.
        :return:
        """
        cls.web_api_process = subprocess.Popen(["python", "webAPI.py"])
        cls.explainer_process = subprocess.Popen(["python", "pptxApp.py"])

    @classmethod
    def tearDownClass(cls):
        """
        This method terminates the subprocesses started before
        :return:
        """
        cls.web_api_process.terminate()
        cls.explainer_process.terminate()

    def test_upload_and_check_status(self):
        """
        This method starts the System test where it uses the PythonClient class to create an object that listens
        to the server (port::5000) adds a power-point path (the presentation is found on my computer please provide
        another one if needed, thanks) and uses both of the methods in that class to upload the file, retrieve the
        UID and check its status. Since the tests are run immediately one after the other, then the status retrieved
        must be 'pending', meaning the file has not been processed yet. Basically, the method test, if the status is
        pending then the explanation must be None, else there must be an explanation and not none.
        :return:
        """
        client = PythonClient("http://localhost:5000")

        powerpoint_path = r"C:\Users\User\Desktop\test\test.pptx"
        uid = client.upload(powerpoint_path)
        self.assertIsNotNone(uid, "UID not found in the output")

        status = client.status(uid)

        if status.status == 'pending':
            self.assertEqual(status.explanation, 'None')
        elif status.status == 'done':
            self.assertIsNone(status.explanation, "Explanation should be None")


if __name__ == '__main__':
    unittest.main()
