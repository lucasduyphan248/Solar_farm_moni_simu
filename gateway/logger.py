import logging.config
import logging.handlers
import os


# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_logger": False,
    "formatters": {
        "verbose": {
            "class": "logging.Formatter",
            "format": "[%(process)d-%(thread)d][%(asctime)s][%(levelname)7s][%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%Y:%m:%d-%H:%M:%S",
        },
        "simple": {
            "class": "logging.Formatter",
            "format": "[%(process)d-%(thread)d][%(asctime)s] %(message)s",
            "datefmt": "%Y:%m:%d-%H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "verbose",
            "filename": "Logs/gw.log",
            "interval": 12,
            "when": "h",
            "backupCount": 14,
            "encoding": "utf8",
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "DEBUG"},
}
os.makedirs("Logs", exist_ok=True)
logging.config.dictConfig(LOGGING)

################ Logger #################
LOG = logging.getLogger('root')
LOG.info("GW")
