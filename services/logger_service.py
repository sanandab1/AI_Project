import logging
import json
from datetime import datetime
from typing import Any, Optional
from functools import wraps
import uuid

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id = str(uuid.uuid4())
        self._setup_handler()

    def _setup_handler(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

    def _format_log(self, level: str, message: str, **kwargs) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "correlation_id": self.correlation_id,
            "message": message,
            **kwargs
        }
        return json.dumps(log_entry)

    def set_correlation_id(self, correlation_id: str):
        self.correlation_id = correlation_id

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_log("CRITICAL", message, **kwargs))

def with_correlation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        correlation_id = kwargs.pop('correlation_id', str(uuid.uuid4()))
        logger = StructuredLogger(func.__module__)
        logger.set_correlation_id(correlation_id)
        kwargs['logger'] = logger
        return func(*args, **kwargs)
    return wrapper
