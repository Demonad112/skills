#!/usr/bin/env python3
"""
MCP Server for the Control D REST API (https://api.controld.com).

Wraps profile, device (endpoint), filter, service, custom-rule, access-IP,
organization, and account operations. Control D's public API does NOT expose
DNS query logs, blocked-domain stats, or activity/report data (as of the
Control D docs current at the time this server was written) -- only the
*settings* for analytics logging (level, storage region) are exposed. Tools
that touch analytics say this explicitly so a model doesn't hallucinate
query-log data the API can't provide.
"""

import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

mcp = FastMCP("controld_mcp")

API_BASE_URL = "https://api.controld.com"
API_TOKEN_ENV_VAR = "CONTROLD_API_KEY"


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


def _get_token() -> str:
    token = os.environ.get(API_TOKEN_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Missing API token. Set the {API_TOKEN_ENV_VAR} environment variable "
            "to a token generated at https://controld.com/dashboard/api "
            "('Read' scope is enough for the get_/list_ tools; 'Write' scope is "
            "required for create/update/delete tools)."
        )
    return token


async def _request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Reusable authenticated request against the Control D API."""
    token = _get_token()
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            params=params,
            json=json_body,
            timeout=30.0,
        )
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()


def _handle_api_error(e: Exception, resource_hint: str = "resource") -> str:
    """Consistent, actionable error formatting across all tools."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return (
                "Error: Invalid or missing API authentication. Check that "
                f"{API_TOKEN_ENV_VAR} is set to a valid token from "
                "https://controld.com/dashboard/api."
            )
        if status == 403:
            return (
                "Error: Permission denied. This token may be 'Read'-scoped; "
                "mutating operations require a 'Write'-scoped token."
            )
        if status == 404:
            return f"Error: {resource_hint.capitalize()} not found. Check the ID is correct."
        if status == 429:
            retry_after = e.response.headers.get("Retry-After")
            suffix = f" Retry after {retry_after}s." if retry_after else ""
            return f"Error: Rate limit exceeded.{suffix} Wait before making more requests."
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text
        return f"Error: API request failed with status {status}: {body}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request to Control D API timed out. Please try again."
    if isinstance(e, RuntimeError):
        return f"Error: {e}"
    return f"Error: Unexpected error occurred: {type(e).__name__}: {e}"


def _format(data: Any, response_format: ResponseFormat, title: str) -> str:
    if response_format == ResponseFormat.JSON:
        return json.dumps(data, indent=2)
    lines = [f"# {title}", ""]
    lines.append("```json")
    lines.append(json.dumps(data, indent=2))
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Account / Organization
# ---------------------------------------------------------------------------


class NoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="controld_get_account_info",
    annotations={
        "title": "Get Control D Account Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_account_info(params: NoInput) -> str:
    """Get the current Control D account/user info for the authenticated API token.

    Args:
        params (NoInput): Only a response_format field.

    Returns:
        str: Account info (email, plan, account id, etc.) as markdown or JSON.

    Error Handling:
        - "Error: Invalid or missing API authentication" if the token is missing/invalid.
    """
    try:
        data = await _request("GET", "/users")
        return _format(data, params.response_format, "Control D Account Info")
    except Exception as e:
        return _handle_api_error(e, "account")


@mcp.tool(
    name="controld_list_organizations",
    annotations={
        "title": "List Control D Organizations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_organizations(params: NoInput) -> str:
    """List organizations (and sub-organizations) the authenticated account belongs to.

    Only relevant for Control D Organizations/MSP accounts; personal accounts
    will return an empty or minimal list.

    Args:
        params (NoInput): Only a response_format field.

    Returns:
        str: List of organizations as markdown or JSON.
    """
    try:
        data = await _request("GET", "/organizations")
        return _format(data, params.response_format, "Control D Organizations")
    except Exception as e:
        return _handle_api_error(e, "organization")


class OrgMembersInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: str = Field(..., description="Organization ID (e.g. 'org_123')", min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_list_organization_members",
    annotations={
        "title": "List Control D Organization Members",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_organization_members(params: OrgMembersInput) -> str:
    """List members of a Control D organization.

    Args:
        params (OrgMembersInput): organization_id (str) and response_format.

    Returns:
        str: List of org members as markdown or JSON.

    Error Handling:
        - "Error: Organization not found" if the organization_id is wrong.
    """
    try:
        data = await _request("GET", f"/organizations/{params.organization_id}/members")
        return _format(data, params.response_format, f"Members of Organization {params.organization_id}")
    except Exception as e:
        return _handle_api_error(e, "organization")


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


class ListProfilesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_list_profiles",
    annotations={
        "title": "List Control D Profiles",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_profiles(params: ListProfilesInput) -> str:
    """List all DNS filtering profiles (policies) on the account.

    A profile bundles filters, services, and custom rules that get applied to
    one or more devices/endpoints. Use the returned profile "PK" (profile id)
    with other controld_profile_* / controld_*_filters / controld_*_rules tools.

    Args:
        params (ListProfilesInput): Only a response_format field.

    Returns:
        str: JSON array of profiles (id, name, updated_at, etc.) as markdown or JSON.

    Examples:
        - Use when: "What DNS profiles do I have configured?"
        - Don't use when: You need device-level info (use controld_list_devices instead).
    """
    try:
        data = await _request("GET", "/profiles")
        return _format(data, params.response_format, "Control D Profiles")
    except Exception as e:
        return _handle_api_error(e, "profile")


class ProfileIdInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(..., description="Profile ID/PK (e.g. from controld_list_profiles)", min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_get_profile_filters",
    annotations={
        "title": "Get Filters Enabled on a Control D Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_profile_filters(params: ProfileIdInput) -> str:
    """List the native filter categories (malware, ads, adult, etc.) enabled/disabled
    on a given profile, plus any external filter lists attached to it.

    Args:
        params (ProfileIdInput): profile_id (str) and response_format.

    Returns:
        str: Filters + external filter lists for the profile, as markdown or JSON.

    Error Handling:
        - "Error: Resource not found" if profile_id is invalid.
    """
    try:
        filters = await _request("GET", f"/profiles/{params.profile_id}/filters")
        external = await _request("GET", f"/profiles/{params.profile_id}/filters/external")
        data = {"filters": filters, "external_filters": external}
        return _format(data, params.response_format, f"Filters for Profile {params.profile_id}")
    except Exception as e:
        return _handle_api_error(e, "profile")


@mcp.tool(
    name="controld_get_profile_services",
    annotations={
        "title": "Get Services Enabled on a Control D Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_profile_services(params: ProfileIdInput) -> str:
    """List the app/service blocks (e.g. TikTok, Instagram) configured on a profile.

    Args:
        params (ProfileIdInput): profile_id (str) and response_format.

    Returns:
        str: Services configured on the profile, as markdown or JSON.
    """
    try:
        data = await _request("GET", f"/profiles/{params.profile_id}/services")
        return _format(data, params.response_format, f"Services for Profile {params.profile_id}")
    except Exception as e:
        return _handle_api_error(e, "profile")


@mcp.tool(
    name="controld_get_profile_custom_rules",
    annotations={
        "title": "Get Custom Rules and Rule Folders on a Control D Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_profile_custom_rules(params: ProfileIdInput) -> str:
    """List custom rule folders (groups) on a profile. To see the individual
    hostname rules inside a specific folder, call the Control D dashboard or
    use a folder-scoped follow-up once folder IDs are known (this server does
    not expose folder-content listing to keep the tool surface small; use
    controld_manage_custom_rule to add/update/delete individual hostname rules).

    Args:
        params (ProfileIdInput): profile_id (str) and response_format.

    Returns:
        str: Rule folders for the profile, as markdown or JSON.
    """
    try:
        data = await _request("GET", f"/profiles/{params.profile_id}/groups")
        return _format(data, params.response_format, f"Rule Folders for Profile {params.profile_id}")
    except Exception as e:
        return _handle_api_error(e, "profile")


class ToggleFilterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(..., description="Profile ID/PK to modify", min_length=1)
    filter_name: str = Field(..., description="Filter identifier (e.g. 'ads', 'malware') from controld_get_profile_filters", min_length=1)
    enabled: bool = Field(..., description="True to enable this filter, False to disable it")
    confirm: bool = Field(
        ..., description="Must be explicitly set to true to confirm you intend to change a live filtering rule"
    )


@mcp.tool(
    name="controld_toggle_profile_filter",
    annotations={
        "title": "Enable/Disable a Filter on a Control D Profile",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_toggle_profile_filter(params: ToggleFilterInput) -> str:
    """Enable or disable a single native filter category on a profile. This
    changes live DNS filtering behavior for every device using this profile.

    Requires a 'Write'-scoped API token and confirm=true.

    Args:
        params (ToggleFilterInput): profile_id, filter_name, enabled, confirm (must be True).

    Returns:
        str: "Success: ..." message or an "Error: ..." message.

    Error Handling:
        - Returns an error immediately (no API call) if confirm is not True.
        - "Error: Permission denied" if the token lacks Write scope.
    """
    if not params.confirm:
        return (
            "Error: This is a mutating operation. Re-call with confirm=true to actually "
            f"{'enable' if params.enabled else 'disable'} filter '{params.filter_name}' "
            f"on profile {params.profile_id}."
        )
    try:
        await _request(
            "PUT",
            f"/profiles/{params.profile_id}/filters/{params.filter_name}",
            json_body={"status": 1 if params.enabled else 0},
        )
        state = "enabled" if params.enabled else "disabled"
        return f"Success: filter '{params.filter_name}' {state} on profile {params.profile_id}."
    except Exception as e:
        return _handle_api_error(e, "profile filter")


class ManageCustomRuleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(..., description="Profile ID/PK to modify", min_length=1)
    action: str = Field(..., description="One of: 'add', 'update', 'delete'")
    hostname: str = Field(..., description="Hostname the custom rule applies to (e.g. 'ads.example.com')", min_length=1)
    do: Optional[int] = Field(
        default=None,
        description="Action code for add/update (e.g. block vs redirect); required for add/update, per Control D rule 'do' field",
    )
    group_id: Optional[str] = Field(default=None, description="Rule folder/group ID to place the rule in, if any")
    confirm: bool = Field(..., description="Must be explicitly set to true to confirm this change to live DNS rules")


@mcp.tool(
    name="controld_manage_custom_rule",
    annotations={
        "title": "Add, Update, or Delete a Custom DNS Rule on a Profile",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def controld_manage_custom_rule(params: ManageCustomRuleInput) -> str:
    """Add, update, or delete a single custom hostname rule on a profile
    (e.g. block or redirect a specific domain). This changes live DNS
    resolution for every device using this profile.

    Requires a 'Write'-scoped API token and confirm=true.

    Args:
        params (ManageCustomRuleInput): profile_id, action ('add'/'update'/'delete'),
            hostname, optional do/group_id, confirm (must be True).

    Returns:
        str: "Success: ..." message or an "Error: ..." message.

    Error Handling:
        - Returns an error immediately if confirm is not True or action is invalid.
        - "Error: Permission denied" if the token lacks Write scope.
    """
    if not params.confirm:
        return f"Error: This is a mutating operation. Re-call with confirm=true to {params.action} rule for '{params.hostname}'."
    try:
        if params.action == "add":
            body: Dict[str, Any] = {"hostname": params.hostname}
            if params.do is not None:
                body["do"] = params.do
            if params.group_id is not None:
                body["group"] = params.group_id
            await _request("POST", f"/profiles/{params.profile_id}/rules", json_body=body)
            return f"Success: added rule for '{params.hostname}' on profile {params.profile_id}."
        elif params.action == "update":
            body = {"hostname": params.hostname}
            if params.do is not None:
                body["do"] = params.do
            if params.group_id is not None:
                body["group"] = params.group_id
            await _request("PUT", f"/profiles/{params.profile_id}/rules", json_body=body)
            return f"Success: updated rule for '{params.hostname}' on profile {params.profile_id}."
        elif params.action == "delete":
            await _request("DELETE", f"/profiles/{params.profile_id}/rules/{params.hostname}")
            return f"Success: deleted rule for '{params.hostname}' on profile {params.profile_id}."
        else:
            return "Error: action must be one of 'add', 'update', 'delete'."
    except Exception as e:
        return _handle_api_error(e, "custom rule")


# ---------------------------------------------------------------------------
# Devices / Endpoints
# ---------------------------------------------------------------------------


class ListDevicesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_list_devices",
    annotations={
        "title": "List Control D Devices (Endpoints)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_devices(params: ListDevicesInput) -> str:
    """List all devices/endpoints (DNS resolvers) registered on the account,
    including which profile each is bound to and its resolver metadata.

    This is the closest thing to a "what's connected" view available via the
    public API. It does NOT include per-query traffic or query logs (see
    controld_get_analytics_settings for why).

    Args:
        params (ListDevicesInput): Only a response_format field.

    Returns:
        str: JSON array of devices/endpoints as markdown or JSON.

    Examples:
        - Use when: "What devices are set up on my Control D account?"
        - Don't use when: You want DNS query history/anomalies (not available via API).
    """
    try:
        data = await _request("GET", "/endpoints")
        return _format(data, params.response_format, "Control D Devices (Endpoints)")
    except Exception as e:
        return _handle_api_error(e, "device")


@mcp.tool(
    name="controld_list_device_types",
    annotations={
        "title": "List Control D Device/Endpoint Types",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_device_types(params: ListDevicesInput) -> str:
    """List the available endpoint types (e.g. router, app, DoH client) that
    can be used when creating a new device.

    Args:
        params (ListDevicesInput): Only a response_format field.

    Returns:
        str: JSON array of endpoint types as markdown or JSON.
    """
    try:
        data = await _request("GET", "/endpoints/types")
        return _format(data, params.response_format, "Control D Endpoint Types")
    except Exception as e:
        return _handle_api_error(e, "device type")


class ManageDeviceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(..., description="One of: 'create', 'update', 'delete'")
    device_id: Optional[str] = Field(default=None, description="Device/endpoint ID; required for update/delete")
    name: Optional[str] = Field(default=None, description="Device name; required for create")
    profile_id: Optional[str] = Field(default=None, description="Profile ID to bind the device to")
    confirm: bool = Field(..., description="Must be explicitly set to true to confirm this change")


@mcp.tool(
    name="controld_manage_device",
    annotations={
        "title": "Create, Update, or Delete a Control D Device",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def controld_manage_device(params: ManageDeviceInput) -> str:
    """Create, update, or delete a device/endpoint on the account.

    Requires a 'Write'-scoped API token and confirm=true. Deleting a device
    that is actively resolving DNS for a machine will break its DNS resolution
    until reconfigured.

    Args:
        params (ManageDeviceInput): action ('create'/'update'/'delete'), device_id
            (for update/delete), name (for create), optional profile_id, confirm.

    Returns:
        str: "Success: ..." message or an "Error: ..." message.

    Error Handling:
        - Returns an error immediately if confirm is not True.
        - "Error: Resource not found" if device_id is invalid for update/delete.
    """
    if not params.confirm:
        return f"Error: This is a mutating operation. Re-call with confirm=true to {params.action} this device."
    try:
        if params.action == "create":
            if not params.name:
                return "Error: name is required to create a device."
            body: Dict[str, Any] = {"name": params.name}
            if params.profile_id:
                body["profile"] = {"PK": params.profile_id}
            data = await _request("POST", "/endpoints", json_body=body)
            return f"Success: created device '{params.name}'.\n{json.dumps(data, indent=2)}"
        elif params.action == "update":
            if not params.device_id:
                return "Error: device_id is required to update a device."
            body = {}
            if params.name:
                body["name"] = params.name
            if params.profile_id:
                body["profile"] = {"PK": params.profile_id}
            await _request("PUT", f"/endpoints/{params.device_id}", json_body=body)
            return f"Success: updated device {params.device_id}."
        elif params.action == "delete":
            if not params.device_id:
                return "Error: device_id is required to delete a device."
            await _request("DELETE", f"/endpoints/{params.device_id}")
            return f"Success: deleted device {params.device_id}."
        else:
            return "Error: action must be one of 'create', 'update', 'delete'."
    except Exception as e:
        return _handle_api_error(e, "device")


# ---------------------------------------------------------------------------
# Access IPs
# ---------------------------------------------------------------------------


class ListKnownIpsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_list_known_ips",
    annotations={
        "title": "List Known/Learned Source IPs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_known_ips(params: ListKnownIpsInput) -> str:
    """List IP addresses Control D has learned/associated with devices on the
    account. This is the closest built-in signal for spotting a new/unexpected
    source IP querying your resolver (a useful "flip" or anomaly signal), but
    it is a snapshot of known IPs, not a timestamped query log.

    Args:
        params (ListKnownIpsInput): Only a response_format field.

    Returns:
        str: JSON array of known IPs as markdown or JSON.

    Examples:
        - Use when: "Has a new IP started using my Control D resolver?"
        - Don't use when: You need exact query timestamps/anomaly counts (not exposed by the API).
    """
    try:
        data = await _request("GET", "/access/ip")
        return _format(data, params.response_format, "Known/Learned IPs")
    except Exception as e:
        return _handle_api_error(e, "IP list")


class DeviceRecentIpsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: str = Field(..., description="Device/endpoint ID to check", min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


@mcp.tool(
    name="controld_list_device_recent_ips",
    annotations={
        "title": "List Recent Source IPs for a Device",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_device_recent_ips(params: DeviceRecentIpsInput) -> str:
    """List up to the latest 50 source IPs that queried a specific device's
    resolver. Useful for spotting an unexpected/new IP hitting a device.

    Args:
        params (DeviceRecentIpsInput): device_id (str) and response_format.

    Returns:
        str: Up to 50 recent source IPs for the device, as markdown or JSON.

    Error Handling:
        - "Error: Resource not found" if device_id is invalid.
    """
    try:
        data = await _request("POST", f"/access/ip/{params.device_id}")
        return _format(data, params.response_format, f"Recent IPs for Device {params.device_id}")
    except Exception as e:
        return _handle_api_error(e, "device")


class DeleteKnownIpInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ip_id: str = Field(..., description="ID of the learned IP entry to remove (from controld_list_known_ips)", min_length=1)
    confirm: bool = Field(..., description="Must be explicitly set to true to confirm removal")


@mcp.tool(
    name="controld_delete_known_ip",
    annotations={
        "title": "Delete a Learned IP Entry",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_delete_known_ip(params: DeleteKnownIpInput) -> str:
    """Remove a previously-learned IP entry from the account's known IP list.

    Requires a 'Write'-scoped API token and confirm=true.

    Args:
        params (DeleteKnownIpInput): ip_id (str), confirm (must be True).

    Returns:
        str: "Success: ..." message or an "Error: ..." message.
    """
    if not params.confirm:
        return f"Error: This is a destructive operation. Re-call with confirm=true to delete learned IP {params.ip_id}."
    try:
        await _request("DELETE", f"/access/ip/{params.ip_id}")
        return f"Success: deleted learned IP entry {params.ip_id}."
    except Exception as e:
        return _handle_api_error(e, "IP entry")


# ---------------------------------------------------------------------------
# Analytics settings (NOT query logs)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="controld_get_analytics_settings",
    annotations={
        "title": "Get Control D Analytics Log Settings (Not Query Logs)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_analytics_settings(params: NoInput) -> str:
    """Get the account's analytics logging LEVEL and storage REGION settings
    (e.g. "no logs" vs "logs with client IP" vs "logs without client IP", and
    which region logs are stored in).

    IMPORTANT LIMITATION: Control D's public REST API does NOT expose actual
    DNS query logs, per-domain traffic counts, blocked-request lists, or any
    other activity/report data -- only these logging *settings* are available
    here. There is no API-based way to detect DNS query anomalies, spikes, or
    "flips" in blocking behavior through this endpoint. For real query-level
    monitoring, use the Control D dashboard's Analytics/Activity Log/Reports
    pages directly (CSV export), or check whether your plan supports a
    webhook/log-export integration for real-time delivery.

    Args:
        params (NoInput): Only a response_format field.

    Returns:
        str: Analytics settings (log level, storage region) as markdown or JSON.

    Examples:
        - Use when: "What's my current DNS logging level set to?"
        - Don't use when: "Show me anomalies in my DNS query traffic" -- this
          tool cannot answer that; say so rather than fabricating data.
    """
    try:
        data = await _request("GET", "/analytics")
        result = {
            "analytics_settings": data,
            "note": (
                "This is only the logging level/storage region configuration. "
                "The Control D public API does not expose query logs, traffic "
                "stats, or blocked-domain data. Use the Control D dashboard for that."
            ),
        }
        return _format(result, params.response_format, "Control D Analytics Settings")
    except Exception as e:
        return _handle_api_error(e, "analytics settings")


# ---------------------------------------------------------------------------
# Services (catalog) and misc
# ---------------------------------------------------------------------------


@mcp.tool(
    name="controld_list_service_catalog",
    annotations={
        "title": "List Control D Service Catalog",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_list_service_catalog(params: NoInput) -> str:
    """List all app/service categories and individual services (e.g. social
    media, gaming) that can be blocked on a profile via controld_toggle... style
    operations. This is the reference catalog, not a per-profile status.

    Args:
        params (NoInput): Only a response_format field.

    Returns:
        str: Full service catalog as markdown or JSON.
    """
    try:
        data = await _request("GET", "/services")
        return _format(data, params.response_format, "Control D Service Catalog")
    except Exception as e:
        return _handle_api_error(e, "service catalog")


@mcp.tool(
    name="controld_get_caller_ip",
    annotations={
        "title": "Get Caller's Public IP (as seen by Control D)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def controld_get_caller_ip(params: NoInput) -> str:
    """Return the public IP address that Control D's API sees this request
    coming from. Useful for confirming what IP a script/server making these
    calls will appear as.

    Args:
        params (NoInput): Only a response_format field.

    Returns:
        str: Caller's IP info as markdown or JSON.
    """
    try:
        data = await _request("GET", "/ip")
        return _format(data, params.response_format, "Caller IP")
    except Exception as e:
        return _handle_api_error(e, "IP lookup")


if __name__ == "__main__":
    mcp.run()
