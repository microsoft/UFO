import logging

import colorama


RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[37m",  # gray
    logging.INFO: "\033[0m",  # white/default
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[41m",  # red background
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_color = COLORS.get(record.levelno, RESET)
        message = super().format(record)
        return f"{log_color}{message}{RESET}"


def setup_logger(level: str = logging.INFO):
    """
    Set up the logger with the specified log level.
    :param level: The logging level to set (e.g., logging.DEBUG, logging.INFO).
    """

    colorama.init()

    if level == "OFF":
        logging.disable(logging.CRITICAL)  # Disable all logs
    else:
        # Get the numeric log level from the string
        level = getattr(logging, level.upper(), logging.INFO)

        # Clear root logger handlers to avoid duplicate handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Create a new handler with color
        handler = logging.StreamHandler()
        handler.setFormatter(
            ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        root_logger.setLevel(level)
        root_logger.addHandler(handler)
