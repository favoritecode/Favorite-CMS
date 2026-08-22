import { adminRequest } from "./admin-client";
import type { MediaItem } from "./admin-types";

const inferredImageMime = (file: File) => file.type || ({ jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp" } as Record<string, string>)[file.name.toLowerCase().split(".").pop() ?? ""] || "";

export async function uploadAdminImage(file: File): Promise<string> {
  const mimeType = inferredImageMime(file);
  if (!new Set(["image/jpeg", "image/png", "image/webp"]).has(mimeType)) throw new Error("Choose a PNG, JPEG, or WebP image.");
  if (!file.size || file.size > 4_000_000) throw new Error("Image must be no larger than 4 MB.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  const item = await adminRequest<MediaItem>("/admin/manage/transport/media", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ file_name: file.name, mime_type: mimeType, data_base64: btoa(binary),
      description: "", labels: [], visibility: "published" }),
  });
  return `/media/${encodeURIComponent(item.id)}`;
}
