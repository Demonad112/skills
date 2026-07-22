import Link from "next/link";
import { ControlDError, listProfiles } from "@/lib/controld";
import { Card, ErrorBanner } from "../components";

export const dynamic = "force-dynamic";

export default async function ProfilesPage() {
  try {
    const data = await listProfiles();
    const profiles = data?.body?.profiles ?? data?.profiles ?? [];

    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold">Profiles</h1>
        {profiles.length === 0 && <p className="text-sm text-gray-500">No profiles found.</p>}
        <div className="flex flex-col gap-2">
          {profiles.map((p: any) => (
            <Link key={p.PK} href={`/profiles/${p.PK}`}>
              <Card className="hover:border-gray-400 dark:hover:border-neutral-600 transition">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{p.name ?? p.PK}</span>
                  <span className="text-xs text-gray-500">{p.PK}</span>
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
