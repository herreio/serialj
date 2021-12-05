import logging
import dateutil.tz
from .utils import set_stream


class Parser:
    """
    Generic parser class
    """

    def __init__(self, data, name, level, local_tz="Europe/Berlin"):
        self.data = data
        if name is None:
            name = __name__
        self.logger = logging.getLogger(name)
        if level is None:
            level = logging.INFO
        if not self.logger.handlers:
            set_stream(self.logger, level=level)
        self.timezone = dateutil.tz.gettz(local_tz)
