import logging
import sys
from backend.app.core.config import get_settings

settings = get_settings()


def setup_logging() -> logging.Logger:
    """
    Configures standardized application-wide logging with uniform formatting.
    """
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Specific logger for application events
    logger = logging.getLogger("docgen")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
