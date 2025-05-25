import pprint
import logging

from pydantic import BaseModel

class logger:
    uvicorn_logger = logging.getLogger("uvicorn.error")
    keys_to_mask = ["email", "hash", "api_key_hash"]

    @staticmethod
    def info(message: str):
        logger.uvicorn_logger.info(message)

    @staticmethod
    def error(message: str, error: Exception, **data):
        content = {}
        for name, value in data.items():
            content[name] = logger._mask_sensitive(value)

        logger.uvicorn_logger.error(f"{message}\n{repr(error)}\n{pprint.pformat(content)}")

    @staticmethod
    def _mask_sensitive(data):
        # if (isinstance(data, BaseModel)):
        #     data = data.model_dump()
            
        if isinstance(data, dict):
            return { 
                key: ("[REDACTED]" if key in logger.keys_to_mask else logger._mask_sensitive(value))
                for key, value in data.items() 
            }
        elif isinstance(data, list):
            return [ logger._mask_sensitive(item) for item in data ]
        return data