#!/usr/bin/env python3
"""
Monitor Hagezi's blocklists for new records using GitHub API.
Supports multiple files configured in config.yml.
"""

import os
import requests
import yaml
from datetime import datetime, UTC
from git import Repo
from pathlib import Path

# Configuration files
CONFIG_FILE = "config.yml"
LAST_COMMIT_FILE = "last_commit.txt"

# GitHub API URLs
API_BASE = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"

def load_config():
    """Load configuration from YAML file."""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def load_last_commit():
    """Load the last processed commit SHA from file."""
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, 'r') as f:
            commit_sha = f.read().strip()
            print(f"Last processed commit: {commit_sha}")
            return commit_sha
    return None

def save_last_commit(commit_sha):
    """Save the current commit SHA to file."""
    with open(LAST_COMMIT_FILE, 'w') as f:
        f.write(commit_sha)
    print(f"Saved current commit: {commit_sha}")

def github_api_request(endpoint):
    """Make a request to GitHub API."""
    url = f"{API_BASE}{endpoint}"
    headers = {}

    # Use GitHub token if available for higher rate limits
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def get_latest_commit(repo):
    """Get the latest commit SHA for the repository."""
    endpoint = f"/repos/{repo}/commits"
    params = "?page=1&per_page=1"

    commits = github_api_request(endpoint + params)
    if commits:
        latest_commit = commits[0]
        return latest_commit['sha'], latest_commit['commit']['committer']['date']
    return None, None

def get_file_content(repo, commit_sha, file_path):
    """Fetch the file content at a specific commit."""
    url = f"{RAW_BASE}/{repo}/{commit_sha}/{file_path}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text

def parse_records(content):
    """Parse records from file content, filtering comments and empty lines."""
    records = set()
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            records.add(line)
    return records

def get_output_filename(file_path):
    """Generate output filename: [monitored_file]_NEW_last_hour.[extension]"""
    path_obj = Path(file_path)
    directory = path_obj.parent  # e.g., "domains", "ips"
    base_name = path_obj.stem  # filename without extension
    extension = path_obj.suffix  # .txt, etc.
    return os.path.join(str(directory), f"{base_name}_NEW_last_hour{extension}")

def save_new_records(file_path, records):
    """Save newly added records to output file."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    output_file = get_output_filename(file_path)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(f"# New records added to {file_path}\n")
        f.write(f"# Last updated: {timestamp}\n")
        f.write(f"# Total new records: {len(records)}\n\n")

        if records:
            for record in sorted(records):
                f.write(f"{record}\n")
        else:
            f.write("# No new records detected in the last check\n")

    print(f"  Saved {len(records)} new records to {output_file}")
    return output_file

def process_file(repo, file_path, old_commit_sha, new_commit_sha):
    """Process a single monitored file."""
    print(f"\nProcessing {file_path}:")
    print("-" * 60)

    # Fetch file content for new commit
    print("  Fetching latest file content...")
    new_content = get_file_content(repo, new_commit_sha, file_path)
    new_records_set = parse_records(new_content)
    print(f"  Latest version has {len(new_records_set)} records")

    if old_commit_sha:
        print("  Fetching previous file content...")
        try:
            old_content = get_file_content(repo, old_commit_sha, file_path)
            old_records_set = parse_records(old_content)
            print(f"  Previous version had {len(old_records_set)} records")

            # Find new records
            new_records = new_records_set - old_records_set
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("  File did not exist in previous commit")
                new_records = new_records_set
            else:
                raise
    else:
        print("  First run, no previous commit to compare")
        new_records = set()

    # Save results
    output_file = save_new_records(file_path, new_records)

    return output_file

def commit_changes(output_files):
    """Commit changes to this repository."""
    try:
        repo = Repo('.')

        # Files to commit: all output files and last commit file
        files_to_commit = output_files + [LAST_COMMIT_FILE]

        # Check if there are changes
        has_changes = False
        for file in files_to_commit:
            if os.path.exists(file) and (repo.is_dirty(path=file) or file in repo.untracked_files):
                has_changes = True
                break

        if has_changes:
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            repo.index.add(files_to_commit)
            repo.index.commit(f'Update new records - {timestamp}')
            print(f"\nCommitted changes")
        else:
            print("\nNo changes to commit")
    except Exception as e:
        print(f"\nError committing changes: {e}")

def main():
    """Main execution function."""
    try:
        print("=" * 60)
        print("Hagezi Blocklists - New Records Tracker")
        print("=" * 60)

        # Load configuration
        config = load_config()
        repo = config['repository']
        monitored_files = config['monitored_files']

        print(f"\nRepository: {repo}")
        print(f"Monitoring {len(monitored_files)} file(s)")

        # Get the latest commit from GitHub
        latest_commit_sha, commit_date = get_latest_commit(repo)
        if not latest_commit_sha:
            print("Error: Could not fetch latest commit")
            return

        print(f"\nLatest commit: {latest_commit_sha[:7]}")
        print(f"Commit date: {commit_date}")

        # Load last processed commit
        old_commit_sha = load_last_commit()

        # Check if there are new changes
        if old_commit_sha == latest_commit_sha:
            print("No new changes detected in repository")
            # Still update output files with empty results
            output_files = []
            for file_path in monitored_files:
                output_file = save_new_records(file_path, [])
                output_files.append(output_file)
            commit_changes(output_files)
            return

        # Process each monitored file
        output_files = []
        for file_path in monitored_files:
            output_file = process_file(repo, file_path, old_commit_sha, latest_commit_sha)
            if output_file:
                output_files.append(output_file)

        # Save the current commit SHA
        save_last_commit(latest_commit_sha)

        # Commit all changes
        commit_changes(output_files)

        print("\n" + "=" * 60)
        print("Process completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during execution: {e}")
        raise

if __name__ == "__main__":
    main()
