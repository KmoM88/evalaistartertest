import logging

logger = logging.getLogger(__name__)

def evaluate(user_submission_file, phase_codename, **kwargs):
    """
    Realiza la evaluación (Mock por ahora).
    """
    logger.info(f"Starting evaluation phase: {phase_codename}")
    logger.info(f"File: {user_submission_file}")

    output = {}
    
    # Lógica Mock solicitada
    if phase_codename == "dev":
        logger.info("Evaluating for Dev Phase")
        output["result"] = [
            {
                "split": "train_split",
                "show_to_participant": True,
                "accuracies": {"Metric1": 90},
            },
        ]
    elif phase_codename == "test":
        logger.info("Evaluating for Test Phase")
        output["result"] = [
            {
                "split": "train_split",
                "show_to_participant": True,
                "accuracies": {"Metric1": 90},
            },
            {
                "split": "test_split",
                "show_to_participant": False,
                "accuracies": {"Metric1": 50, "Metric2": 40},
            },
        ]
    
    logger.info("Completed evaluation for Test Phase")
    return output