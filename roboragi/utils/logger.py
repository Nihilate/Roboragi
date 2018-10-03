"""
This class creates the logger used throughout the program
"""
import logging


def logger_factory(str_format: str, filename=None, level: str="Warning",
                   max_bytes: int=500000, backup_count: int=5):
    """
    Factory method to create a new logger instance
    """
    if not str_format:
        raise ValueError('First parameter must be a string format for logger.')
    log_level = getattr(logging, level.upper())

    # Create new logger
    new_logger = logging.getLogger('roboragi')
    new_logger.setLevel(log_level)

    # If a filename was passed in, set up logger with filename and maxbytes
    if filename:
        handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=max_bytes, backupCount=backup_count)
    # Otherwise create a simple console logger
    else:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)

    # Create Formatter
    formatter = logging.Formatter(str_format)

    handler.setFormatter(formatter)
    new_logger.addHandler(handler)
    return new_logger
