import Link from "next/link";
import {
  ControlDError,
  getAccountInfo,
  getAnalyticsSettings,
  listDevices,
  listKnownIps,
  listProfiles,
} from "@/lib/controld";
import { Card, ErrorBanner, StatTile } from "./components";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  try {
    const [account, profiles, devices, knownIps, analytics] = await Promise.all([
      getAccountInfo(),
      listProfiles(),
      listDevices(),
      listKnownIps(),
      getAnalyticsSettings(),
    ]);

    const profileList = profiles?.body?.profiles ?? profiles?.profiles ?? [];
    const deviceList = devices?.body?.devices ?? devices?.devices ?? [];
    const ipList = knownIps?.body?.ips ?? knownIps?.ips ?? [];
    const email = account?.body?.user?.email ?? account?.user?.email ?? "unknown";

    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-semibold mb-1">Overview</h1>
          <p className="text-sm text-gray-500">Signed in as {email}</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <StatTile label="Profiles" value={Array.isArray(profileList) ? profileList.length : "—"} />
          <StatTile label="Devices" value={Array.isArray(deviceList) ? deviceList.length : "—"} />
          <StatTile label="Known IPs" value={Array.isArray(ipList) ? ipList.length : "—"} />
        </div>

        <Card>
          <h2 className="font-medium mb-2">Analytics logging settings</h2>
          <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(analytics, null, 2)}
          </pre>
          <p className="text-xs text-gray-500 mt-2">
            This is only the logging level/storage region configuration. Control D&apos;s
            public API does not expose query logs, traffic stats, or blocked-domain data —
            use the Control D dashboard&apos;s Analytics/Activity Log pages for that.
          </p>
        </Card>

        <div className="flex gap-4 text-sm">
          <Link className="underline" href="/profiles">
            Browse profiles →
          </Link>
          <Link className="underline" href="/devices">
            Browse devices →
          </Link>
          <Link className="underline" href="/ips">
            Browse known IPs →
          </Link>
        </div>
      </div>
    );
  } catch (e) {
    return <ErrorBanner message={e instanceof ControlDError ? e.message : String(e)} />;
  }
}
