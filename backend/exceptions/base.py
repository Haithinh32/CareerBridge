class AppException(Exception):
    """Đã có lỗi xảy ra."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Đã có lỗi xảy ra"
        super().__init__(self.message)


class NotFoundError(AppException):
    """Không tìm thấy tài nguyên."""

    code = "NOT_FOUND"
    status_code = 404


class ValidationError(AppException):
    """Dữ liệu không hợp lệ."""

    code = "VALIDATION_ERROR"
    status_code = 400


class AuthenticationError(AppException):
    """Chưa đăng nhập hoặc phiên đăng nhập đã hết hạn."""

    code = "NOT_AUTHENTICATED"
    status_code = 401


class PermissionDeniedError(AppException):
    """Không có quyền thực hiện hành động này."""

    code = "PERMISSION_DENIED"
    status_code = 403


class ConflictError(AppException):
    """Dữ liệu đã tồn tại."""

    code = "CONFLICT"
    status_code = 409


class ConsentRequiredError(PermissionDeniedError):
    """Bạn chưa đồng ý cho mục đích xử lý dữ liệu này."""

    code = "CONSENT_REQUIRED"


class ProfileAccessRevokedError(PermissionDeniedError):
    """Doanh nghiệp không còn quyền xem hồ sơ này."""

    code = "PROFILE_ACCESS_REVOKED"


class CompanyNotVerifiedError(PermissionDeniedError):
    """Doanh nghiệp chưa được xác minh mã số thuế."""

    code = "COMPANY_NOT_VERIFIED"


class ExternalServiceError(AppException):
    """Dịch vụ bên ngoài không phản hồi."""

    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502
