from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime
from app.schemas.schemas import PullRequestReassign, PullRequestCreate, PullRequestMerge


async def get_conn(request: Request):
    return request.app.state.db

router = APIRouter(prefix="/pullRequest", tags=["PullRequests"])

@router.post("/create")
async def create_pull_request(data: PullRequestCreate, db=Depends(get_conn)):
    pr_id = data.pull_request_id
    pr_name = data.pull_request_name
    author_id = data.author_id

    async with db.acquire() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow("SELECT * FROM pull_requests WHERE pull_request_id=$1", pr_id)
            if existing:
                raise HTTPException(
                    status_code=409, 
                    detail={"error": {"code": "PR_EXISTS", "message": "PR id already exists"}}
                )
    
        author = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", author_id)
        if not author or not author["team_name"]:
            raise HTTPException(
                status_code=404,
                detail={"error": "AUTHOR_NOT_FOUND", "message": "Author not found" }
            )
        
        reviewers = await conn.fetch("""
            SELECT user_id FROM users
            WHERE team_name=$1 AND is_active=TRUE AND user_id <> $2
            ORDER BY RANDOM() LIMIT 2
        """, author["team_name"], author_id)

        assigned_reviewers = [r["user_id"] for r in reviewers]

        await conn.execute("""
            INSERT INTO pull_requests (pull_request_id, pull_request_name, author_id, status, assigned_reviewers, created_at) 
            VALUES ($1, $2, $3, 'OPEN', $4, $5)
        """, pr_id, pr_name, author_id, assigned_reviewers, datetime.now())

        await conn.close()
        return {
            "pr": {
                "pull_request_id": pr_id,
                "pull_request_name": pr_name,
                "author_id": author_id,
                "status": "OPEN",
                "assigned_reviewers": assigned_reviewers
            }
        }
    
@router.post("/merge")
async def merge_pull_requests(data: PullRequestMerge, db=Depends(get_conn)):
    pr_id = data.pull_request_id

    async with db.acquire() as conn:
        pr = await conn.fetchrow("SELECT * FROM pull_requests WHERE pull_request_id=$1", pr_id)
        if not pr:
            raise HTTPException(
                status_code=404,
                detail={"error": "PR_NOT_FOUND", "message": "Pr not found" }
            )

        if pr["status"] == "MERGED":
            return {"pr": dict(pr)}

        merged_at = datetime.now()
        await conn.execute(
            "UPDATE pull_requests SET status='MERGED', merged_at=$1 WHERE pull_request_id=$2", merged_at, pr_id
        )

        pr = await conn.fetchrow("SELECT * FROM pull_requests WHERE pull_request_id=$1", pr_id)

        return {"pr": dict(pr)}

@router.post("/reassign")
async def reassign_reviewer(data: PullRequestReassign, db=Depends(get_conn)):
    pr_id = data.pull_request_id
    old_reviewer_id = data.old_user_id

    async with db.acquire() as conn:
        pr = await conn.fetchrow("SELECT * FROM pull_requests WHERE pull_request_id=$1", pr_id)
        
        if not pr:
            raise HTTPException(
                status_code=404,
                detail={"error": "PR_NOT_FOUND", "message": "Pr not found" }
            )

        if pr["status"] == "MERGED":
            raise HTTPException(
                status_code=409,
                detail={"code": "PR_MERGED", "message": "cannot reassign on merged PR" }
            )
        
        reviewers: list[str] = pr["assigned_reviewers"] or []

        if old_reviewer_id not in reviewers:
            raise HTTPException(
                status_code=409,
                detail={"code": "NOT_ASSIGNED", "message": "reviewer is not assigned to this PR"}
            )

        author_team = await conn.fetchval(
            "SELECT team_name FROM users WHERE user_id=$1",
            pr["author_id"],
        )

        if not author_team:
            raise HTTPException(
                status_code=404,
                detail={"error": "AUTHOR_NOT_FOUND", "message": "Author not found" }
            )
        
        candidate = await conn.fetchrow(
            """
            SELECT user_id FROM users
            WHERE team_name=$1
              AND is_active=TRUE
              AND user_id <> $2
              AND user_id NOT IN ($3)
            ORDER BY RANDOM() LIMIT 1
            """,
            author_team,
            pr["author_id"],
            reviewers,
        )

        if not candidate:
            raise HTTPException(
                status_code=409,
                detail={ "code": "NO_CANDIDATE", "message": "no active replacement candidate in team" }
            )

        new_reviewer = candidate["user_id"]

        updated_reviewers = [
            new_reviewer if r == old_reviewer_id else r for r in reviewers
        ]

        await conn.execute(
            "UPDATE pull_requests SET assigned_reviewers=$2 WHERE pull_request_id=$1",
            pr_id,
            updated_reviewers,
        )

        updated = await conn.fetchrow(
            "SELECT * FROM pull_requests WHERE pull_request_id=$1",
            pr_id,
        )

        return {"pr": dict(updated), "replaced_by": new_reviewer}