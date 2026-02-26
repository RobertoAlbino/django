class DomainError(Exception):
    pass


class AlreadyEnrolledError(DomainError):
    pass


class NotEnrolledError(DomainError):
    pass


class InvalidGradeError(DomainError):
    pass
