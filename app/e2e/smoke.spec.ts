import { test, expect } from "@playwright/test";

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
    await page.waitForSelector("text=加载搜索索引", { state: "hidden", timeout: 10000 });
    const input = page.getByPlaceholder("搜索标题、描述、标签");
    await input.fill("github");
    await page.waitForTimeout(500);
    const countText = await page.locator("text=找到").textContent();
    expect(countText).toMatch(/找到 \d+ 条结果/);
  });

  test("search supports fuzzy matching", async ({ page }) => {
    await page.goto("/search/");
    await page.waitForSelector("text=加载搜索索引", { state: "hidden", timeout: 10000 });
    const input = page.getByPlaceholder("搜索标题、描述、标签");
    // Intentional typo should still match "github" thanks to MiniSearch fuzzy search
    await input.fill("githib");
    await page.waitForTimeout(500);
    const countText = await page.locator("text=找到").textContent();
    expect(countText).toMatch(/找到 \d+ 条结果/);
    expect(countText).not.toMatch(/找到 0 条结果/);
  });

  test("search results can load more", async ({ page }) => {
    await page.goto("/search/");
    await page.waitForSelector("text=加载搜索索引", { state: "hidden", timeout: 10000 });
    // Use a broad query that returns more than PAGE_SIZE (20) results
    await page.getByPlaceholder("搜索标题、描述、标签").fill("ai");
    await page.waitForTimeout(500);
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
    await page.goto("/tag/github/");
    await expect(page.locator("h1")).toContainText("github");
    await expect(page.locator("article").first()).toBeVisible({ timeout: 10000 });
  });

  test("can navigate to a domain page", async ({ page }) => {
    await page.goto("/domain/github.com/");
    await expect(page.locator("h1")).toContainText("github.com");
    // The domain page is client-rendered; wait for a known GitHub repo title to appear.
    await expect(page.locator("text=codecrafters-io/build-your-own-x").first()).toBeVisible({ timeout: 10000 });
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
    await page.waitForSelector("text=加载搜索索引", { state: "hidden", timeout: 10000 });
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
    for (const url of ["/search/", "/tag/github/", "/domain/github.com/", "/history/", "/weekly/"]) {
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      const width = await page.locator("body").evaluate((el) => el.scrollWidth);
      const viewport = await page.evaluate(() => window.innerWidth);
      expect(width, `overflow on ${url}`).toBeLessThanOrEqual(viewport + 1);
    }
  });
});
