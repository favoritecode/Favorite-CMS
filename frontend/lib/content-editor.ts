export type SlugControl = { value: string; manual: boolean };

export function slugifyTitle(title: string): string {
  const normalized = title.normalize("NFKC").toLocaleLowerCase().trim();
  const slug = normalized
    .replace(/[^\p{Letter}\p{Number}\p{Mark}]+/gu, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  return Array.from(slug).slice(0, 120).join("").replace(/-$/g, "");
}

export function titleDrivenSlug(current: SlugControl, title: string): SlugControl {
  return current.manual ? current : { value: slugifyTitle(title), manual: false };
}

export function manuallyEditedSlug(value: string): SlugControl {
  return { value, manual: true };
}

export function regeneratedSlug(title: string): SlugControl {
  return { value: slugifyTitle(title), manual: false };
}

export function uniqueSlugSuggestion(base: string, existing: Iterable<string>): string {
  const used = new Set(existing);
  if (!used.has(base)) return base;
  let index = 2;
  while (used.has(`${base.slice(0, Math.max(1, 119 - String(index).length))}-${index}`)) index += 1;
  return `${base.slice(0, Math.max(1, 119 - String(index).length))}-${index}`;
}

export function validArticleUrl(value: string, kind: "link" | "image"): boolean {
  try {
    const protocol = new URL(value).protocol;
    return kind === "image" ? protocol === "https:" || protocol === "http:"
      : protocol === "https:" || protocol === "http:" || protocol === "mailto:";
  } catch { return false; }
}
