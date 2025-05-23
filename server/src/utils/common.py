from typing import Callable, Dict, List

from pydantic import BaseModel
from models.AppMetadataModel import AppMetadataModel
from utils import exception
from utils.logging import logger


def app_exist(app_name: str, apps: List[AppMetadataModel]):
    return bool(list(filter(lambda apps: apps.name == app_name, apps)))

def get_app(app_name: str, apps: List[AppMetadataModel]) -> AppMetadataModel:
    return next((app for app in apps if app.name == app_name), None)

def filter_out_app(app_name: str, apps: List[AppMetadataModel]) -> List[AppMetadataModel]:
    return list(filter(lambda app: app.name != app_name, apps))

def model_list_dump(models: List[BaseModel]) -> List[Dict]:
    return [model.model_dump() for model in models]

def try_except(lambda_func: Callable, error_message: str,  **include_in_error_log):
    """
    Lambda function try catch wrapper with error logging.

    Args:
        lambda_func (Callable): Lambda function to wrap.
        error_message (int): Message to log on errors.

    Returns:
        **include_in_error_log: Data to log on errors.
    """

    if not callable(lambda_func) or lambda_func.__name__ != "<lambda>":
        raise TypeError("Only lambda functions are allowed.")

    try:
        return lambda_func()
    except Exception as error:
        logger.error(error_message, error, **include_in_error_log)
        raise exception.internal_server_error