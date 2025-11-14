from fastapi import Request
import asyncpg
 
DSN_DB = "postgresql://postgres:postgres@db:5432/pr_reviewer"

async def get_connection(request: Request):
    if not hasattr(request.app.state, "db"):
        raise RuntimeError("DB pool is not initialized")
    return request.app.state.db

async def run_migrations():
    DSN_DB = "postgresql://postgres:postgres@db:5432/pr_reviewer"
    conn = await asyncpg.connect(DSN_DB)
    with open("models.sql", "r") as f:
        schema = f.read()
    await conn.execute(schema)
    await conn.close()


