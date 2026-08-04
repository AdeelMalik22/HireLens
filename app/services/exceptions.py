class ServiceError(Exception):
    """Base exception for expected business-level failures."""


class NotFoundError(ServiceError):
    pass


class UnsupportedFileError(ServiceError):
    pass


class FileTooLargeError(ServiceError):
    pass


class DatabaseOperationError(ServiceError):
    pass
