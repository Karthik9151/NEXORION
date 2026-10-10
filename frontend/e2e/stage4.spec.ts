import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";

const password = "Nexorion-E2E-Password-2026";

async function registerWorkspace(page: Page, email: string) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Welcome back", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.getByLabel("Workspace name").fill("Stage 4 E2E Workspace");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Create workspace", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mission Center", exact: true })).toBeVisible();
}

async function addEntity(page: Page, name: string) {
  await page.getByRole("button", { name: "Digital World", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Digital World Explorer", exact: true })).toBeVisible();
  await expect(page.getByText("Primary Only Entity", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Add entity", exact: true }).first().click();
  await page.getByLabel("Entity name").fill(name);
  await page.getByLabel("Entity type").selectOption("service");
  await page.locator(".modal-card").getByRole("button", { name: "Add entity", exact: true }).click();
  await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
}

test("invalid login returns a safe visible error", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Email address").fill("unknown-stage4-user@example.com");
  await page.getByLabel("Password").fill("incorrect-password");
  await page.getByRole("button", { name: "Sign in securely", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Email or password is incorrect.");
  await expect(page.getByText(/traceback|stack trace|internal server error/i)).toHaveCount(0);
});

test("registration, workspace isolation, graph, approval gating, reporting, and mobile navigation", async ({ page }) => {
  const email = `stage4-${Date.now()}@example.com`;
  await registerWorkspace(page, email);

  // The UI starts with the workspace returned by the authenticated API.
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  const workspaceSelect = page.getByLabel("Active workspace");
  await expect(workspaceSelect).toBeVisible();
  await expect(workspaceSelect).toBeDisabled();
  await expect(workspaceSelect.locator("option")).toContainText("Stage 4 E2E Workspace");

  // Graph writes are persisted to the currently selected workspace.
  await addEntity(page, "Primary Only Entity");

  // Add a second authorized membership to the disposable CI database, then
  // reload so /auth/me returns the complete membership list to the UI.
  const seedScript = fileURLToPath(new URL("./seed_second_workspace.py", import.meta.url));
  execFileSync("python", [seedScript, email], { stdio: "pipe", env: process.env });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Mission Center", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Settings", exact: true }).click();

  const switcher = page.getByLabel("Active workspace");
  await expect(switcher).toBeEnabled();
  const secondaryId = await switcher.selectOption({ label: "Stage 4 Secondary E2E Workspace" });
  expect(secondaryId).toBeTruthy();
  await expect(page.getByText("Primary Only Entity", { exact: true })).toHaveCount(0);

  await addEntity(page, "Secondary Only Entity");
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  const activeWorkspace = page.getByLabel("Active workspace");
  await activeWorkspace.selectOption({ label: "Stage 4 E2E Workspace" });
  await expect(page.getByText("Secondary Only Entity", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Digital World", exact: true }).click();
  await expect(page.getByText("Primary Only Entity", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Secondary Only Entity", { exact: true })).toHaveCount(0);

  // A synthetic mission must pass server-owned lifecycle commands and then
  // fail closed at the human approval gate when no distinct approver exists.
  await page.getByRole("button", { name: "Mission Center", exact: true }).click();
  await page.getByRole("button", { name: "New mission", exact: true }).click();
  await page.getByLabel("Mission objective").fill("Validate Stage 5 approval enforcement workflow");
  await page.getByLabel("Registered scenario").selectOption("scenario-auth-failure-v1");
  await page.locator(".modal-card").getByRole("button", { name: "Create mission", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Simulation Lab", exact: true })).toBeVisible();

  const queueResponse = page.waitForResponse((response) =>
    response.url().includes("/v1/missions/") &&
    response.url().includes("/jobs") &&
    response.request().method() === "POST" &&
    response.status() === 409
  );
  await page.getByRole("button", { name: /Run synthetic simulation/ }).click();
  const blockedQueue = await queueResponse;
  expect((await blockedQueue.json()).error.code).toBe("APPROVAL_REQUIRED");
  await expect(page.getByRole("status")).toContainText(/APPROVAL_REQUIRED|approval/i);

  // The report is generated by the API from persisted workspace data.
  await page.getByRole("button", { name: "Reports", exact: true }).click();
  const reportResponse = page.waitForResponse((response) =>
    response.url().includes("/report") &&
    response.request().method() === "GET" &&
    response.status() === 200
  );
  await page.getByRole("button", { name: "Generate mission report", exact: true }).click();
  await reportResponse;
  await expect(page.getByRole("heading", { name: "Persisted mission report", exact: true })).toBeVisible();

  // Responsive navigation must remain available at a narrow mobile viewport.
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileNavigation = page.getByRole("navigation", { name: "Mobile navigation" });
  await expect(mobileNavigation).toBeVisible();
  await mobileNavigation.getByRole("button", { name: "World", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Digital World Explorer", exact: true })).toBeVisible();
  const hasHorizontalOverflow = await page.evaluate(() =>
    document.documentElement.scrollWidth > window.innerWidth
  );
  expect(hasHorizontalOverflow).toBe(false);
});

test("Origo verification is requested from the UI and persists independently of simulation completion", async ({ page }) => {
  const seedScript = fileURLToPath(new URL("./seed_origo_run.py", import.meta.url));
  const seeded = JSON.parse(
    execFileSync("python", [seedScript], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], env: process.env })
  ) as { email: string; password: string; run_id: string };

  await page.goto("/");
  await page.getByLabel("Email address").fill(seeded.email);
  await page.getByLabel("Password").fill(seeded.password);
  await page.getByRole("button", { name: "Sign in securely", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mission Center", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Evidence & Origo", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Independent Origo verification", exact: true })).toBeVisible();
  await expect(page.getByText(seeded.run_id.slice(0, 18), { exact: true })).toBeVisible();

  const verificationResponse = page.waitForResponse((response) =>
    response.url().includes("/runs/" + seeded.run_id + "/verify") &&
    response.request().method() === "POST"
  );
  await page.getByRole("button", { name: /Verify latest run with Origo/ }).click();
  const response = await verificationResponse;
  expect(response.status()).toBe(201);
  expect((await response.json()).status).toBe("verified");
  await expect(page.getByText("verified", { exact: true })).toBeVisible();

  // Reload to prove the verdict comes from persisted API history, not local UI state.
  await page.reload();
  await expect(page.getByRole("heading", { name: "Mission Center", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Evidence & Origo", exact: true }).click();
  await expect(page.getByText("verified", { exact: true })).toBeVisible();
});
