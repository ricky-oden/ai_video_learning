import { expect, test } from "@playwright/test";

test("premium user logs in, opens the material list, and views a local video", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("premium@example.com");
  await page.getByLabel("パスワード").fill("Learning123!");
  await page.getByRole("button", { name: "ログイン" }).click();

  await expect(page).toHaveURL(/\/materials$/);
  await expect(page.getByRole("heading", { name: "教材一覧" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "教材一覧" })).toBeVisible();
  await page.getByRole("link", { name: "教材を見る" }).first().click();

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "動画プレイヤー" }),
  ).toBeVisible();
  await expect(page.locator("video source")).toHaveAttribute(
    "src",
    "/media/demo-hair-technique.mp4",
  );

  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("link", { name: "ログイン" })).toBeVisible();
});
