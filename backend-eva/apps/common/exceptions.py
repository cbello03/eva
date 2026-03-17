class EVABaseException(Exception):
    """Excepción base para todo el proyecto EVA"""
    message = "Ha ocurrido un error inesperado"
    code = "error_general"

    def __init__(self, message=None, code=None):
        if message: self.message = message
        if code: self.code = code

class PermissionDeniedException(EVABaseException):
    message = "No tienes permiso para realizar esta acción"
    code = "permission_denied"

class NotFoundException(EVABaseException):
    message = "El recurso solicitado no existe"
    code = "not_found"