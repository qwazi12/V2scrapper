import { test, expect } from "../../apps/web/node_modules/@playwright/test";

test("hosted frontend proxies staging and keeps unconfigured owner sign-in locked", async ({ page, request, baseURL }) => {
  test.skip(!process.env.SCOS_E2E_LOCKED, "Requires the isolated locked staging frontend");
  const protection: Record<string, string> = process.env.VERCEL_OIDC_TOKEN
    ? { "x-vercel-trusted-oidc-idp-token": process.env.VERCEL_OIDC_TOKEN }
    : {};
  const origin = new URL(baseURL!).origin;
  // The short-lived Vercel credential is never forwarded to Google or another origin.
  await page.route("**/*", async (route) => {
    const req = route.request();
    await route.continue({ headers: new URL(req.url()).origin === origin ? { ...req.headers(), ...protection } : req.headers() });
  });
  const config = await request.get("/api/v1/auth/config", { headers: protection });
  expect(config.status()).toBe(200);
  expect(await config.json()).toMatchObject({
    environment: "staging",
    local_login_allowed: false,
    oidc_configured: false,
    publishing_disabled: true,
    paid_calls_disabled: true,
  });
  expect((await request.get("/api/v1/workspace", { headers: protection })).status()).toBe(401);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Sign in with Google" })).toBeDisabled();
  await expect(page.getByText("Owner sign-in is locked until", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Enter local owner workspace" })).toHaveCount(0);
  await page.setViewportSize({ width: 375, height: 812 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: process.env.SCOS_LOCK_SCREENSHOT || "artifacts/staging-locked.png", fullPage: true });
});
