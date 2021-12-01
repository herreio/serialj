import json
import logging


def set_stream(logger, level=None):
    """
    Create log stream, format output and set level
    """
    if level is None:
        level = logging.INFO
    stream = logging.StreamHandler()
    stream.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    stream.setFormatter(formatter)
    logger.addHandler(stream)


logger = logging.getLogger(__name__)
set_stream(logger)


def read_json(path):
    """
    Read JSON file at given path
    """
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as err:
        logger.error(err)


def pretty_json(data):
    """
    Create a pretty formatted JSON string.
    """
    return json.dumps(data, ensure_ascii=False, indent=2)
