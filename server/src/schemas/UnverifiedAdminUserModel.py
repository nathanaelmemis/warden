from schemas.AdminUserModel import AdminUserModel


class UnverifiedAdminUserModel(AdminUserModel):
    verification_code: str