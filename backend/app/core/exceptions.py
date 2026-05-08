class EnmaskException(Exception):
    """Base exception for Enmask platform"""
    pass

class ConnectionError(EnmaskException):
    """Raised when a database connection fails"""
    pass

class RuleValidationError(EnmaskException):
    """Raised when a masking rule is invalid"""
    pass

class JobExecutionError(EnmaskException):
    """Raised when a masking job fails during execution"""
    pass

class ResourceNotFoundError(EnmaskException):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type} with ID {resource_id} not found."
        super().__init__(self.message)


class AuthenticationError(EnmaskException):
    """Raised when authentication fails"""
    pass
