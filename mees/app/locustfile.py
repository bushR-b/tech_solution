from locust import HttpUser, task, between 

class PRReviewUser(HttpUser):
    wait_time = between(1,2)

    @task 
    def get_team(self):
        self.client.get("/team/get?team_name=backend")

    @task
    def create_pr(self):
        payload = {
            "pull_request_id": "pr-1001",
            "pull_request_name": "Add search",
            "author_id": "u1"
        }
        self.client.post("/pullRequest/create", json=payload)

    @task
    def get_user_reviews(self):
        self.client.get("/users/getReview?user_id=u2")
        