import logging
from .utils import set_stream


class Parser:
    """
    Generic parser class
    """

    def __init__(self, data, name, level):
        self.data = data
        if name is None:
            name = __name__
        self.logger = logging.getLogger(name)
        if level is None:
            level = logging.INFO
        set_stream(self.logger, level=level)
