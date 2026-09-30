class AppError(Exception):
    """Error de negocio con estado HTTP y errores por campo."""

    def __init__(self, status: int, errors: dict[str, list[str]]):
        self.status = status
        self.errors = errors
