from fastapi import HTTPException, status

invalid_credentials = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Credentials")
account_locked = HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Account locked. Contact support.")