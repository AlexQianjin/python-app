from sqlalchemy.engine import make_url

from app.db.urls import async_database_url, postgres_url


def test_supabase_uri_preserves_credentials_and_translates_ssl():
    uri = (
        "postgresql://postgres.project:p%40ss%25word@pooler.supabase.com:5432/"
        "postgres?sslmode=require&application_name=api"
    )
    url = async_database_url(uri)
    assert url.drivername == "postgresql+asyncpg"
    assert url.password == "p@ss%word"
    assert url.query == {"ssl": "require", "application_name": "api"}
    assert async_database_url(url.render_as_string(hide_password=False)) == url
    assert make_url(postgres_url(uri)) == make_url(uri)


def test_legacy_asyncpg_uri_works_for_both_drivers():
    uri = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    assert async_database_url(uri).drivername == "postgresql+asyncpg"
    assert postgres_url(uri) == "postgresql://postgres:postgres@localhost:5432/app"


def test_short_postgres_scheme():
    uri = "postgres://user:password@pooler.supabase.com:5432/postgres?sslmode=require"
    assert async_database_url(uri).query == {"ssl": "require"}
    assert postgres_url(uri).startswith("postgresql://")
