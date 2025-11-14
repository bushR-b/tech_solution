from fastapi import APIRouter, Depends, Request, HTTPException, status
from app.schemas import schemas


router = APIRouter(prefix="/users", tags=["Users"])

async def get_conn(request: Request):
    return request.app.state.db

@router.post("/setIsActive")
async def set_is_active(user: schemas.User, db=Depends(get_conn)):
    
    async with db.acquire() as conn:
        User = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1 AND team_name = $2", user.user_id, user.team_name)
        
        if not User:
            raise HTTPException(
                status_code=404,
                detail= {"error": {"code": "NOT_FOUND", "message": "User not found"}}
            )
        
        await conn.execute("UPDATE users SET is_active = $1 WHERE user_id = $2", user.is_active, user.user_id)
        updated = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user.user_id)

        return {"user": dict(updated)}
    

@router.get("/getReview")
async def get_reviews(user_id: str, db=Depends(get_conn)):
    async with db.acquire() as conn:
        prs = await conn.fetch("""
            SELECT pull_request_id, pull_request_name, author_id, status
            FROM pull_requests
            WHERE $1 = ANY(assigned_reviewers)
        """, user_id)
        return {"user_id": user_id, "pull_requests": [dict(r) for r in prs]}
