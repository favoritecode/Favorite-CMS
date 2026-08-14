import { describe, expect, it } from "vitest";
import { manuallyEditedSlug, regeneratedSlug, slugifyTitle, titleDrivenSlug, uniqueSlugSuggestion, validArticleUrl } from "./content-editor";

describe("article editor helpers", () => {
  it("generates a normalized slug from a title", () => {
    expect(slugifyTitle("How Near Field Communication Works!"))
      .toBe("how-near-field-communication-works");
  });

  it("preserves Unicode letters and marks", () => {
    expect(slugifyTitle("বাংলা পোস্টের শিরোনাম")).toBe("বাংলা-পোস্টের-শিরোনাম");
  });

  it("stops title-driven updates after manual editing until regeneration", () => {
    const manual = manuallyEditedSlug("editorial-slug");
    expect(titleDrivenSlug(manual, "Changed title")).toEqual(manual);
    expect(titleDrivenSlug(regeneratedSlug("Changed title"), "Final title").value).toBe("final-title");
  });

  it("suggests a deterministic unused slug", () => {
    expect(uniqueSlugSuggestion("article", ["article", "article-2"])).toBe("article-3");
  });

  it("rejects script URLs while accepting safe links and images", () => {
    expect(validArticleUrl("javascript:alert(1)", "link")).toBe(false);
    expect(validArticleUrl("https://example.com/read", "link")).toBe(true);
    expect(validArticleUrl("https://images.example.com/photo.jpg", "image")).toBe(true);
  });
});
