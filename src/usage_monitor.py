#!/usr/bin/env python3
"""
Gemini CLI Usage Monitor Extension - Zero Dependencies Version

This implementation uses only Python standard library to avoid
requiring any external dependencies or system modifications.
"""

import sys
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse


def log(message):
    """Log to stderr."""
    print(f"[usage_monitor] {message}", file=sys.stderr, flush=True)


def get_access_token():
    """
    Get Google Cloud access token from gemini-cli's stored OAuth credentials.
    Gemini CLI stores credentials in ~/.gemini/oauth_creds.json
    """
    import os
    import time
    from urllib.parse import urlencode
    
    # Path to gemini CLI OAuth credentials
    gemini_dir = os.path.expanduser("~/.gemini")
    creds_file = os.path.join(gemini_dir, "oauth_creds.json")
    
    if not os.path.exists(creds_file):
        raise Exception(
            "Gemini CLI credentials not found. Please run 'gemini' first to authenticate."
        )
    
    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        
        access_token = creds.get('access_token')
        expiry_date = creds.get('expiry_date')
        refresh_token = creds.get('refresh_token')
        
        if not access_token:
            raise Exception("No access token found in credentials")
        
        # Check if token is expired (expiry_date is in milliseconds)
        if expiry_date:
            expiry_seconds = expiry_date / 1000
            if time.time() >= expiry_seconds:
                # Token expired, try to refresh
                if refresh_token:
                    log("Access token expired, refreshing...")
                    return refresh_access_token(refresh_token, creds_file)
                else:
                    raise Exception(
                        "Access token expired and no refresh token available. "
                        "Please run 'gemini' to re-authenticate."
                    )
        
        return access_token
        
    except json.JSONDecodeError:
        raise Exception("Invalid credentials file format")
    except Exception as e:
        raise Exception(f"Failed to read credentials: {e}")


def refresh_access_token(refresh_token, creds_file):
    """Refresh the access token using the refresh token."""
    # Google OAuth2 token endpoint
    token_url = "https://oauth2.googleapis.com/token"
    
    # Client ID for Google OAuth (public client)
    client_id = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"
    
    data = {
        'client_id': client_id,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        request = Request(
            token_url,
            data=urlencode(data).encode('utf-8'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            new_access_token = result.get('access_token')
            expires_in = result.get('expires_in', 3600)
            
            if not new_access_token:
                raise Exception("No access token in refresh response")
            
            # Update the credentials file with new token
            try:
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                
                creds['access_token'] = new_access_token
                creds['expiry_date'] = int((time.time() + expires_in) * 1000)
                
                with open(creds_file, 'w') as f:
                    json.dump(creds, f, indent=2)
                
                log("Access token refreshed successfully")
            except Exception as e:
                log(f"Warning: Could not update credentials file: {e}")
            
            return new_access_token
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Failed to refresh token: {error_body}")
    except URLError as e:
        raise Exception(f"Network error refreshing token: {e.reason}")


def get_previous_day_range():
    """Get the start and end time for a time range (last 7 days for now)."""
    now = datetime.now(timezone.utc)
    
    # Query last 7 days instead of just yesterday (more likely to have data)
    end_time = now
    start_time = now - timedelta(days=7)
    
    # Format for MQL: RFC3339 format
    start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Get the date for display
    display_date = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    return start_str, end_str, display_date


def query_monitoring_api(project_id, start_time, end_time, access_token):
    """
    Query Google Cloud Monitoring API using listTimeSeries.
    Returns total request count.
    """
    from urllib.parse import urlencode
    
    #  Use listTimeSeries API instead of MQL
    params = {
        'filter': f'metric.type="serviceruntime.googleapis.com/api/request_count" AND resource.labels.project_id="{project_id}"',
        'interval.startTime': start_time,
        'interval.endTime': end_time,
        'aggregation.alignmentPeriod': '604800s',  # 7 days in seconds
        'aggregation.perSeriesAligner': 'ALIGN_SUM'
    }
    
    url = f"https://monitoring.googleapis.com/v3/projects/{project_id}/timeSeries?{urlencode(params)}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    request = Request(url, headers=headers, method='GET')
    
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Parse the response to get total requests
            total_requests = 0
            if 'timeSeries' in result:
                for ts in result['timeSeries']:
                    if 'points' in ts:
                        for point in ts['points']:
                            if 'value' in point:
                                value = point['value']
                                if 'int64Value' in value:
                                    total_requests += int(value['int64Value'])
                                elif 'doubleValue' in value:
                                    total_requests += int(value['doubleValue'])
            
            return total_requests
            
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        if e.code == 403:
            raise Exception(
                f"Permission denied accessing project '{project_id}'.\n"
                "Ensure you have the 'monitoring.viewer' role or equivalent."
            )
        elif e.code == 404:
            raise Exception(
                f"Project '{project_id}' not found. Please verify the project ID."
            )
        elif e.code == 400:
            if 'API' in error_body and 'disabled' in error_body.lower():
                raise Exception(
                    f"Cloud Monitoring API not enabled for project '{project_id}'.\n"
                    "Enable it at: https://console.cloud.google.com/apis/library/monitoring.googleapis.com"
                )
        raise Exception(f"API error ({e.code}): {error_body}")
    except URLError as e:
        raise Exception(f"Network error: {e.reason}")


def get_plan_info(plan_type):
    """Get plan information."""
    plans = {
        "free": {"limit": 1000, "label": "Free"},
        "pro": {"limit": 1500, "label": "Google AI Pro"},
        "ultra": {"limit": 2000, "label": "Google AI Ultra"},
        "standard": {"limit": 1500, "label": "Standard"},
        "enterprise": {"limit": 2000, "label": "Enterprise"}
    }
    return plans.get(plan_type.lower())


def format_report(total_requests, plan_type, date_str):
    """Format the usage report."""
    plan = get_plan_info(plan_type)
    if not plan:
        available = ", ".join(["free", "pro", "ultra", "standard", "enterprise"])
        return f"Error: Invalid plan type '{plan_type}'. Available: {available}"
    
    limit = plan["limit"]
    label = plan["label"]
    remaining = limit - total_requests
    percentage = (remaining / limit) * 100 if limit > 0 else 0
    
    # Determine status
    if remaining < 0:
        status = "⚠️  OVER LIMIT"
        percentage = 0
    elif percentage < 10:
        status = "⚠️  WARNING"
    elif percentage < 25:
        status = "⚡ LOW"
    else:
        status = "✓ OK"
    
    report = f"""
Gemini API Usage Report - {date_str}

Total Requests: {total_requests:,}

Plan: {label}
  Limit:     {limit:,} requests/day
  Used:      {total_requests:,} requests
  Remaining: {remaining:,} requests ({percentage:.1f}% available)
  Status:    {status}
"""
    
    if remaining < 0:
        report += f"\n⚠️  You have exceeded your daily limit by {abs(remaining):,} requests!"
    elif percentage < 25:
        report += f"\n💡 Consider upgrading your plan if you frequently approach this limit."
    
    return report.strip()


def handle_mcp_request(request):
    """Handle MCP protocol request."""
    method = request.get("method")
    
    # Handle notifications (no response needed)
    if method and method.startswith("notifications/"):
        return None  # No response for notifications
    
    if method == "initialize":
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "gemini-usage-monitor",
                    "version": "2.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "result": {
                "tools": [
                    {
                        "name": "check_usage",
                        "description": (
                            "Check Google Cloud API usage against subscription plan limits. "
                            "Retrieves total API request count for the most recent complete UTC day."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "project_id": {
                                    "type": "string",
                                    "description": "Google Cloud Project ID"
                                },
                                "plan": {
                                    "type": "string",
                                    "enum": ["free", "pro", "ultra", "standard", "enterprise"],
                                    "description": "Subscription plan type"
                                }
                            },
                            "required": ["project_id", "plan"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})
        
        if tool_name != "check_usage":
            return {"error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
        
        project_id = arguments.get("project_id")
        plan = arguments.get("plan")
        
        if not project_id or not plan:
            return {
                "error": {
                    "code": -32602,
                    "message": "Missing required parameters: project_id and plan"
                }
            }
        
        try:
            log(f"Checking usage for project: {project_id}, plan: {plan}")
            
            # Get access token
            access_token = get_access_token()
            
            # Get time range
            start_time, end_time, date_str = get_previous_day_range()
            
            # Query the API
            total_requests = query_monitoring_api(
                project_id, start_time, end_time, access_token
            )
            
            log(f"Total requests: {total_requests}")
            
            # Format report
            report = format_report(total_requests, plan, date_str)
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": report
                        }
                    ]
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            log(f"Error: {error_msg}")
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error checking usage: {error_msg}"
                        }
                    ]
                }
            }
    
    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    """Main MCP server loop."""
    log("Starting Gemini Usage Monitor (zero-dependency version)")

    # Check if running in a non-interactive session (e.g., with -p flag)
    is_non_interactive = not sys.stdin.isatty()
    if is_non_interactive:
        log("Running in non-interactive mode. Will process one request and exit.")

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                method = request.get("method", "unknown")
                log(f"Received: {method}")

                response = handle_mcp_request(request)

                # Only send response if we have one and request had an id
                if response is not None and "id" in request:
                    # Add jsonrpc version and request ID
                    response["jsonrpc"] = "2.0"
                    response["id"] = request["id"]

                    # Send response
                    print(json.dumps(response), flush=True)

                    # If in non-interactive mode, exit after the first valid response
                    if is_non_interactive:
                        log("Request processed in non-interactive mode. Exiting.")
                        break  # Exit loop

                elif response is None:
                    log(f"Notification handled, no response")

            except json.JSONDecodeError as e:
                log(f"JSON decode error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                }
                print(json.dumps(error_response), flush=True)
                if is_non_interactive:
                    break  # Exit loop

        log("MCP server loop finished.")

    except KeyboardInterrupt:
        log("Server stopped by user")
    except Exception as e:
        log(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

