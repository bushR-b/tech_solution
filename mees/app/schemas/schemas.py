from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum 


class ErrorCode(str, Enum):
    TEAM_EXISTS = "TEAM_EXISTS"
    PR_EXISTS = "PR_EXISTS"
    PR_MERGED = "PR_MERGED"
    NOT_ASSIGNED = "NOT_ASSIGNED"
    NO_CANDIDATE = "NO_CANDIDATE"
    NOT_FOUND = "NOT_FOUND"

class ErrorResponse(BaseModel):
    error: dict

class TeamMember(BaseModel):
    user_id: str 
    username: str 
    is_active: bool


class Team(BaseModel):
    team_name: str 
    members: list[TeamMember]


class User(BaseModel):
    user_id: str 
    username: str 
    team_name: str 
    is_active: bool


class PullRequest(BaseModel):
    pull_request_id: str 
    pull_request_name: str 
    author_id: str 
    status: str 
    assigned_reviewers: list[str] 
    createdAt: datetime | None = None
    mergedAt: datetime | None = None

class PullRequestCreate(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str

class PullRequestMerge(BaseModel):
    pull_request_id: str

class PullRequestReassign(BaseModel):
    pull_request_id: str
    old_user_id: str = Field(alias="old_reviewer_id")
