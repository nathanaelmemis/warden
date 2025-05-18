from models.AdminCredentialsModel import AdminCredentialsModel


class UnverifiedAdminCredentialsModel(AdminCredentialsModel):
    verification_code: str