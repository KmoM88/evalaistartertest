import os
import json
import logging
import requests
from interface import EvalAIInterface
from evaluate import evaluate

# Logging
logging.basicConfig(
    level=logging.DEBUG,
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

def process_message(evalai, message):
    body = message.get("body")
    if not body:
        return False

    receipt_handle = message.get("receipt_handle")
    submission_pk = body.get("submission_pk")
    phase_pk = body.get("phase_pk")
    
    logger.info(f"Submission Processing ID: {submission_pk}")

    try:
        submission = evalai.get_submission_details(submission_pk)
        phase = evalai.get_challenge_phase_details(phase_pk)
        
        current_status = submission.get("status")
        if current_status in ["finished", "failed", "cancelled"]:
            logger.info(f"Submission {submission_pk} in status ({current_status}). Removing from queue.")
            evalai.delete_message_from_sqs_queue(receipt_handle)
            return True

        if current_status == "submitted":
            evalai.update_submission_status(submission_pk, "RUNNING")

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

    except Exception as e:
        logger.exception(f"Error processing submission {submission_pk}: {e}")
        try:
            evalai.update_submission_result(
                phase_pk=phase_pk,
                submission_pk=submission_pk,
                status="FAILED",
                stderr=str(e)
            )
            evalai.delete_message_from_sqs_queue(receipt_handle)
        except Exception as api_err:
            logger.error(f"Cant contact the API: {api_err}")
    return True

def main():
    if not all([AUTH_TOKEN, QUEUE_NAME, CHALLENGE_PK]):
        logger.error("Env var error (AUTH_TOKEN, QUEUE_NAME, CHALLENGE_PK)")
        return

    evalai = EvalAIInterface(AUTH_TOKEN, API_SERVER, QUEUE_NAME, CHALLENGE_PK)
    
    submission_queue = evalai.get_submission_from_queue()
    logger.
    # max_messages_per_run = 10
    # processed_count = 0

    # logger.info("Starting cronjob for EvalAI challenge evaluation.")

    # while processed_count < max_messages_per_run:
    #     try:
    #         message = evalai.get_message_from_sqs_queue()
    #         if not message or 'body' not in message:
    #             logger.info("Execution completed. No messages in queue.")
    #             break
            
    #         process_message(evalai, message)
    #         processed_count += 1
            
    #     except Exception as e:
    #         logger.error(f"Error in main loop: {e}")
    #         break

    logger.info(f"Loop completed. Proccesed submissions: {processed_count}")

if __name__ == "__main__":
    main()