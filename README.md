# Hagezi Blocklists - New Records Tracker

[![Update New Records](https://github.com/anhdowastaken/hagezi-new-last-hour/actions/workflows/update.yml/badge.svg)](https://github.com/anhdowastaken/hagezi-new-last-hour/actions/workflows/update.yml)

An automated monitoring tool that tracks newly added records (domains, IPs, etc.) from the [Hagezi DNS Blocklists](https://github.com/hagezi/dns-blocklists) repository. This lightweight tracker uses GitHub API to efficiently monitor blocklist updates without cloning large repositories.

## What It Does

- **Hourly Monitoring**: Automatically checks for new additions to Hagezi blocklists every hour
- **Incremental Tracking**: Identifies only the newly added records since the last check
- **API-Based**: Uses GitHub API for efficient fetching without repository cloning
- **Configurable**: Monitor multiple blocklist files through simple YAML configuration
- **Auto-Commit**: Automatically commits changes to track historical additions

## Why It's Useful

If you need to:
- Stay updated on the latest threats added to Hagezi blocklists
- Track new malicious domains/IPs as they're discovered
- Integrate new blocklist additions into your security infrastructure
- Monitor specific blocklist files for changes
- Build custom filtering or alerting based on new additions

This tool provides a lightweight, automated solution that runs on GitHub Actions with zero infrastructure costs.

## Getting Started

### Prerequisites

- Python 3.12+
- Git
- GitHub account (for automated hourly updates via Actions)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/anhdowastaken/hagezi-new-last-hour.git
cd hagezi-new-last-hour
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

Edit `config.yml` to specify which blocklist files to monitor:

```yaml
repository: hagezi/dns-blocklists

monitored_files:
  - domains/tif.txt
  - domains/pro.txt
  - domains/ultimate.txt
  # Add more files as needed
```

Available blocklist files can be found in the [Hagezi DNS Blocklists repository](https://github.com/hagezi/dns-blocklists).

### Usage

#### Run Locally

Execute the monitoring script:

```bash
python update_and_extract_new.py
```

For higher GitHub API rate limits, use a personal access token:

```bash
export GITHUB_TOKEN="your_github_token"
python update_and_extract_new.py
```

#### Automated Updates (GitHub Actions)

The workflow runs automatically every hour. You can also trigger it manually:

1. Go to the "Actions" tab in your GitHub repository
2. Select "Update New Records" workflow
3. Click "Run workflow"

### Output

New records are saved to files following the pattern:
```
[directory]/[filename]_NEW_last_hour.[extension]
```

**Examples:**
- Input: `domains/tif.txt` → Output: `domains/tif_NEW_last_hour.txt`
- Input: `domains/pro.txt` → Output: `domains/pro_NEW_last_hour.txt`

Each output file includes:
- Header with source file path
- Timestamp of last update
- Count of new records
- Sorted list of new additions

**Sample Output:**
```
# New records added to domains/tif.txt
# Last updated: 2025-12-25 14:00:00 UTC
# Total new records: 3

example-malicious-domain.com
phishing-site.net
spam-tracker.org
```

## How It Works

1. **GitHub API**: Fetches latest commit information without cloning the repository
2. **Commit Tracking**: Stores last processed commit SHA in `last_commit.txt`
3. **Content Comparison**: Downloads file content at both old and new commits
4. **Diff Calculation**: Identifies newly added records using set difference
5. **Output Generation**: Saves new records to timestamped files
6. **Auto-Commit**: Commits changes to track historical new additions

## File Structure

```
├── update_and_extract_new.py    # Main monitoring script
├── config.yml                   # Configuration file
├── requirements.txt             # Python dependencies
├── last_commit.txt              # Last processed commit (auto-generated)
├── domains/                     # Output directory
│   └── tif_NEW_last_hour.txt   # New records (auto-generated)
└── .github/
    └── workflows/
        └── update.yml           # GitHub Actions workflow
```

## Requirements

Dependencies are listed in `requirements.txt`:
- **GitPython**: Git operations and repository management
- **PyYAML**: Configuration file parsing
- **requests**: HTTP requests to GitHub API

## Getting Help

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/anhdowastaken/hagezi-new-last-hour/issues)
- **Hagezi Blocklists**: For questions about the blocklists themselves, visit the [Hagezi DNS Blocklists repository](https://github.com/hagezi/dns-blocklists)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- **[Hagezi](https://github.com/hagezi)**: For maintaining comprehensive DNS blocklists
- Blocklists sourced from [hagezi/dns-blocklists](https://github.com/hagezi/dns-blocklists)

## License

This project is open source and available for use. Please check the original [Hagezi DNS Blocklists repository](https://github.com/hagezi/dns-blocklists) for their licensing terms regarding the blocklist data.
