from models.AdminCredentialsModel import AdminCredentialsModel


class ChangePasswordModel(AdminCredentialsModel):
    new_hash: str