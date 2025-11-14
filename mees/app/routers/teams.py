from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas import schemas


router = APIRouter(prefix="/team", tags=["Teams"])

async def get_conn(request: Request):
    return request.app.state.db

@router.post("/add", status_code=201)
async def add_team(team: schemas.Team, db=Depends(get_conn)):
    async with db.acquire() as conn:
        existing = await conn.fetchrow("SELECT team_name FROM teams WHERE team_name = $1", team.team_name)
        if existing:
            print("Этого нет в бд")
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "TEAM_EXISTS", "message": "team_name already exists"}}
            )
            
        
        async with conn.transaction():
            await conn.execute("INSERT INTO teams(team_name) VALUES ($1)", team.team_name)
            for member in team.members:
                await conn.execute("""
                    INSERT INTO users (user_id, username, team_name, is_active) 
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET 
                        username = EXCLUDED.username,
                        team_name = EXCLUDED.team_name,
                        is_active = EXCLUDED.is_active
                    """, member.user_id, member.username, team.team_name, member.is_active)
    return {"team": team}


@router.get("/get")
async def get_team(team_name: str, db=Depends(get_conn)):
    async with db.acquire() as conn:
        team = await conn.fetchrow("SELECT team_name FROM teams WHERE team_name = $1", team_name)
        if not team:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "team_not_found"}}
            )
        
        members = await conn.fetch("""
            SELECT user_id, username, is_active FROM users WHERE team_name = $1
        """, team_name)

        result = {
            "team_name": team_name,
            "members": [
                {"user_id": m["user_id"], "username": m["username"], "is_active": m["is_active"]}
                for m in members
            ]
        }
        return result 
    
@router.get("/deactivate")
async def deactivate_team(team_name: str, db=Depends(get_conn)):
    async with db.acquire() as conn:
        team = await conn.fetchrow("SELECT * FROM teams WHERE team_name=$1", team_name)
        if not team:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "team not found"}}
            )

        members = await conn.fetch("SELECT user_id FROM users WHERE team_name=$1", team_name)
        users_id = [m["user_id"] for m in members]

        await conn.execute("UPDATE users SET is_active=false WHERE team_name=$1", team_name)

        open_prs = await conn.fetch("SELECT * FROM pull_requests WHERE team_name=$1", team_name)

        updated = 0
        for pr in open_prs:
            reviewers = pr["assigned_reviewers"]
            changed = False 
            new_reviewers = []
            for r in reviewers:
                if r in users_id:
                    changed = True 
                    replacement = await conn.fetchval("""
                        SELECT user_id FROM users
                        WHERE team_name=$1 AND is_active=true
                        AND user_id<>$2
                        ORDER BY random() LIMIT 1
                    """, team_name, pr["author_id"])
                    if replacement:
                        new_reviewers.append(replacement)
                else:
                    new_reviewers.append(r)

            if changed:
                await conn.execute("""
                    UPDATE pull_requests
                    SET assigned_reviewers=$1
                    WHERE pull_request_id=$2
                """, new_reviewers, pr["pull_request_id"])
                updated += 1
        return {"team_name": team_name, "deactivated_users": users_id, "updated_prs": updated}
