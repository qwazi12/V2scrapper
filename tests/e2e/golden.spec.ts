import { test, expect } from "../../apps/web/node_modules/@playwright/test";

test("original research → three real media formats → exact approval → unknown mock receipt → reconciliation", async ({
  page,
}) => {
  await page.goto("/");
  const localLogin = page.getByRole("button", {
    name: "Enter local owner workspace",
  });
  await expect(localLogin.or(page.getByRole("heading", {name:"Control Room."}))).toBeVisible();
  if (await localLogin.isVisible()) await localLogin.click();
  await expect(
    page.getByRole("heading", { name: "Control Room." }),
  ).toBeVisible();
  await expect(page.locator(".safe-card")).toContainText("LOCAL SAFE MODE");
  await page
    .getByRole("button", { name: "Create original test story" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Research Desk." }),
  ).toBeVisible();
  for (const phrase of [
    "Mara keeps the last lighthouse lit.",
    "The signal guides travelers home.",
  ]) {
    await page
      .locator("article.claim-card")
      .filter({ hasText: phrase })
      .getByRole("button", { name: "Review exact evidence" })
      .click();
    await expect(
      page.getByRole("button", { name: "Approve research package" }),
    ).toBeEnabled();
  }
  await page.getByRole("button", { name: "Approve research package" }).click();
  await expect(
    page.getByText("Research package approved and hashed.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Create campaign from approved research" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Campaign Studio." }),
  ).toBeVisible();
  const campaignURL = page.url();
  const gemini = page.locator("section.variant-editor").first();
  await gemini.getByText("Draft with Gemini", { exact: true }).click();
  await expect(gemini.getByRole("button", { name: "Estimate draft cost" })).toBeDisabled();
  await expect(gemini).toContainText("Paid calls are disabled");
  for (const format of ["Landscape · 16:9", "Short · 9:16", "Carousel · 4:5"]) {
    const editor = page
      .locator("section.variant-editor")
      .filter({ hasText: format });
    await editor
      .getByRole("button", { name: "Approve script", exact: true })
      .click();
    await expect(
      editor.getByRole("button", { name: "Approve script", exact: true }),
    ).toBeDisabled();
  }
  for (const format of ["Landscape · 16:9", "Short · 9:16", "Carousel · 4:5"]) {
    await page.goto(campaignURL);
    await page
      .locator("section.variant-editor")
      .filter({ hasText: format })
      .getByRole("button", {
        name: format.includes("Carousel") ? "Render carousel" : "Render video",
        exact: true,
      })
      .click();
    await expect(
      page.getByRole("heading", { name: "Production." }),
    ).toBeVisible();
  }
  await expect
    .poll(() => page.locator("article.export-card").count(), {
      timeout: 180000,
      intervals: [1000, 2000, 4000],
    })
    .toBeGreaterThanOrEqual(3);
  await expect(page.locator(".job-row .badge.failed")).toHaveCount(0);
  await page.screenshot({
    path: "artifacts/e2e-production.png",
    fullPage: true,
  });
  await page
    .locator("article.export-card")
    .filter({ hasText: "Short · 9:16" })
    .first()
    .getByRole("link", { name: "Play & inspect" })
    .click();
  const video = page.locator("video");
  await expect(video).toBeVisible();
  await expect
    .poll(() => video.evaluate((v: HTMLVideoElement) => v.readyState), {
      timeout: 30000,
    })
    .toBeGreaterThanOrEqual(2);
  const meta = await video.evaluate((v: HTMLVideoElement) => ({
    width: v.videoWidth,
    height: v.videoHeight,
    duration: v.duration,
  }));
  expect(meta.width).toBe(1080);
  expect(meta.height).toBe(1920);
  expect(meta.duration).toBeGreaterThan(10);
  await video.press("Space");
  await expect
    .poll(() => video.evaluate((v: HTMLVideoElement) => v.currentTime), {
      timeout: 10000,
    })
    .toBeGreaterThan(0.2);
  await video.press("Space");
  await page
    .getByRole("textbox", { name: "Editorial & rights review note" })
    .fill(
      "Automated synthetic-only inspection of original art, decoded portrait video, technical QA and reviewed test rights. Not commercial editorial approval.",
    );
  await page.getByRole("button", { name: "Approve exact export" }).click();
  await expect(
    page.getByText(
      "Approval recorded for this exact export hash and input snapshot.",
    ),
  ).toBeVisible();
  await page.screenshot({
    path: "artifacts/e2e-quality-review.png",
    fullPage: true,
  });
  const ex = await page
    .getByRole("combobox", { name: "Export", exact: true })
    .inputValue();
  await page.getByRole("button", { name: "Prepare distribution" }).click();
  await page
    .getByRole("combobox", { name: "Approved export", exact: true })
    .selectOption(ex);
  await page
    .getByRole("combobox", { name: "Exact destination account" })
    .selectOption({ label: "youtube · scos-mock-youtube" });
  await page.getByRole("button", { name: "Create mock package" }).click();
  await page
    .getByRole("button", { name: "Schedule mock submit" })
    .first()
    .click();
  await expect(
    page.getByRole("button", { name: "Reconcile receipt" }),
  ).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Reconcile receipt" }).click();
  await expect(
    page.getByText(
      "Provider receipt reconciled. Confirmed with one mock submission; no retry performed.",
    ),
  ).toBeVisible();
  await page.screenshot({
    path: "artifacts/e2e-reconciled.png",
    fullPage: true,
  });
});

test("mobile layout and keyboard dialog", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const localLogin = page.getByRole("button", {
    name: "Enter local owner workspace",
  });
  await expect(localLogin.or(page.getByRole("heading", {name:"Control Room."}))).toBeVisible();
  if (await localLogin.isVisible()) await localLogin.click();
  await expect(
    page.getByRole("heading", { name: "Control Room." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "New idea", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "Working title", exact: true }),
  ).toBeFocused();
  await page
    .getByRole("textbox", { name: "Working title", exact: true })
    .press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.screenshot({ path: "artifacts/e2e-mobile.png", fullPage: true });
});
