class AppError(Exception):
    """Erro base do sistema."""


class ValidationError(AppError):
    """Erro de validacao de dados de entrada."""


class NotFoundError(AppError):
    """Erro para entidades nao encontradas."""


class BusinessRuleError(AppError):
    """Erro para regras de negocio violadas."""
