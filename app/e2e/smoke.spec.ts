import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

// Sample real entries from the build-time dataset so tests don't rot as the
// data is refreshed daily. Thresholds mirror the static generation rules:
// tag pages require >= 8 items, domain pages >= 3 (see the respective pages).
type SearchIndexItem = { id: string; title: string; tags: string[]; domain: string };
const searchIndex = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "../public/search-index.json"), "utf-8")
) as { items: SearchIndexItem[] };

function normalizeTag(tag: string): string {
  return tag.toLowerCase().replace(/\s+/g, "-");
}

const tagCounts = new Map<string, number>();
const domainCounts = new Map<string, number>();
for (const item of searchIndex.items) {
  for (const tag of item.tags ?? []) {
    const key = normalizeTag(tag);
    tagCounts.set(key, (tagCounts.get(key) ?? 0) + 1);
  }
  if (item.domain) {
    domainCounts.set(item.domain, (domainCounts.get(item.domain) ?? 0) + 1);
  }
}

const topEntry = (counts: Map<string, number>, min: number) =>
  [...counts.entries()].filter(([, c]) => c >= min).sort((a, b) => b[1] - a[1])[0];

const sampleTag = topEntry(tagCounts, 8)?.[0];
const sampleDomain = topEntry(domainCounts, 3)?.[0];
const sampleDomainItem = searchIndex.items.find((i) => i.domain === sampleDomain);

test.describe("basic navigation", () => {
  test("homepage loads and shows daily content", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("新鲜事");
    const articles = page.locator("article");
    await expect(articles.first()).toBeVisible({ timeout: 10000 });
    const count = await articles.count();
    expect(count).toBeGreaterThan(0);
  });

  test("can navigate to search page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("banner").getByRole("link", { name: "搜索" }).click();
    await expect(page).toHaveURL(/\/search\//);
    await expect(page.locator("h1")).toContainText("搜索内容");
  });

  test("search filters content", async ({ page }) => {
    await page.goto("/search/");
    const input = page.getByPlaceholder("搜索标题、描述、标签");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("github");
    // 等待真实信号：结果计数行出现且 > 0（Suspense fallback 消失不代表索引加载完）
    await expect(page.getByText(/找到 [1-9]\d* 条结果/)).toBeVisible({ timeout: 15000 });
    await expect(page.locator("article").first()).toBeVisible();
  });

  test("search supports fuzzy matching", async ({ page }) => {
    await page.goto("/search/");
    const input = page.getByPlaceholder("搜索标题、描述、标签");
    await expect(input).toBeVisible({ timeout: 15000 });
    // Intentional typo should still match "github" thanks to MiniSearch fuzzy search
    await input.fill("githib");
    await expect(page.getByText(/找到 [1-9]\d* 条结果/)).toBeVisible({ timeout: 15000 });
  });

  test("search results can load more", async ({ page }) => {
    await page.goto("/search/");
    const input = page.getByPlaceholder("搜索标题、描述、标签");
    await expect(input).toBeVisible({ timeout: 15000 });
    // Use a broad query that returns more than PAGE_SIZE (20) results
    await input.fill("ai");
    await expect(page.getByText(/找到 [1-9]\d* 条结果/)).toBeVisible({ timeout: 15000 });
    const firstCount = await page.locator("article").count();
    const loadMore = page.locator("button", { hasText: "加载更多" });
    if (await loadMore.isVisible().catch(() => false)) {
      await loadMore.click();
      await page.waitForTimeout(300);
      const secondCount = await page.locator("article").count();
      expect(secondCount).toBeGreaterThan(firstCount);
    } else {
      // If there are no more results to load, at least ensure some results rendered
      expect(firstCount).toBeGreaterThan(0);
    }
  });

  test("can navigate to weekly page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("banner").getByRole("link", { name: "周榜" }).click();
    await expect(page).toHaveURL(/\/weekly\//);
    await expect(page.locator("h1")).toContainText("本周热门");
  });

  test("can navigate to history index", async ({ page }) => {
    await page.goto("/history/");
    await expect(page.locator("h1")).toContainText("往期精选");
    await page.locator("a", { hasText: /\d{4}-\d{2}-\d{2}/ }).first().click();
    await expect(page).toHaveURL(/\/history\/\d{4}-\d{2}-\d{2}\//);
  });

  test("can navigate to a tag page", async ({ page }) => {
    test.skip(!sampleTag, "No tag with enough items in the search index");
    await page.goto(`/tag/${encodeURIComponent(sampleTag!)}/`);
    await expect(page.locator("h1")).toContainText(sampleTag!);
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });
  });

  test("can navigate to a domain page", async ({ page }) => {
    test.skip(!sampleDomain || !sampleDomainItem, "No domain with enough items in the search index");
    await page.goto(`/domain/${sampleDomain!}/`);
    await expect(page.locator("h1")).toContainText(sampleDomain!);
    // The domain page is client-rendered; wait for a real item title to appear.
    await expect(page.getByText(sampleDomainItem!.title.slice(0, 30)).first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });
  });

  test("item detail page renders for enriched items", async ({ page }) => {
    // Use the first daily digest item which always has a summary
    await page.goto("/");
    const firstDetailLink = page.locator('article a[href^="/item/"]').first();
    if (await firstDetailLink.isVisible().catch(() => false)) {
      await firstDetailLink.click();
      await expect(page).toHaveURL(/\/item\//);
      await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });
      await expect(page.locator("text=摘要").first()).toBeVisible();
    } else {
      test.skip(true, "No detail links on homepage today");
    }
  });

  test("subscribe form validates email and shows feedback", async ({ page }) => {
    await page.goto("/");
    const input = page.locator('input[inputmode="email"]');
    await expect(input).toBeVisible();
    await input.fill("not-an-email");
    await page.locator("button", { hasText: "留下邮箱" }).click();
    await expect(page.locator("text=请输入有效邮箱")).toBeVisible();

    await input.fill("test@example.com");
    await page.locator("button", { hasText: "留下邮箱" }).click();
    await expect(page.locator("text=订阅功能即将上线")).toBeVisible();
  });
});

test.describe("mobile viewport", () => {
  test.use({ viewport: { width: 390, height: 844 }, userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)" });

  test("homepage renders without horizontal overflow", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("新鲜事");
    const articles = page.locator("article");
    await expect(articles.first()).toBeVisible({ timeout: 10000 });

    const body = page.locator("body");
    const width = await body.evaluate((el) => el.scrollWidth);
    const viewport = await page.evaluate(() => window.innerWidth);
    expect(width).toBeLessThanOrEqual(viewport + 1); // allow 1px rounding
  });

  test("mobile menu opens and navigates", async ({ page }) => {
    await page.goto("/");
    const menuButton = page.locator('button[aria-label="打开菜单"]');
    await expect(menuButton).toBeVisible();
    await menuButton.click();
    await page.locator('[data-testid="mobile-menu"] a', { hasText: "搜索" }).click();
    await expect(page).toHaveURL(/\/search\//);
  });

  test("search page filters fit on screen", async ({ page }) => {
    await page.goto("/search/");
    await expect(page.locator('select').first()).toBeVisible({ timeout: 15000 });
    const filters = page.locator('select');
    await expect(filters.first()).toBeVisible({ timeout: 10000 });
    const count = await filters.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const box = await filters.nth(i).boundingBox();
      expect(box).not.toBeNull();
      if (box) {
        expect(box.x + box.width).toBeLessThanOrEqual(390 + 2); // iPhone 13 width + margin
      }
    }
  });

  test("key pages have no horizontal overflow", async ({ page }) => {
    const urls = ["/search/", "/history/", "/weekly/"];
    if (sampleTag) urls.push(`/tag/${encodeURIComponent(sampleTag)}/`);
    if (sampleDomain) urls.push(`/domain/${sampleDomain}/`);
    for (const url of urls) {
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      const width = await page.locator("body").evaluate((el) => el.scrollWidth);
      const viewport = await page.evaluate(() => window.innerWidth);
      expect(width, `overflow on ${url}`).toBeLessThanOrEqual(viewport + 1);
    }
  });
});

test.describe("extended coverage", () => {
  test("trends page renders heatmap topics", async ({ page }) => {
    await page.goto("/trends/");
    await expect(page.locator("h1")).toContainText("趋势", { timeout: 10000 });
    // 热力表格至少渲染一个话题行（data 驱动，无话题时跳过）
    const rows = page.locator("table tbody tr[role='button']");
    if ((await rows.count()) > 0) {
      const row = rows.first();
      await expect(row).toBeVisible();
      // 键盘可达性：焦点 + Enter 展开（aria-expanded 翻转）
      await row.focus();
      await page.keyboard.press("Enter");
      await expect(row).toHaveAttribute("aria-expanded", "true");
      // 有样例标题的话题会渲染列表
      const sampleLists = page.locator("table tbody tr td ul");
      if ((await sampleLists.count()) > 0) {
        await expect(sampleLists.first()).toBeVisible();
      }
    }
  });

  test("unknown route renders 404", async ({ page }) => {
    await page.goto("/this-route-does-not-exist/");
    await expect(page.locator("text=404").first()).toBeVisible({ timeout: 10000 });
  });

  test("language toggle updates html lang attribute", async ({ page }) => {
    await page.goto("/");
    const langBefore = await page.evaluate(() => document.documentElement.lang);
    const toggle = page.locator("button[title*='Switch to English'], button[title*='切换到中文']").first();
    await expect(toggle).toBeVisible();
    await toggle.click();
    // 等 effect 同步 <html lang>
    await expect
      .poll(() => page.evaluate(() => document.documentElement.lang), { timeout: 5000 })
      .toBe(langBefore === "zh-CN" ? "en" : "zh-CN");
  });
});
