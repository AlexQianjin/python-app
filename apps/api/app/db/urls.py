"""Adapt a shared PostgreSQL URI for the application's database drivers."""

from sqlalchemy.engine import URL, make_url


def postgres_url(uri: str) -> str:
    """Return a libpq-compatible URI for psycopg and checkpoint storage."""
    return (
        make_url(uri).set(drivername="postgresql").render_as_string(hide_password=False)
    )


def async_database_url(uri: str) -> URL:
    """Accept Supabase/libpq URIs, translating SSL options for asyncpg."""
    url = make_url(uri).set(drivername="postgresql+asyncpg")
    query = dict(url.query)
    if "sslmode" in query:
        query["ssl"] = query.pop("sslmode")
    return url.set(query=query)
