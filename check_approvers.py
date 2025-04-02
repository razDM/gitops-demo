import os
import sys
from github import Github

class PullRequestChecker:
    def __init__(self, repo_name: str, pr_number: int, token: str):
        self.repo_name = repo_name
        self.pr_number = pr_number
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)
        self.pr = self.repo.get_pull(pr_number)

    def get_committers(self):
        committers = set()
        commits = self.pr.get_commits()
        for commit in commits:
            if commit.committer:
                committers.add(commit.committer.login)
        return committers

    def get_approvers(self):
        approvers = set()
        reviews = self.pr.get_reviews()
        for review in reviews:
            if review.state == "APPROVED":
                approvers.add(review.user.login)
        return approvers

    def check_approvers(self):
        committers = self.get_committers()
        approvers = self.get_approvers()
        intersection = committers.intersection(approvers)
        if intersection:
            print(f"Approver(s) {', '.join(intersection)} are also committers. Failing the workflow.")
            sys.exit(1)
        print("All checks passed successfully.")

if __name__ == "__main__":
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('PR_NUMBER'))
    token = os.getenv('GITHUB_TOKEN')

    checker = PullRequestChecker(repo_name, pr_number, token)
    checker.check_approvers()