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

test("admin imports a local transcript and sees READY counts", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("admin@example.com");
  await page.getByLabel("パスワード").fill("Learning123!");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/materials$/);
  await page.goto("/admin/materials");

  const row = page.getByRole("row", { name: /シャンプーの基本/ });
  await row.getByRole("button", { name: "字幕を取り込む" }).click();
  await expect(row.getByText("READY")).toBeVisible();
  await expect(
    row.getByText(/segment 5 \/ chunk 2 \/ embedding 2/),
  ).toBeVisible();
  await expect(row.getByText(/deterministic-local/)).toBeVisible();
});

test("premium asks a grounded question, seeks from a citation, and sees history", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill("premium@example.com");
  await page.getByLabel("パスワード").fill("Learning123!");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/materials$/);
  await page.goto("/ask");
  await page.getByLabel("質問").fill("すすぎ残しがないよう丁寧に流します。");
  await page.getByLabel("シャンプーの基本").check();
  await page.getByRole("button", { name: "質問する" }).click();

  await expect(page.getByText("COMPLETED")).toBeVisible();
  await expect(page.getByRole("heading", { name: "回答" })).toBeVisible();
  const citation = page.getByRole("link", { name: /秒から動画を確認/ }).first();
  await citation.click();
  await expect(page).toHaveURL(/start_ms=/);
  const expectedSeconds =
    Number(new URL(page.url()).searchParams.get("start_ms")) / 1000;
  const video = page.locator("video");
  await video.evaluate((element) =>
    element.dispatchEvent(new Event("loadedmetadata")),
  );
  await expect
    .poll(() =>
      video.evaluate((element) => (element as HTMLVideoElement).currentTime),
    )
    .toBe(expectedSeconds);

  await page.goto("/history");
  await expect(
    page
      .getByRole("heading", { name: "すすぎ残しがないよう丁寧に流します。" })
      .first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "役に立った" }).first().click();
  await expect(page.getByText("評価を保存しました。")).toBeVisible();
});
