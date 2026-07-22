import { ControlDError, listDeviceRecentIps } from "@/lib/controld";
import { Card, ErrorBanner } from "../../components";

export const dynamic = "force-dynamic";

export default async function DeviceDetailPage({ params }: { params: { id: string } }) {
  const deviceId = params.id;

  try {
    const data = await listDeviceRecentIps(deviceId);
    const ips = data?.body?.ips ?? data?.ips ?? [];

    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold">Device {deviceId}</h1>
        <section>
          <h2 className="font-medium mb-2">
            Recent source IPs (up to last 50)
          </h2>
          <p className="text-xs text-gray-500 mb-2">
            Watch this list for a new/unrecognized IP — that&apos;s the closest signal
            the public API offers for detecting unexpected activity on a device.
          </p>
          {ips.length === 0 && <p className="text-sm text-gray-500">No recent IPs returned.</p>}
          <div className="flex flex-col gap-2">
            {ips.map((ip: any, i: number) => (
              <Card key={i}>
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(ip, null, 2)}
                </pre>
              </Card>
            ))}
          </div>
        </section>
      </div>
    );
  } catch (e) {
    return <ErrorBanner message={e instanceof ControlDError ? e.message : String(e)} />;
  }
}
