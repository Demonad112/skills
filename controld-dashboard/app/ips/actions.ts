"use server";

import { revalidatePath } from "next/cache";
import { deleteKnownIp } from "@/lib/controld";

export async function deleteKnownIpAction(formData: FormData) {
  const ipId = String(formData.get("ipId"));
  await deleteKnownIp(ipId);
  revalidatePath("/ips");
}
