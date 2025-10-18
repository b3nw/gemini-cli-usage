# Gemini CLI Usage Monitor

A Gemini CLI extension that monitors your Google Cloud API usage and compares it against subscription plan limits.

## Overview

This extension provides a simple way to check your Google Cloud API usage directly from the Gemini CLI. It queries the Google Cloud Monitoring API to fetch your API request count and compares it against your subscription plan limits.

## Features

- 🔍 Query API usage for any Google Cloud project
- 📊 Compare usage against subscription plan limits (Free, Pro, Ultra, Standard, Enterprise)
- ⚡ Visual status indicators (OK, LOW, WARNING, OVER LIMIT)
- 📅 Automatic querying of the most recent complete UTC day
- 🔐 Secure authentication using Google Cloud Application Default Credentials

## Prerequisites

- Gemini CLI v0.8.2 or later
- Python 3.6 or later (included with most systems)
- A Google Cloud project with billing enabled
- Access to Google Cloud Monitoring API

**No pip packages, gcloud CLI, or system modifications required!** This extension uses only Python standard library and authenticates using your existing Gemini CLI credentials.

## Installation

Install directly from the git repository - no additional dependencies or setup required:

```bash
gemini extensions install https://github.com/yourusername/geminicli-usage.git
```

That's it! The extension is ready to use.

## Setup (First Time Only)

Before using the extension, you need to:

### 1. Authenticate with Gemini CLI

If you haven't already, authenticate with Gemini CLI:

```bash
gemini
```

Follow the prompts to sign in with your Google account. This creates authentication credentials that the extension will use.

### 2. Enable Cloud Monitoring API

The extension requires the Cloud Monitoring API to be enabled in your Google Cloud project. Enable it via the [Google Cloud Console](https://console.cloud.google.com/apis/library/monitoring.googleapis.com):

1. Visit the [Cloud Monitoring API page](https://console.cloud.google.com/apis/library/monitoring.googleapis.com)
2. Select your project
3. Click "Enable"

**Note**: Most Google Cloud APIs, including the Generative Language API, are not enabled by default and must be activated manually.

## Usage

⚠️ **Interactive mode only** - The extension works in interactive chat. The `-p` (prompt) flag currently has a known bug, likely related to Gemini CLI's MCP implementation, which causes the command to hang indefinitely.

Start Gemini CLI:

```bash
gemini
```

Then ask about your usage in natural language:

```
> Check my usage for project my-project-123 on the pro plan
```

The extension provides a `check_usage` tool that Gemini will automatically invoke.

### Example Prompts

```
> Check my usage for project my-project-123 on the pro plan
```

```
> What's my API usage for project my-gcp-project on the free plan?
```

```
> Show usage for project my-project, I'm on the ultra plan
```

```
> How many API requests have I used today for project my-company-project on the enterprise plan?
```

### Example Output

```
Gemini API Usage Report - 2025-10-17

Total Requests: 1,367

Plan: Google AI Pro
  Limit:     1,500 requests/day
  Used:      1,367 requests
  Remaining: 133 requests (8.9% available)
  Status:    ⚠️  WARNING

💡 Consider upgrading your plan if you frequently approach this limit.
```

**Tip:** Be specific in your prompts. Include both the project ID and plan type clearly.

### Available Plans

- `free`: 1,000 requests/day
- `pro`: 1,500 requests/day (Google AI Pro)
- `ultra`: 2,000 requests/day (Google AI Ultra)
- `standard`: 1,500 requests/day
- `enterprise`: 2,000 requests/day

### Status Indicators

The extension displays one of four status indicators based on your usage:

- **✓ OK**: Usage is below 75% of your daily limit (comfortable usage level)
- **⚡ LOW**: Usage is between 75% and 90% of your daily limit (approaching limit)
- **⚠️ WARNING**: Usage is between 90% and 100% of your daily limit (very close to limit)
- **❌ OVER LIMIT**: Usage has exceeded 100% of your daily limit (rate limiting may occur)

### Note on Time Range

The extension queries the last 7 days of data by default to ensure metrics are available. The report shows usage for the most recent complete day.

## Troubleshooting

### Extension Hangs or Times Out

**Problem**: Command hangs indefinitely with no response

**Solution**: Use **interactive mode only**. The `-p` (prompt) flag has a known bug, likely related to Gemini CLI's MCP implementation:

```bash
# ❌ Does not work - hangs indefinitely
gemini -p 'check my usage...'

# ✅ Works
gemini
> check my usage for project X on plan Y
```

This appears to be a bug in Gemini CLI's handling of MCP tool calls when using the `-p` flag, not a limitation of this extension.

### Authentication Errors

**Problem**: "Permission denied accessing project" or "Failed to get access token"

**Solutions**:
1. Ensure you've authenticated with Gemini CLI first by running `gemini` and following the sign-in prompts (this creates `~/.gemini/oauth_creds.json`)
2. Verify your project ID is correct
3. Check you have the required IAM role via the [Google Cloud Console IAM page](https://console.cloud.google.com/iam-admin/iam):
   - You need at least the `Monitoring Viewer` role (`roles/monitoring.viewer`)
   - Or any role that includes the `monitoring.timeSeries.list` permission

### API Not Enabled

**Problem**: "Cloud Monitoring API may not be enabled"

**Solution**: Enable the API via the [Google Cloud Console](https://console.cloud.google.com/apis/library/monitoring.googleapis.com):
1. Visit the [Cloud Monitoring API page](https://console.cloud.google.com/apis/library/monitoring.googleapis.com)
2. Select your project
3. Click "Enable"

The API is not enabled by default and must be activated manually for each project.

### No Data Found

**Problem**: Query returns 0 requests but you know you've made API calls

**Possible causes**:
1. The metric may not be available yet (monitoring data has a delay)
2. You're querying the wrong project ID
3. The API calls were made to a different service

**Solution**: 
- Wait a few minutes for metrics to populate (monitoring data has inherent delays)
- Verify your project ID is correct
- Check the [Google Cloud Console Monitoring page](https://console.cloud.google.com/monitoring) to see available metrics for your project


## Uninstallation

To remove the extension:

```bash
gemini extensions uninstall gemini-usage-monitor
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

Apache 2.0 - See LICENSE file for details

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the [Gemini CLI Extensions Documentation](https://google-gemini.github.io/gemini-cli/docs/extensions/)
- File an issue in the repository


