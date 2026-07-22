# controld-dashboard

A local Next.js web dashboard for your [Control D](https://controld.com) DNS
account: browse profiles, toggle filters, view devices, and check known/recent
source IPs — without leaving a browser tab.

It uses the same Control D REST API (`https://api.controld.com`) as the
`controld-mcp` MCP server in this repo, but as a standalone app rather than an
MCP tool.

## Important limitation: no query-log / analytics data

Control D's public API does not expose DNS query logs, per-domain traffic, or
blocked-request history — only profile/device/filter/rule configuration and
known/recent IPs. The Overview page shows your analytics *logging settings*
(level + storage region), not actual traffic. For real query-history-based
anomaly detection, use the Control D dashboard's own Analytics/Activity Log
pages.

The **Devices → recent IPs** and **Known IPs** pages are the closest useful
signal this app can offer for "did something new start hitting my resolver."

## Setup

```bash
cd controld-dashboard
npm install
cp .env.local.example .env.local
# edit .env.local and set CONTROLD_API_KEY (generate at https://controld.com/dashboard/api)
npm run dev
```

Open http://localhost:3000.

- **Read** scope token: browse profiles, devices, known IPs.
- **Write** scope token: also needed to toggle filters or remove a known IP
  from the dashboard.

The API key is only ever read server-side (`lib/controld.ts` is marked
`server-only`) — it is never sent to the browser.

## Pages

- `/` — account info, counts, analytics logging settings
- `/profiles` → `/profiles/[id]` — list profiles; toggle individual filters
- `/devices` → `/devices/[id]` — list devices; view a device's recent source IPs
- `/ips` — known/learned IPs account-wide; remove an entry

## Production build

```bash
npm run build
npm start
```
