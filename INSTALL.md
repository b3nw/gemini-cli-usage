# Installation Guide

## Quick Install

Install the extension with a single command:

```bash
gemini extensions install https://github.com/b3nw/gemini-cli-usage.git
```

**That's it!** No pip packages, no gcloud CLI, no system modifications required.

## Prerequisites

The extension requires:

- **Gemini CLI** v0.8.2 or later
- **Python 3.6+** (standard on most systems)
- **A Google Cloud project** with billing enabled

If you can run `gemini`, you're ready to go! No gcloud CLI installation needed.

## First-Time Setup

After installation, complete these one-time setup steps:

### 1. Authenticate with Gemini CLI

If you haven't already, authenticate with Gemini CLI:

```bash
gemini
```

Follow the prompts to sign in with your Google account. This creates authentication credentials at `~/.gemini/oauth_creds.json` that the extension will use.

### 2. Enable Cloud Monitoring API

For each Google Cloud project you want to monitor, enable the Cloud Monitoring API via the [Google Cloud Console](https://console.cloud.google.com/apis/library/monitoring.googleapis.com):

1. Visit the [Cloud Monitoring API page](https://console.cloud.google.com/apis/library/monitoring.googleapis.com)
2. Select your project
3. Click "Enable"

**Note**: Most Google Cloud APIs are not enabled by default and must be activated manually.

### 3. Verify Installation

```bash
gemini extensions list
```

You should see `gemini-usage-monitor` version 2.0.0.

## Usage

⚠️ **Interactive mode only** - The `-p` (prompt) flag currently has a known bug, likely related to Gemini CLI's MCP implementation.

Start Gemini CLI and ask it to check your usage:

```bash
gemini
```

Then:
```
> Check my API usage for project my-project-123 on the free plan
```

## Updating

To update to the latest version:

```bash
gemini extensions update gemini-usage-monitor
```

## Uninstalling

To remove the extension:

```bash
gemini extensions uninstall gemini-usage-monitor
```

## Troubleshooting

### Installation Issues

**Problem**: "python3: command not found"

**Solution**: Install Python 3:
- **Debian/Ubuntu**: `sudo apt install python3`
- **macOS**: Pre-installed, or `brew install python3`

### Runtime Issues

**Problem**: Extension hangs with `-p` flag

**Solution**: Use interactive mode instead. The `-p` flag has a known bug with MCP tool calls:
```bash
# ❌ Does not work
gemini -p 'check my usage...'

# ✅ Works
gemini
> check my usage for project X on plan Y
```

**Problem**: "Failed to get access token"

**Solution**: Authenticate with Gemini CLI first:
```bash
gemini
```
Follow the prompts to sign in. This creates `~/.gemini/oauth_creds.json`.

**Problem**: "Permission denied accessing project"

**Solution**: Check you have the required IAM role via the [Google Cloud Console IAM page](https://console.cloud.google.com/iam-admin/iam):
- You need at least the `Monitoring Viewer` role (`roles/monitoring.viewer`)
- Or any role that includes the `monitoring.timeSeries.list` permission

**Problem**: "Cloud Monitoring API not enabled"

**Solution**: Enable the API via the [Google Cloud Console](https://console.cloud.google.com/apis/library/monitoring.googleapis.com):
1. Visit the [Cloud Monitoring API page](https://console.cloud.google.com/apis/library/monitoring.googleapis.com)
2. Select your project
3. Click "Enable"

### Extension Not Working

**Problem**: Extension appears in list but doesn't work

**Solution**:
1. Check Python version: `python3 --version` (should be 3.6+)
2. Check Gemini CLI authentication: Run `gemini` and ensure you can authenticate
3. Reinstall: `gemini extensions uninstall gemini-usage-monitor` then install again

## Local Development

For development or testing local changes:

```bash
# Clone the repository
git clone https://github.com/yourusername/geminicli-usage.git
cd geminicli-usage

# Link for development (changes reflect immediately)
gemini extensions link .
```

Edit files, and Gemini CLI will use your local version automatically.

## Requirements Details

### Why No pip Packages?

This extension uses **only Python standard library** to avoid dependency issues. It makes direct HTTP calls to Google Cloud APIs using built-in `urllib`.

### Why No gcloud CLI?

The extension uses Gemini CLI's existing OAuth credentials (stored at `~/.gemini/oauth_creds.json`) to authenticate with Google Cloud APIs. No separate gcloud CLI installation is required.

### Supported Platforms

- ✅ Linux (including WSL2)
- ✅ macOS
- ✅ Any platform with Python 3.6+ and gcloud CLI

## Security

The extension:
- Does NOT store credentials
- Uses your existing gcloud authentication
- Makes read-only API calls
- Runs locally on your machine
- Source code is fully auditable

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review the [README](README.md)
3. Check [Gemini CLI Extensions Documentation](https://google-gemini.github.io/gemini-cli/docs/extensions/)
4. File an issue in the repository

## Version History

- **v2.0.0** (2025-10-18): Initial release
  - Zero-dependency implementation
  - Five subscription plans supported
  - MCP server architecture
  - Direct Google Cloud API integration
