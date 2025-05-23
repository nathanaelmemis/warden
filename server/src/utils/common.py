from typing import Dict, List, TypeVar

from pydantic import BaseModel
from models.AppMetadataModel import AppMetadataModel


def app_exist(app_name: str, apps: List[AppMetadataModel]):
    return bool(list(filter(lambda apps: apps.name == app_name, apps)))

def get_app(app_name: str, apps: List[AppMetadataModel]) -> AppMetadataModel:
    return next((app for app in apps if app.name == app_name), None)

def filter_out_app(app_name: str, apps: List[AppMetadataModel]) -> List[AppMetadataModel]:
    return list(filter(lambda app: app.name != app_name, apps))

def model_list_dump(models: List[BaseModel]) -> List[Dict]:
    return [model.model_dump() for model in models]