import os
from datetime import datetime

# GitHub API Configuration
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Токен для увеличения лимитов

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "your-github-data-bucket")

# Data Configuration
REPOSITORIES = [
    "octocat/Hello-World",
    "torvalds/linux",
    "python/cpython"
]

# File naming
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DATA_FILE_PREFIX = "github_repos_data"