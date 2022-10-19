""" Base class for the action processor
Teh action is a means to run a operation against a object
in the queues.
"""

import logging

logger = logging.getLogger(__name__)

class BaseAction():
    """ The base action required th4e following:
        - settings: dict of
                information to load and
                initilize the action
        - criteria: dict
                informaiton to proces the object
                and / or its associated information
                to select the object to the action
        - parser: object (class, function)
        - params: dict
                A dict to build the and run against the
                parser obejct
        - destination: dict
                a set of information to sepcifiy the
                output information
                    - name / rename
                    - destination location
    """
    
    def __init__(self) -> None:
        pass