from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


USER_EMAIL_VERIFICATION_COLUMNS = {
    "email_verified": "BOOLEAN DEFAULT FALSE NOT NULL",
    "email_verification_code_hash": "VARCHAR(255)",
    "email_verification_expires_at": "TIMESTAMP",
    "email_verification_sent_at": "TIMESTAMP",
    "email_verification_attempts": "INTEGER DEFAULT 0 NOT NULL",
}


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    missing_columns = [
        (name, definition)
        for name, definition in USER_EMAIL_VERIFICATION_COLUMNS.items()
        if name not in existing_columns
    ]
    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
