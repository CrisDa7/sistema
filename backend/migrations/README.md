# Migrations

This project is configured to use Flask-Migrate/Alembic.

Migration files are tracked under `migrations/versions/`.

This repository intentionally keeps schema changes explicit and scoped.

No automatic `db.create_all()` is used.
