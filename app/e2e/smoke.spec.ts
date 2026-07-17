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
});
