import logging
import requests

logger = logging.getLogger(__name__)

class EvalAIInterface:
    def __init__(self, auth_token, api_server, queue_name, challenge_pk):
        self.auth_token = auth_token
        self.api_server = api_server
        self.queue_name = queue_name
        self.challenge_pk = challenge_pk
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    def _get_url(self, endpoint):
        return f"{self.api_server}{endpoint}"

    def _make_request(self, method, endpoint, data=None):
        url = self._get_url(endpoint)
        try:
            response = requests.request(method=method, url=url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conecting with EvalAI ({method} {url}): {e}")
            if response is not None:
                logger.error(f"Server error: {response.text}")
            raise

    def get_message_from_sqs_queue(self):
        endpoint = f"/api/jobs/challenge/queues/{self.queue_name}/"
        return self._make_request("GET", endpoint)

    def delete_message_from_sqs_queue(self, receipt_handle):
        endpoint = f"/api/jobs/queues/{self.queue_name}/"
        data = {"receipt_handle": receipt_handle}
        return self._make_request("POST", endpoint, data)

    def update_submission_status(self, submission_pk, status):
        endpoint = f"/api/jobs/challenge/{self.challenge_pk}/update_submission/"
        data = {
            "submission": submission_pk,
            "submission_status": status,
        }
        return self._make_request("PATCH", endpoint, data)

    def update_submission_result(self, phase_pk, submission_pk, status, result=None, stdout="", stderr="", metadata=""):
        endpoint = f"/api/jobs/challenge/{self.challenge_pk}/update_submission/"
        data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "submission_status": status,
            "stdout": stdout,
            "stderr": stderr,
            "result": result,
            "metadata": metadata,
        }
        return self._make_request("PUT", endpoint, data)

    def get_submission_details(self, submission_pk):
        endpoint = f"/api/jobs/submission/{submission_pk}"
        return self._make_request("GET", endpoint)

    def get_challenge_phase_details(self, phase_pk):
        endpoint = f"/api/challenges/challenge/phase/{phase_pk}"
        return self._make_request("GET", endpoint)