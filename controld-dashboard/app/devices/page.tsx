import Link from "next/link";
import { ControlDError, listDevices } from "@/lib/controld";
import { Card, ErrorBanner } from "../components";

export const dynamic = "force-dynamic";

export default async function DevicesPage() {
  try {
    const data = await listDevices();
    const devices = data?.body?.devices ?? data?.devices ?? [];

    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold">Devices</h1>
        {devices.length === 0 && <p className="text-sm text-gray-500">No devices found.</p>}
        <div className="flex flex-col gap-2">
          {devices.map((d: any) => (
            <Link key={d.PK} href={`/devices/${d.PK}`}>
              <Card className="hover:border-gray-400 dark:hover:border-neutral-600 transition">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{d.name ?? d.PK}</div>
                    <div className="text-xs text-gray-500">
                      Profile: {d.profile?.name ?? d.profile?.PK ?? "—"}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">{d.PK}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    );
  } catch (e) {
    return <ErrorBanner message={e instanceof ControlDError ? e.message : String(e)} />;
  }
}
