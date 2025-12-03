import os
import json
import logging
import requests
import time
from interface import EvalAIInterface
from evaluate import evaluate

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment Variables
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
API_SERVER = os.environ.get("API_SERVER")
QUEUE_NAME = os.environ.get("QUEUE_NAME")
CHALLENGE_PK = os.environ.get("CHALLENGE_PK")
SAVE_DIR = os.environ.get("SAVE_DIR", "/tmp")

def download_file(url, save_dir):
    try:
        local_filename = url.split("/")[-1]
        path = os.path.join(save_dir, local_filename)
        logger.info(f"Downloading file from {url} to {path}")
        
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return path
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

def process_message(evalai, queue_resp):
    logger.debug(f"Processing submission body: {queue_resp.get('body')}")
    receipt_handle = queue_resp.get("receipt_handle")
    logger.debug(f"Receipt handle: {receipt_handle}")
    submission_pk = queue_resp.get('body').get("submission_pk")
    phase_pk = queue_resp.get('body').get("phase_pk")
    
    logger.info(f"Submission Processing ID: {submission_pk}")

    try:
        submission = evalai.get_submission_details(submission_pk)
        phase = evalai.get_challenge_phase_details(phase_pk)
        
        current_status = submission.get("status")
        logger.info(f"Current status of submission {submission_pk}: {current_status}")
        if current_status in ["finished", "failed", "cancelled"]:
            logger.info(f"Submission {submission_pk} in status {current_status}. Removing from queue.")
            evalai.delete_message_from_queue(receipt_handle)
            return True

        if current_status == "submitted":
            evalai.update_submission_status(submission_pk, "running")

        input_file_url = submission.get("input_file")
        file_path = download_file(input_file_url, SAVE_DIR)
        
        results = evaluate(file_path, phase["codename"])
        
        evalai.update_submission_result(
            phase_pk=phase_pk,
            submission_pk=submission_pk,
            status="FINISHED",
            result=json.dumps(results["result"])
        )
        logger.info(f"Submission {submission_pk} completed.")
        evalai.delete_message_from_queue(receipt_handle)

    except Exception as e:
        logger.exception(f"Error processing submission {submission_pk}: {e}")
        try:
            evalai.update_submission_result(
                phase_pk=phase_pk,
                submission_pk=submission_pk,
                status="FAILED",
                stderr=str(e)
            )
            evalai.delete_message_from_queue(receipt_handle)
        except Exception as api_err:
            logger.error(f"Cant contact the API: {api_err}")
    return True

def main():
    if not all([AUTH_TOKEN, API_SERVER, QUEUE_NAME, CHALLENGE_PK]):
        logger.error("Env var error (AUTH_TOKEN, API_SERVER QUEUE_NAME, CHALLENGE_PK)")
        return
    evalai = EvalAIInterface(AUTH_TOKEN, API_SERVER, QUEUE_NAME, CHALLENGE_PK)
    while True:
        try:
            queue_resp = evalai.get_submission_from_queue()
            logger.debug(f"Submission queue response: {queue_resp}")
            if 'body' not in queue_resp:
                logger.error("Malformed response from submissions queue response. No body found.")
                #break
            elif queue_resp.get('body') == None:
                logger.info("Execution completed. No body in queue.")
                #break
            else:
                process_message(evalai, queue_resp)
        except Exception as e:
            logger.error(f"Error fetching submission queue: {e}")
            # break
        time.sleep(10)

if __name__ == "__main__":
    main()