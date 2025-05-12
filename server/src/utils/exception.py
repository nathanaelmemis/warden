from fastapi import HTTPException, status

invalid_credentials = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid credentials.")
account_locked = HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Account locked. Contact support.")
unauthorized_access = HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized access.")
invalid_access_token = HTTPException(status.HTTP_403_FORBIDDEN, "Invalid access token.")

def data_conflict(message: str):
    return HTTPException(status.HTTP_409_CONFLICT, message)