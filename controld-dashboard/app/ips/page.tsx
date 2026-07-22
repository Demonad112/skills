import { ControlDError, listKnownIps } from "@/lib/controld";
import { Card, ErrorBanner } from "../components";
import { deleteKnownIpAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function KnownIpsPage() {
  try {
    const data = await listKnownIps();
    const ips = data?.body?.ips ?? data?.ips ?? [];

    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold">Known / Learned IPs</h1>
        <p className="text-sm text-gray-500">
          A new entry here can indicate a new device or unexpected source querying your
          resolver. This is a snapshot, not a timestamped log.
        </p>
        {ips.length === 0 && <p className="text-sm text-gray-500">No known IPs found.</p>}
        <div className="flex flex-col gap-2">
          {ips.map((ip: any) => {
            const id = ip.PK ?? ip.id;
            return (
              <Card key={id} className="flex items-center justify-between">
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(ip, null, 2)}
                </pre>
                <form action={deleteKnownIpAction}>
                  <input type="hidden" name="ipId" value={id} />
                  <button
                    type="submit"
                    className="text-xs px-3 py-1 rounded-full border border-red-300 text-red-700 hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950"
                  >
                    Remove
                  </button>
                </form>
              </Card>
            );
          })}
        </div>
      </div>
    );
  } catch (e) {
    return <ErrorBanner message={e instanceof ControlDError ? e.message : String(e)} />;
  }
}
