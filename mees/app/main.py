from fastapi import FastAPI
import asyncpg
from contextlib import asynccontextmanager
import app.utils.db as db
from app.routers import pull_requests, teams, users, stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.run_migrations()
    app.state.db = await asyncpg.create_pool(dsn=db.DSN_DB)
    yield
    await app.state.db.close()

app = FastAPI(title="PR Reviewer Assignment Service", lifespan=lifespan) 

app.include_router(teams.router) # Подключаем все эндпоинты которые начинаются на /team
app.include_router(pull_requests.router) # Подключаем все эндпоинты которые начинаются на /pullRequest
app.include_router(users.router) # Подключаем все эндпоинты которые начинаются на /users
app.include_router(stats.router)
