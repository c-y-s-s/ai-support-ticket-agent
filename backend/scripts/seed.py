from app.config import get_settings
from app.database import Database


def main() -> None:
    settings = get_settings()
    database = Database(settings.database_path, settings.database_url)
    database.initialize()
    backend = "postgres" if database.is_postgres else "sqlite"
    print(f"Database initialized with seed data ({backend}).")


if __name__ == "__main__":
    main()
