# controld-mcp

An MCP server that wraps the [Control D](https://controld.com) REST API
(`https://api.controld.com`), so an MCP-capable client (Claude Code, Claude
Desktop, etc.) can manage profiles, devices, filters, custom DNS rules, and
known IPs on a Control D account.

## Important limitation: no query-log / analytics data

Control D's public API does **not** expose DNS query logs, per-domain traffic
counts, blocked-request history, or any other activity/report data. It only
exposes the analytics *settings* (log level, storage region) via `GET
/analytics`. This server can therefore tell you things like "what profiles,
filters, and devices are configured" and "what IPs have queried a device
recently" (via `/access/ip`), but it **cannot** answer "show me anomalies in
my DNS traffic over the last N hours" — that data isn't in the API today.

For real query-log-based anomaly detection, use the Control D dashboard's
Analytics / Activity Log / Reports pages (CSV export), or watch for an
official log-export/webhook feature to ship.

## Setup

1. **Generate an API token** in the Control D dashboard at
   https://controld.com/dashboard/api. Choose:
   - **Read** scope if you only want to list profiles/devices/filters/IPs.
   - **Write** scope if you also want to create/update/delete profiles,
     rules, devices, or IP entries via this server.

   You can optionally restrict the token to specific source IPs.

2. **Install dependencies**:
   ```bash
   cd controld-mcp
   pip install -r requirements.txt
   ```

3. **Set the token** as an environment variable:
   ```bash
   export CONTROLD_API_KEY="your_token_here"
   ```
   Never hardcode the token in source, and never paste it into a chat message.

4. **Register the server with Claude Code**:
   ```bash
   claude mcp add controld-mcp \
     --env CONTROLD_API_KEY="your_token_here" \
     -- python /absolute/path/to/controld-mcp/controld_mcp.py
   ```
   Or add it to `.mcp.json` / `claude_desktop_config.json` directly:
   ```json
   {
     "mcpServers": {
       "controld-mcp": {
         "command": "python",
         "args": ["/absolute/path/to/controld-mcp/controld_mcp.py"],
         "env": { "CONTROLD_API_KEY": "your_token_here" }
       }
     }
   }
   ```

5. Restart your MCP client. Tools will appear prefixed `controld_...`.

## Tools

Read-only:
- `controld_get_account_info`
- `controld_list_organizations` / `controld_list_organization_members`
- `controld_list_profiles`
- `controld_get_profile_filters` / `controld_get_profile_services` / `controld_get_profile_custom_rules`
- `controld_list_devices` / `controld_list_device_types`
- `controld_list_known_ips` / `controld_list_device_recent_ips`
- `controld_get_analytics_settings` (settings only — see limitation above)
- `controld_list_service_catalog`
- `controld_get_caller_ip`

Mutating (require a Write-scoped token **and** `confirm=true`):
- `controld_toggle_profile_filter`
- `controld_manage_custom_rule` (add/update/delete a hostname rule)
- `controld_manage_device` (create/update/delete a device)
- `controld_delete_known_ip`

Every mutating tool refuses to call the API unless `confirm=true` is passed
explicitly, so nothing destructive happens by accident.

## Testing locally

```bash
python -m py_compile controld_mcp.py   # syntax check
npx @modelcontextprotocol/inspector python controld_mcp.py   # interactive testing
```

## Security notes

- The API token is read only from the `CONTROLD_API_KEY` environment
  variable — it is never logged or echoed back in tool output.
- 401/403/404/429 responses are translated into actionable error messages
  instead of raw stack traces.
- Destructive/mutating tools are annotated `destructiveHint: true` and
  require an explicit `confirm=true` argument.
