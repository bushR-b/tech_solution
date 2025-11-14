from fastapi import APIRouter, Request, Depends


async def get_conn(request: Request):
    return request.app.state.db

router = APIRouter(prefix="/stats", tags=["Stats"])


# Эндпоинт статистики который будет выдавать количество назначений на пользователя, 
# количество open, merged пул реквестов, 
# количество назначений на пул реквест.
@router.get("/reviews")
async def get_review_stats(db=Depends(get_conn)):
    async with db.acquire() as conn:
        user_rows = await conn.fetch("""
            SELECT reviewer_id AS user_id, COUNT(*) AS review_count
            FROM (
                SELECT unnest(assigned_reviewers) AS reviewer_id
                FROM pull_requests
            ) reviewers
            GROUP BY reviewer_id
            ORDER BY review_count DESC;
        """)
        user_stats = [dict(row) for row in user_rows]

        pr_counts = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'OPEN') AS open,
                COUNT(*) FILTER (WHERE status = 'MERGED') AS merged,
                ROUND(AVG(array_length(assigned_reviewers, 1))::numeric, 2) AS avg_reviewers
            FROM pull_requests;
        """)

        pr_stats = dict(pr_counts) if pr_counts else {
            "total": 0, "open": 0, "merged": 0, "avg_reviewers": 0
        }

        pr_assignments = await conn.fetch("""
            SELECT
                pull_request_id,
                pull_request_name,
                COALESCE(array_length(assigned_reviewers, 1), 0) AS reviewers_count
            FROM pull_requests
            ORDER BY reviewers_count DESC, pull_request_id;
        """)
        assignments_per_pr = [dict(row) for row in pr_assignments]
    
    return { # Получаем полную статистику по 
        "users": user_stats,
        "pull_requests": pr_stats,
        "assignments_per_pr": assignments_per_pr
    }