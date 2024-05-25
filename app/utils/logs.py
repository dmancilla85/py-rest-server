import errno
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler
from os import environ as env


def create_directory(directory_path):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Created directory: {directory_path}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def setup_logging(app_name, logger=logging.getLogger()):
    if env["MODE"] != "DEBUG":
        handler = setup_handler(app_name)
        logger.addHandler(handler)

    logger.setLevel(env['LOG_LEVEL'])


def setup_handler(app_name, use_utc=False):
    filename = f"{env['LOG_PATH']}/{app_name}.log"
    backup_days = int(env['LOG_BACKUP_COUNT'])
    create_directory(env['LOG_PATH'])
    log_handler = logging.handlers.TimedRotatingFileHandler(filename,
                                                            when='midnight',
                                                            encoding='utf-8',
                                                            backupCount=backup_days)
    formatter = logging.Formatter(f'%(asctime)s {app_name} [%(process)d]: %(message)s', '%Y-%m-%d %H:%M:%S %Z')

    if use_utc:
        formatter.converter = time.gmtime  # Use UTC time

    log_handler.setFormatter(formatter)
    return log_handler

