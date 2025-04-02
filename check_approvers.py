from github import Github
import sys
import os
APPROVED_STATE = "APPROVED"

class CommitHandler:
    def __init__(self, pr):
        self.pr = pr

    def get_committers(self):
        return {commit.committer.login for commit in self.pr.get_commits() if commit.committer}


class PullRequestChecker:
    def __init__(self, repo_name: str, pr_number: int, token: str):
        self.repo_name = repo_name
        self.pr_number = pr_number
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)
        self.pr = self.repo.get_pull(pr_number)
        self.commit_handler = CommitHandler(self.pr)

    def get_approvers(self):
        return {review.user.login for review in self.pr.get_reviews() if review.state == APPROVED_STATE}

    def check_approvers(self):
        committers = self.commit_handler.get_committers()
        approvers = self.get_approvers()
        intersection = committers.intersection(approvers)
        if intersection:
            raise Exception(f"Approver(s) {', '.join(intersection)} are also committers. Failing the workflow.")
        print("All checks passed successfully.")

if __name__ == "__main__":
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PR_NUMBER')
    token = os.getenv('GITHUB_TOKEN')

    if not repo_name or not pr_number or not token:
        print("Error: Missing required environment variables.")
        sys.exit(1)

    try:
        pr_number = int(pr_number)
    except ValueError:
        print("Error: PR_NUMBER should be an integer.")
        sys.exit(1)

    try:
        checker = PullRequestChecker(repo_name, pr_number, token)
        checker.check_approvers()
    except Exception as e:
        print(str(e))
        sys.exit(1)
