import { test, expect } from "@playwright/test";

test.describe.serial("Kluda Retail POS - Complete End-to-End Suite", () => {
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

  test("01. Merchant Registration, Store Provisioning & PIN Setup", async ({ page }) => {
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
    await expect(page.getByRole("heading", { name: /Create Your Merchant Account/i })).toBeVisible();

    await page.getByPlaceholder("e.g. Chidinma Okonkwo").fill(merchant.fullname);
    await page.getByPlaceholder("owner@mybusiness.com").fill(merchant.email);
    await page.getByPlaceholder("••••••••").fill(merchant.password);
    await page.getByRole("button", { name: "Continue to Store Setup" }).click();

    // 3. Step 2: Store Branch Setup
    await expect(page.getByRole("heading", { name: /Setup Your First Store Branch/i })).toBeVisible();

    await page.getByPlaceholder("e.g. Chidinma Supermarket").fill(merchant.storeName);
    await page.getByRole("combobox").click();
    await page.getByText(merchant.storeCategory, { exact: false }).click();
    await page.getByPlaceholder(/14 Allen Avenue/i).fill(merchant.storeAddress);

    // Listen for backend registration response
    const [regResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/api/v1/auth/register") && resp.status() === 200,
        { timeout: 20000 }
      ),
      page.getByRole("button", { name: "Launch Store & Register" }).click(),
    ]);
    expect(regResponse.ok()).toBeTruthy();

    // 4. Quick Terminal PIN Setup Modal
    await expect(page.getByText("Create Quick Terminal PIN")).toBeVisible({ timeout: 15000 });

    const pinModal = page.locator("div").filter({ hasText: /Create Quick Terminal PIN|Confirm Your PIN/ }).last();

    // Enter initial PIN (1 2 3 4)
    for (const digit of ["1", "2", "3", "4"]) {
      await pinModal.getByRole("button", { name: digit, exact: true }).click();
    }

    // Wait for step transition to confirmation
    await expect(page.getByText("Confirm Your PIN")).toBeVisible({ timeout: 5000 });

    // Enter confirmation PIN (1 2 3 4) and listen for /pin response
    const [pinResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/api/v1/auth/pin") && resp.status() === 200,
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
    await expect(page.getByText("KLUDA")).toBeVisible();
    await expect(page.getByText(merchant.storeName)).toBeVisible();
    await expect(page.getByText("Quota Status")).toBeVisible();
  });

  test("02. Product Catalog Management (Create Stock with Barcode)", async ({ page }) => {
    await page.goto("/products");
    await expect(page.getByRole("heading", { name: /Products & Inventory/i })).toBeVisible();

    await page.getByRole("button", { name: "Add Product" }).click();

    const addProductModal = page.locator("div").filter({ hasText: "Add New Product" }).last();
    await expect(addProductModal).toBeVisible();

    await addProductModal.getByPlaceholder("e.g. Golden Penny Spaghetti 500g").fill(product.name);
    await addProductModal.getByPlaceholder("0.00").fill(product.price);
    await addProductModal.getByPlaceholder("0", { exact: true }).fill(product.quantity);
    await addProductModal.getByPlaceholder("5901234123457").fill(product.barcode);

    const [productRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/api/v1/products") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      addProductModal.getByRole("button", { name: "Add Product" }).click(),
    ]);
    expect(productRes.ok()).toBeTruthy();

    // Verify product is listed in catalog
    await expect(page.getByText(product.name).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(product.barcode).first()).toBeVisible();
  });

  test("03. POS Register Workflow (Search, Discount, Complete Sale)", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByPlaceholder(/Enter name or scan barcode/i)).toBeVisible();

    // Search and select product
    const searchInput = page.getByPlaceholder(/Enter name or scan barcode/i);
    await searchInput.fill(product.name.slice(0, 8));

    const productResult = page.getByRole("button", { name: new RegExp(product.name, "i") }).first();
    await expect(productResult).toBeVisible({ timeout: 10000 });
    await productResult.click();

    // Cart validation
    await expect(page.getByRole("heading", { name: "Cart" })).toBeVisible();
    await expect(page.getByText(product.name)).toBeVisible();

    // Apply Payment Method: POS
    await page.getByRole("button", { name: "POS", exact: true }).click();

    // Apply discount of ₦300
    const discountInput = page.getByPlaceholder("0.00");
    await discountInput.fill("300");

    await expect(page.getByText(/Total₦4,700\.00/)).toBeVisible();

    // Complete Sale and listen for API transaction response
    const [saleRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/api/v1/sales") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      page.getByRole("button", { name: "Complete Sale" }).click(),
    ]);
    expect(saleRes.ok()).toBeTruthy();

    // Close Receipt Dialog
    const doneBtn = page.getByRole("button", { name: "Done" });
    if (await doneBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await doneBtn.click();
    }
  });

  test("04. Sales Audit Log Verification", async ({ page }) => {
    await page.goto("/sales");
    await expect(page.getByRole("heading", { name: /Sales History/i })).toBeVisible();

    // Verify Walk-in sale with POS payment method
    await expect(page.getByRole("cell", { name: "Walk-in" }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("cell", { name: "pos", exact: true }).first()).toBeVisible();
  });

  test("05. Customer Management & Debt Ledger", async ({ page }) => {
    await page.goto("/customers");
    await expect(page.getByRole("heading", { name: /Customers & Debtors/i })).toBeVisible();

    await page.getByRole("button", { name: "Add Customer" }).click();

    const customerModal = page.locator("div").filter({ hasText: "Add New Customer" }).last();
    await expect(customerModal).toBeVisible();

    await customerModal.getByPlaceholder("e.g. Aliko Dangote").fill(customer.name);
    await customerModal.getByPlaceholder("customer@example.com").fill(customer.email);
    await customerModal.getByPlaceholder("08012345678").fill(customer.phone);
    await customerModal.getByPlaceholder("Street address, City").fill(customer.address);

    const [custRes] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes("/api/v1/customers") && (resp.status() === 200 || resp.status() === 201),
        { timeout: 15000 }
      ),
      customerModal.getByRole("button", { name: "Add Customer" }).click(),
    ]);
    expect(custRes.ok()).toBeTruthy();

    // Verify customer in table
    await expect(page.getByRole("cell", { name: customer.email }).first()).toBeVisible({ timeout: 10000 });

    // Inspect Debts tab
    await page.getByRole("button", { name: /Debts/i }).click();
    await expect(page.getByText("Total Outstanding")).toBeVisible();
  });

  test("06. Analytics and Reporting", async ({ page }) => {
    await page.goto("/analytics");
    await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();

    // Test Period Toggle
    await page.getByRole("button", { name: "Today" }).click();
    await expect(page.getByText("Total Revenue")).toBeVisible();
    await expect(page.getByText("Transactions")).toBeVisible();
  });

  test("07. Merchant Hub & Branch Cashier Management", async ({ page }) => {
    // 1. Visit Merchant Hub
    await page.goto("/marchant");
    await expect(page.getByRole("heading", { name: new RegExp(merchant.fullname, "i") })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("button", { name: "Manage Billing" })).toBeVisible();

    // 2. Open Stores Management
    await page.goto("/marchant/stores");
    await expect(page.getByText(merchant.storeName)).toBeVisible({ timeout: 10000 });

    // 3. Open Store Branch Detail
    const manageBtn = page.getByRole("button", { name: "Manage Branch" }).first();
    if (await manageBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await manageBtn.click();
    } else {
      await page.getByText(merchant.storeName).first().click();
    }

    // 4. Add Cashier to this Branch
    await page.getByRole("button", { name: "Add Cashier" }).click();

    const addStaffModal = page.locator("div").filter({ hasText: "Add Cashier / Staff Member" }).last();
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
    await expect(page.getByText("Cashier Account Created!")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/added to this branch/)).toBeVisible();

    // Verify staff appears in branch team team
    await expect(page.getByRole("cell", { name: cashier.email })).toBeVisible();
  });

  test("08. Logout & Terminal Lock", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("KLUDA")).toBeVisible();

    // Open User Dropdown Menu
    const userMenuBtn = page.getByRole("button", { name: /T\d|O/i }).first();
    await userMenuBtn.click();

    await page.getByRole("menuitem", { name: "Logout" }).click();

    // Verify redirected to sign in
    await expect(page.getByRole("heading", { name: "Terminal Sign In" })).toBeVisible({ timeout: 10000 });
  });
});
