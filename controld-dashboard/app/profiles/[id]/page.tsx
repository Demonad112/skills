import {
  ControlDError,
  getProfileFilters,
  getProfileRuleFolders,
  getProfileServices,
} from "@/lib/controld";
import { Card, ErrorBanner } from "../../components";
import { toggleFilterAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function ProfileDetailPage({ params }: { params: { id: string } }) {
  const profileId = params.id;

  try {
    const [filtersData, servicesData, groupsData] = await Promise.all([
      getProfileFilters(profileId),
      getProfileServices(profileId),
      getProfileRuleFolders(profileId),
    ]);

    const filters = filtersData?.body?.filters ?? filtersData?.filters ?? [];
    const services = servicesData?.body?.services ?? servicesData?.services ?? [];
    const groups = groupsData?.body?.groups ?? groupsData?.groups ?? [];

    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-xl font-semibold">Profile {profileId}</h1>

        <section>
          <h2 className="font-medium mb-2">Filters</h2>
          <div className="flex flex-col gap-2">
            {filters.length === 0 && <p className="text-sm text-gray-500">No filters returned.</p>}
            {filters.map((f: any) => {
              const name = f.PK ?? f.name;
              const enabled = Boolean(f.status ?? f.enabled);
              return (
                <Card key={name} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{f.name ?? name}</div>
                    <div className="text-xs text-gray-500">{name}</div>
                  </div>
                  <form action={toggleFilterAction}>
                    <input type="hidden" name="profileId" value={profileId} />
                    <input type="hidden" name="filterName" value={name} />
                    <input type="hidden" name="nextEnabled" value={String(!enabled)} />
                    <button
                      type="submit"
                      className={`text-xs px-3 py-1 rounded-full border ${
                        enabled
                          ? "bg-green-100 border-green-400 text-green-800 dark:bg-green-950 dark:text-green-300"
                          : "bg-gray-100 border-gray-300 text-gray-600 dark:bg-neutral-800 dark:text-gray-400"
                      }`}
                    >
                      {enabled ? "Enabled — click to disable" : "Disabled — click to enable"}
                    </button>
                  </form>
                </Card>
              );
            })}
          </div>
        </section>

        <section>
          <h2 className="font-medium mb-2">Services blocked</h2>
          <Card>
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(services, null, 2)}
            </pre>
          </Card>
        </section>

        <section>
          <h2 className="font-medium mb-2">Custom rule folders</h2>
          <Card>
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(groups, null, 2)}
            </pre>
          </Card>
        </section>
      </div>
    );
  } catch (e) {
    return <ErrorBanner message={e instanceof ControlDError ? e.message : String(e)} />;
  }
}
