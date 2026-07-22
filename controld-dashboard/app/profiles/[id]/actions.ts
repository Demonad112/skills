"use server";

import { revalidatePath } from "next/cache";
import { setProfileFilter } from "@/lib/controld";

export async function toggleFilterAction(formData: FormData) {
  const profileId = String(formData.get("profileId"));
  const filterName = String(formData.get("filterName"));
  const nextEnabled = formData.get("nextEnabled") === "true";

  await setProfileFilter(profileId, filterName, nextEnabled);
  revalidatePath(`/profiles/${profileId}`);
}
