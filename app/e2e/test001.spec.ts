import { test, expect } from "@playwright/test";

test("Kluda Retail POS - Complete End-to-End Suite", async ({ page }) => {
  // Allow ample time for the full 8-step end-to-end journey across dev server / CI
  test.setTimeout(120000);

  await page.addInitScript(() => {
    try {
      window.localStorage.setItem("bypass_pwa_gate", "true");
      window.sessionStorage.setItem("bypass_pwa_gate", "true");
      window.sessionStorage.setItem("pos_unlocked", "true");
    } catch {}
  });

  // Generate isolated, dynamic variables for each test execution
  const testId = Date.now().toString().slice(-6);

  const merchant = {
    fullname: `Tester ${testId}`,
    email: `tester_${testId}@test.com`,
    password: "Password123!",
    storeName: `Gadget Branch ${testId}`,
    storeCategory: "Electronics & Gadgets",
    storeAddress: "Plot 14 Commercial Avenue, Lagos",
  };

  const product = {
    name: `Riggs Perfume ${testId}`,
    price: "5000",
    quantity: "20",
    barcode: `50${testId}${Math.floor(1000 + Math.random() * 9000)}`,
  };

  const customer = {
    name: `Funke Fumilayo ${testId}`,
    email: `funke_${testId}@test.com`,
    phone: `080${Math.floor(10000000 + Math.random() * 90000000)}`,
    address: "22 Victoria Island, Lagos",
  };

  const cashier = {
    firstName: "Cashier",
    lastName: `Staff ${testId}`,
    email: `cashier_${testId}@test.com`,
    phone: `081${Math.floor(10000000 + Math.random() * 90000000)}`,
  };

  // ── Step 01 ─────────────────────────────────────────────────────────────
  await test.step("01. Merchant Registration, Store Provisioning & PIN Setup", async () => {
    // 1. Visit POS application root
    await page.goto("/?standalone=true");

    // Handle PWA standalone gatekeeper if visible in browser tab
    const pwaBypass = page.getByRole("button", { name: /Continue in Browser Tab/i });
    if (await pwaBypass.isVisible({ timeout: 2000 }).catch(() => false)) {
      await pwaBypass.click();
    }

    // Handle onboarding slides tour if presented
    const startRegistrationBtn = page.getByRole("button", { name: /Create Free Store & Account/i });
    if (await startRegistrationBtn.isVisible({ timeout: 2500 }).catch(() => false)) {
      await startRegistrationBtn.click();
    } else {
      await page.goto("/auth/register");
    }

    // 2. Step 1: Merchant Account Information
    await expect(page.getByRole("heading", { name: /Create Your Account/i })).toBeVisible({ timeout: 20000 });

    await page.getByPlaceholder("e.g. Chidinma Okonkwo").fill(merchant.fullname);
    await page.getByPlaceholder("owner@mybusiness.com").fill(merchant.email);
    await page.getByPlaceholder("••••••••").fill(merchant.password);
    await page.getByRole("button", { name: "Continue to Store Setup" }).click();

    // 3. Step 2: Store Branch Setup
    await expect(page.getByRole("heading", { name: /Set Up Your Store/i })).toBeVisible();

    await page.getByPlaceholder("e.g. Chidinma Supermarket").fill(merchant.storeName);
    await page.getByRole("combobox").click();
    await page.getByText(merchant.storeCategory, { exact: false }).click();
    await page.getByPlaceholder(/14 Allen Avenue/i).fill(merchant.storeAddress);

    // Check mandatory terms & privacy policy agreement
    await page.locator('input[type="checkbox"]').check();

    // Listen for backend registration response
    const [regResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/auth/register") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 20000 }
      ),
      page.getByRole("button", { name: "Launch Store & Register" }).click(),
    ]);
    expect(regResponse.ok()).toBeTruthy();

    // 4. Quick Terminal PIN Setup Modal
    await expect(page.getByText("Create Quick Terminal PIN")).toBeVisible({ timeout: 15000 });

    const pinModal = page.locator('[data-testid="set-pin-modal"]');

    // Enter initial PIN (1 2 3 4)
    for (const digit of ["1", "2", "3", "4"]) {
      await pinModal.getByRole("button", { name: digit, exact: true }).click();
    }

    // Wait for step transition to confirmation
    await expect(page.getByText("Confirm Your PIN")).toBeVisible({ timeout: 5000 });

    // Enter confirmation PIN (1 2 3 4) and listen for /pin response
    const [pinResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/staff/pin") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      (async () => {
        for (const digit of ["1", "2", "3", "4"]) {
          await pinModal.getByRole("button", { name: digit, exact: true }).click();
        }
      })(),
    ]);
    expect(pinResponse.ok()).toBeTruthy();

    // 5. Verify Terminal Loaded
    await expect(page.getByText("KLUDA", { exact: true })).toBeVisible();
    await expect(page.getByText(merchant.storeName).first()).toBeVisible();
    await expect(page.getByText("Quota Status")).toBeVisible();
  });

  // ── Step 02 ─────────────────────────────────────────────────────────────
  await test.step("02. Product Catalog Management (Create Stock with Barcode)", async () => {
    await page.goto("/products");
    await expect(page.getByRole("heading", { name: /Products & Inventory/i })).toBeVisible();

    await page.getByRole("button", { name: "Add Product" }).click();

    const addProductModal = page.getByRole("dialog");
    await expect(addProductModal).toBeVisible();

    await addProductModal.getByPlaceholder("e.g. Golden Penny Spaghetti 500g").fill(product.name);
    await addProductModal.getByPlaceholder("0.00").fill(product.price);
    await addProductModal.getByPlaceholder("0", { exact: true }).fill(product.quantity);
    await addProductModal.getByPlaceholder("5901234123457").fill(product.barcode);

    const [productRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/product") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      addProductModal.getByRole("button", { name: "Add Product" }).click(),
    ]);
    expect(productRes.ok()).toBeTruthy();

    // Verify product is listed in catalog
    await expect(page.getByText(product.name).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(product.barcode).first()).toBeVisible();
  });

  // ── Step 03 ─────────────────────────────────────────────────────────────
  await test.step("03. POS Register Workflow (Search, Discount, Complete Sale)", async () => {
    await page.goto("/pos");
    await expect(page.getByPlaceholder(/Enter name or scan barcode/i)).toBeVisible();

    // Search and select product
    const searchInput = page.getByPlaceholder(/Enter name or scan barcode/i);
    await searchInput.fill(product.name.slice(0, 8));

    const productResult = page.getByRole("button", { name: new RegExp(product.name, "i") }).first();
    await expect(productResult).toBeVisible({ timeout: 10000 });
    await productResult.click();

    // Cart validation
    await expect(page.getByRole("heading", { name: "Cart" })).toBeVisible();
    await expect(page.getByText(product.name).first()).toBeVisible();

    // Apply Payment Method: POS
    await page.getByRole("button", { name: "POS", exact: true }).click();

    // Apply discount of ₦300
    const discountInput = page.getByPlaceholder("0.00");
    await discountInput.fill("300");

    await expect(page.getByText("₦4,700.00").first()).toBeVisible();

    // 1. Open Receipt Dialog
    await page.getByRole("button", { name: "Complete Sale" }).click();

    // 2. Click Done to finalize sale and listen for API transaction response
    const [saleRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/sales") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      page.getByRole("button", { name: "Done" }).click(),
    ]);
    expect(saleRes.ok()).toBeTruthy();
  });

  // ── Step 04 ─────────────────────────────────────────────────────────────
  await test.step("04. Sales Audit Log Verification", async () => {
    // Navigate and wait for the page's API fetch to complete
    const [salesFetch] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/sales") && resp.status() === 200,
        { timeout: 15000 }
      ),
      page.goto("/sales"),
    ]);
    expect(salesFetch.ok()).toBeTruthy();

    await expect(page.getByRole("heading", { name: /Sales History/i })).toBeVisible();

    // Verify Walk-in sale with POS payment method appear as text (plain <td>)
    await expect(page.getByText("Walk-in").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("pos").first()).toBeVisible();
  });

  // ── Step 05 ─────────────────────────────────────────────────────────────
  await test.step("05. Customer Management & Debt Ledger", async () => {
    await page.goto("/customers");
    await expect(page.getByRole("heading", { name: /Customers & Debts/i })).toBeVisible();

    await page.getByRole("button", { name: "Add Customer" }).click();

    const customerModal = page.getByRole("dialog");
    await expect(customerModal).toBeVisible();

    await customerModal.getByPlaceholder("e.g. Adebayo Femi").fill(customer.name);
    await customerModal.getByPlaceholder("email@example.com").fill(customer.email);
    await customerModal.getByPlaceholder("08012345678").fill(customer.phone);
    await customerModal.getByPlaceholder("Customer address...").fill(customer.address);

    const [custRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/customer") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      customerModal.getByRole("button", { name: "Add Customer" }).click(),
    ]);
    expect(custRes.ok()).toBeTruthy();

    // Verify customer in table (using text match since table uses plain <td>)
    await expect(page.getByText(customer.email).first()).toBeVisible({ timeout: 10000 });

    // Inspect Debts tab — button is a plain <button> with text "Debts"
    await page.getByRole("button", { name: "Debts", exact: true }).click();
    await expect(page.getByText("Total Outstanding").first()).toBeVisible({ timeout: 10000 });
  });

  // ── Step 06 ─────────────────────────────────────────────────────────────
  await test.step("06. Analytics and Reporting", async () => {
    await page.goto("/analytics");
    await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();

    // Click Today and wait for analytics API to return data before asserting KPI cards
    const [analyticsRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/analytics") && resp.status() === 200,
        { timeout: 15000 }
      ),
      page.getByRole("button", { name: "Today" }).first().click(),
    ]);
    expect(analyticsRes.ok()).toBeTruthy();

    // KPI cards only render once data is loaded (v-if="data")
    await expect(page.getByText("Total Revenue").first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Transactions").first()).toBeVisible({ timeout: 10000 });
  });

  // ── Step 07 ─────────────────────────────────────────────────────────────
  await test.step("07. Merchant Hub & Branch Cashier Management", async () => {
    // 1. Visit Merchant Hub
    await page.goto("/marchant");
    await expect(page.getByRole("heading", { name: new RegExp(merchant.fullname, "i") })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("button", { name: "Manage Billing" })).toBeVisible();

    // 2. Open Stores Management
    await page.goto("/marchant/stores");
    await expect(page.getByText(merchant.storeName)).toBeVisible({ timeout: 10000 });

    // 3. Open Store Branch Detail
    const manageBtn = page.getByRole("link", { name: "Manage Branch" }).or(page.getByRole("button", { name: "Manage Branch" })).first();
    if (await manageBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await manageBtn.click();
    } else {
      await page.getByText(merchant.storeName).first().click();
    }

    // 4. Add Cashier to this Branch
    await page.getByRole("button", { name: "Add Cashier" }).click();

    const addStaffModal = page.getByRole("dialog");
    await expect(addStaffModal).toBeVisible();

    await addStaffModal.locator('input[type="text"]').first().fill(cashier.firstName);
    await addStaffModal.locator('input[type="text"]').nth(1).fill(cashier.lastName);
    await addStaffModal.locator('input[type="email"]').fill(cashier.email);
    await addStaffModal.locator('input[type="tel"]').fill(cashier.phone);

    // Submit Staff creation and listen for API response
    const [staffRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/staff") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      addStaffModal.getByRole("button", { name: "Add Staff" }).click(),
    ]);
    expect(staffRes.ok()).toBeTruthy();

    // Assert dynamic confirmation without brittle hardcoded UUIDs
    await expect(page.getByText("Cashier Account Created!").last()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/added to this branch/).last()).toBeVisible();

    // Verify staff appears in branch team (plain <td>, use getByText)
    await expect(page.getByText(cashier.email).first()).toBeVisible({ timeout: 10000 });
  });

  // ── Step 08 ─────────────────────────────────────────────────────────────
  await test.step("08. Logout & Terminal Lock", async () => {
    await page.goto("/");
    await expect(page.getByText("KLUDA", { exact: true })).toBeVisible();

    // Open User Dropdown Menu
    const userMenuBtn = page.locator("header").locator("button.rounded-full").last();
    await userMenuBtn.click();

    await page.getByRole("menuitem", { name: "Logout" }).click();

    // Verify redirected to sign in
    await expect(page.getByRole("heading", { name: "Terminal Sign In" })).toBeVisible({ timeout: 10000 });
  });
});
