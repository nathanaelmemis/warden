if (-Not (Test-Path -Path ".venv" -PathType Container)) {
    python -m venv .venv
}

.\.venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload --env-file .env.development --app-dir src