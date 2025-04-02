#!/usr/bin/env python3
"""
Script to verify that pull request approvers are not also committers.
"""

from typing import Set, Optional
import logging
import sys
import os
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
APPROVED_STATE = "APPROVED"
REQUIRED_ENV_VARS = ["GITHUB_REPOSITORY", "PR_NUMBER", "GITHUB_TOKEN"]

class CommitHandler:
    """Handles commit-related operations for a pull request."""
    
    def __init__(self, pr: PullRequest) -> None:
        """
        Initialize CommitHandler.
        
        Args:
            pr: GitHub pull request object
        """
        self.pr = pr

    def get_committers(self) -> Set[str]:
        """
        Get the set of all committers in the pull request.
        
        Returns:
            Set of committer login names
        """
        return {
            commit.committer.login 
            for commit in self.pr.get_commits() 
            if commit.committer and commit.committer.login
        }

class PullRequestChecker:
    """Checks pull request approvals against committers."""

    def __init__(self, repo_name: str, pr_number: int, token: str) -> None:
        """
        Initialize PullRequestChecker.
        
        Args:
            repo_name: Name of the repository (owner/repo)
            pr_number: Pull request number
            token: GitHub authentication token
        """
        self.repo_name = repo_name
        self.pr_number = pr_number
        try:
            self.g = Github(token)
            self.repo: Repository = self.g.get_repo(repo_name)
            self.pr: PullRequest = self.repo.get_pull(pr_number)
            self.commit_handler = CommitHandler(self.pr)
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    def get_approvers(self) -> Set[str]:
        """
        Get the set of users who have approved the pull request.
        
        Returns:
            Set of approver login names
        """
        return {
            review.user.login 
            for review in self.pr.get_reviews() 
            if review.state == APPROVED_STATE and review.user
        }

    def check_approvers(self) -> None:
        """
        Verify that no committer is also an approver.
        
        Raises:
            ValueError: If any committer is also an approver
        """
        committers = self.commit_handler.get_committers()
        approvers = self.get_approvers()
        intersection = committers.intersection(approvers)
        
        if intersection:
            error_msg = (
                f"Security violation: The following users both committed code "
                f"and approved the PR: {', '.join(intersection)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Approval validation passed: No committers found among approvers")

def validate_environment() -> tuple[str, int, str]:
    """
    Validate required environment variables.
    
    Returns:
        Tuple of (repo_name, pr_number, token)
        
    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PR_NUMBER')
    token = os.getenv('GITHUB_TOKEN')

    try:
        pr_number_int = int(pr_number)
    except ValueError:
        raise ValueError(f"Invalid PR_NUMBER: {pr_number}. Must be an integer.")

    return repo_name, pr_number_int, token

def main() -> None:
    """Main execution function."""
    try:
        repo_name, pr_number, token = validate_environment()
        checker = PullRequestChecker(repo_name, pr_number, token)
        checker.check_approvers()
    except ValueError as ve:
        logger.error(str(ve))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()