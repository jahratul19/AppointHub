from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_appointment_doctor_fields(engine: Engine) -> None:
    columns = {
        column["name"]
        for column in inspect(engine).get_columns("appointments")
    }

    statements = []
    if "doctor_id" not in columns:
        statements.append(
            "ALTER TABLE appointments "
            "ADD COLUMN doctor_id INTEGER REFERENCES doctors(id)"
        )
    if "reason" not in columns:
        statements.append("ALTER TABLE appointments ADD COLUMN reason TEXT")

    statements.append(
        "CREATE INDEX IF NOT EXISTS ix_appointments_doctor_id "
        "ON appointments (doctor_id)"
    )

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
