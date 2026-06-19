class ServiceError(Exception):
    code = "SERVICE_ERROR"


class ResourceNotFoundError(ServiceError):
    code = "NOT_FOUND"


class ValidationError(ServiceError):
    code = "VALIDATION_ERROR"

