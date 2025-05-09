if (-Not (Test-Path -Path ".venv" -PathType Container)) {
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
} else {
    .\.venv\Scripts\activate
}

uvicorn main:app --reload --env-file .env.development --app-dir src