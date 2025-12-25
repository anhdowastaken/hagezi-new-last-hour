#!/usr/bin/env python3
"""
Monitor Hagezi's TIF blocklist for new domains using git.
Clones/pulls the repository and extracts newly added domains.
"""

import os
from datetime import datetime
from git import Repo

# Configuration
REPO_URL = "https://github.com/hagezi/dns-blocklists.git"
REPO_DIR = "hagezi-dns-blocklists"
BLOCKLIST_PATH = "domains/tif.txt"
OUTPUT_DIR = "domains"
NEW_DOMAINS_FILE = "domains/new_last_hour.txt"
LAST_COMMIT_FILE = "last_commit.txt"

def load_last_commit():
    """Load the last processed commit hash from file."""
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, 'r') as f:
            commit_hash = f.read().strip()
            print(f"Last processed commit: {commit_hash}")
            return commit_hash
    return None

def save_last_commit(commit_hash):
    """Save the current commit hash to file."""
    with open(LAST_COMMIT_FILE, 'w') as f:
        f.write(commit_hash)
    print(f"Saved current commit: {commit_hash}")

def setup_repository():
    """Clone or update the Hagezi repository."""
    if os.path.exists(REPO_DIR):
        print(f"Repository exists, pulling latest changes...")
        repo = Repo(REPO_DIR)
        origin = repo.remotes.origin
        origin.pull()
        print("Repository updated")
    else:
        print(f"Cloning repository from {REPO_URL}...")
        repo = Repo.clone_from(REPO_URL, REPO_DIR)
        print("Repository cloned successfully")

    return repo

def extract_new_domains(repo, old_commit_hash, new_commit_hash, file_path):
    """Extract new domains added between two commits."""
    if not old_commit_hash:
        print("No previous commit to compare, this is the first run")
        return []

    if old_commit_hash == new_commit_hash:
        print("No changes detected")
        return []

    print(f"Extracting changes between {old_commit_hash[:7]} and {new_commit_hash[:7]}...")

    # Get commit objects
    old_commit = repo.commit(old_commit_hash)
    new_commit = repo.commit(new_commit_hash)

    # Get the diff between old and new commit for the specific file
    diff = old_commit.diff(new_commit, paths=file_path, create_patch=True)

    new_domains = []
    for diff_item in diff:
        if diff_item.diff:
            diff_text = diff_item.diff.decode('utf-8')
            for line in diff_text.splitlines():
                # Lines starting with '+' are additions (but skip +++ header)
                if line.startswith('+') and not line.startswith('+++'):
                    domain = line[1:].strip()
                    # Skip empty lines and comments
                    if domain and not domain.startswith('#'):
                        new_domains.append(domain)

    return new_domains

def save_new_domains(domains):
    """Save newly added domains to output file."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(NEW_DOMAINS_FILE, 'w') as f:
        f.write(f"# New domains added to Hagezi TIF blocklist\n")
        f.write(f"# Last updated: {timestamp}\n")
        f.write(f"# Total new domains: {len(domains)}\n\n")

        if domains:
            for domain in sorted(domains):
                f.write(f"{domain}\n")
        else:
            f.write("# No new domains detected in the last check\n")

    print(f"Saved {len(domains)} new domains to {NEW_DOMAINS_FILE}")

def commit_changes():
    """Commit changes to this repository."""
    try:
        repo = Repo('.')

        # Files to commit
        files_to_commit = [NEW_DOMAINS_FILE, LAST_COMMIT_FILE]

        # Check if there are changes
        has_changes = False
        for file in files_to_commit:
            if repo.is_dirty(path=file) or file in repo.untracked_files:
                has_changes = True
                break

        if has_changes:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            repo.index.add(files_to_commit)
            repo.index.commit(f'Update new domains - {timestamp}')
            print(f"Committed changes")
        else:
            print("No changes to commit")
    except Exception as e:
        print(f"Error committing changes: {e}")

def main():
    """Main execution function."""
    try:
        print("=" * 60)
        print("Hagezi TIF Blocklist - New Domains Tracker")
        print("=" * 60)

        # Load last processed commit
        old_commit_hash = load_last_commit()

        # Setup and update the Hagezi repository
        repo = setup_repository()

        # Get current commit
        current_commit = repo.head.commit
        new_commit_hash = current_commit.hexsha
        print(f"Current commit: {new_commit_hash}")

        # Extract new domains if there are changes
        new_domains = extract_new_domains(repo, old_commit_hash, new_commit_hash, BLOCKLIST_PATH)

        # Save results
        save_new_domains(new_domains)

        # Save the current commit hash
        save_last_commit(new_commit_hash)

        # Commit to this repository
        commit_changes()

        print("=" * 60)
        print("Process completed successfully!")
        print(f"Total new domains found: {len(new_domains)}")
        print("=" * 60)

    except Exception as e:
        print(f"Error during execution: {e}")
        raise

if __name__ == "__main__":
    main()
