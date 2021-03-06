from typing import Union

from . import framework_integration


class InvalidQueryParamException(framework_integration.APIException):
    """
    An error thrown when a parameter fails its validation.
    """

    def __init__(self, detail: Union[dict, str], status: int):
        """
        Instantiates the exception.

        :param detail: dict or string with the details
        :param status: status code
        """
        super().__init__(detail)
        self.status_code = status


# Avoid circular imports
APIException = framework_integration.APIException
