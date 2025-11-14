CREATE TABLE IF NOT EXISTS teams (
    team_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    team_name TEXT REFERENCES teams(team_name),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pull_requests (
    pull_request_id TEXT PRIMARY KEY,
    pull_request_name TEXT NOT NULL,
    author_id TEXT REFERENCES users(user_id),
    status TEXT CHECK (status IN ('OPEN', 'MERGED')) DEFAULT 'OPEN',
    assigned_reviewers TEXT[] DEFAULT '{}',
    created_at TIMESTAMP,
    merged_at TIMESTAMP
);

