import "server-only";

const API_BASE_URL = "https://api.controld.com";

export class ControlDError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ControlDError";
    this.status = status;
  }
}

function getToken(): string {
  const token = process.env.CONTROLD_API_KEY;
  if (!token) {
    throw new ControlDError(
      "Missing CONTROLD_API_KEY. Copy .env.local.example to .env.local and set your token from https://controld.com/dashboard/api."
    );
  }
  return token;
}

async function request<T = any>(
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new ControlDError("Invalid or missing API token.", 401);
    }
    if (res.status === 403) {
      throw new ControlDError(
        "Permission denied. This action likely needs a Write-scoped token.",
        403
      );
    }
    if (res.status === 404) {
      throw new ControlDError("Not found.", 404);
    }
    if (res.status === 429) {
      const retryAfter = res.headers.get("Retry-After");
      throw new ControlDError(
        `Rate limited by Control D.${retryAfter ? ` Retry after ${retryAfter}s.` : ""}`,
        429
      );
    }
    let detail = "";
    try {
      detail = JSON.stringify(await res.json());
    } catch {
      detail = await res.text();
    }
    throw new ControlDError(`Control D API error (${res.status}): ${detail}`, res.status);
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}

// --- Account / Org ---
export const getAccountInfo = () => request("GET", "/users");
export const listOrganizations = () => request("GET", "/organizations");
export const listOrganizationMembers = (orgId: string) =>
  request("GET", `/organizations/${orgId}/members`);

// --- Profiles ---
export const listProfiles = () => request("GET", "/profiles");
export const getProfileFilters = (profileId: string) =>
  request("GET", `/profiles/${profileId}/filters`);
export const getProfileExternalFilters = (profileId: string) =>
  request("GET", `/profiles/${profileId}/filters/external`);
export const getProfileServices = (profileId: string) =>
  request("GET", `/profiles/${profileId}/services`);
export const getProfileRuleFolders = (profileId: string) =>
  request("GET", `/profiles/${profileId}/groups`);
export const setProfileFilter = (profileId: string, filterName: string, enabled: boolean) =>
  request("PUT", `/profiles/${profileId}/filters/${filterName}`, { status: enabled ? 1 : 0 });

// --- Devices / Endpoints ---
export const listDevices = () => request("GET", "/endpoints");
export const listDeviceTypes = () => request("GET", "/endpoints/types");

// --- Access IPs ---
export const listKnownIps = () => request("GET", "/access/ip");
export const listDeviceRecentIps = (deviceId: string) =>
  request("POST", `/access/ip/${deviceId}`);
export const deleteKnownIp = (ipId: string) => request("DELETE", `/access/ip/${ipId}`);

// --- Analytics settings (NOT query logs — see README) ---
export const getAnalyticsSettings = () => request("GET", "/analytics");

// --- Misc ---
export const listServiceCatalog = () => request("GET", "/services");
export const getCallerIp = () => request("GET", "/ip");
