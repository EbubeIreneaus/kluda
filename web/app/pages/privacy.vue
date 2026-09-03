<script setup lang="ts">
useHead({
  title: 'Privacy Policy — Kluda Retail POS',
  meta: [
    {
      name: 'description',
      content: 'Kluda Privacy Policy: our zero data selling guarantee, how merchant sales and inventory data are protected, and payment security standards.'
    }
  ]
})
</script>

<template>
  <div class="space-y-12 pb-24 overflow-hidden">
    <!-- Header -->
    <section class="relative pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto space-y-4">
      <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-black tracking-wide uppercase">
        <UIcon name="i-lucide-lock" class="w-3.5 h-3.5" />
        <span>Privacy & Data Protection</span>
      </div>

      <h1 class="text-4xl sm:text-5xl font-black text-(--ui-text-highlighted) tracking-tight">
        Privacy Policy
      </h1>

      <p class="text-sm text-(--ui-text-muted)">
        Effective Date: September 1, 2026 • Last updated: September 2026
      </p>
    </section>

    <!-- Zero Data Selling Guarantee Callout -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="p-6 sm:p-8 rounded-3xl border border-emerald-300 dark:border-emerald-500/40 bg-emerald-50 dark:bg-emerald-950/20 shadow-xs space-y-3">
        <div class="flex items-center gap-3 text-emerald-800 dark:text-emerald-300 font-black text-base">
          <UIcon name="i-lucide-shield-check" class="w-6 h-6 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>OUR IRONCLAD PLEDGE: ZERO DATA SELLING</span>
        </div>
        <p class="text-sm text-emerald-950 dark:text-emerald-100/90 leading-relaxed font-medium">
          Kluda does not sell, broker, rent, license, or monetize your store’s transaction records, customer debt ledgers, profit margins, or inventory volumes to third-party advertisers, data brokers, loan companies, or competitors. Your business numbers remain strictly confidential and belong exclusively to your store.
        </p>
      </div>
    </section>

    <!-- Structured Content -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs p-6 sm:p-10 space-y-8 text-sm text-(--ui-text) leading-relaxed">
        <!-- Section 1 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">1.</span> Information We Collect
          </h2>
          <p>
            When you register and use Kluda POS, we collect information necessary to operate your retail register:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li><strong>Merchant Account Details:</strong> Store owner name, phone number, email address, store branch name, and business category.</li>
            <li><strong>Store Catalog Data:</strong> Product names, barcodes, purchase costs, selling prices, stock quantities, and low-stock alerts.</li>
            <li><strong>Checkout & Sales Transactions:</strong> Timestamps of sales, items sold, payment methods (Cash, Transfer, POS, Debt), discounts applied, and cashier staff IDs.</li>
            <li><strong>Customer Credit & Debt Ledgers:</strong> Customer names and phone numbers optionally entered by you to track credit balances and repayments.</li>
            <li><strong>Technical Telemetry:</strong> Device operating system, browser type, and IP address used to detect unusual logins and maintain secure sessions.</li>
          </ul>
        </div>

        <!-- Section 2 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">2.</span> How We Use Your Information
          </h2>
          <p>
            We use your data solely to deliver, protect, and optimize our software:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>To process and record sales at your checkout counter.</li>
            <li>To deduct stock balances automatically and issue reorder warnings.</li>
            <li>To synchronize sales in real time across multiple registers and store branches.</li>
            <li>To authenticate owners and cashiers via passwords and PINs.</li>
            <li>To provide revenue breakdowns, margin calculations, and inventory audits.</li>
          </ul>
        </div>

        <!-- Section 3 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">3.</span> Local Device Storage (IndexedDB) & Cache
          </h2>
          <p>
            To enable 100% offline selling when internet connection drops, Kluda caches product lists and pending transactions directly inside your browser storage:
          </p>
          <p class="text-xs text-(--ui-text-muted)">
            This offline database lives entirely on your physical device. It is not accessible to other websites or applications. Once internet connectivity is restored, pending offline transactions are synced to our secure encrypted cloud database.
          </p>
        </div>

        <!-- Section 4 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">4.</span> Payment & Billing Data Security
          </h2>
          <p>
            When purchasing subscriptions or passes, payment card data is processed directly by PCI-DSS certified payment processors (Paystack):
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>Kluda never receives, logs, or stores your full credit/debit card numbers, CVVs, or card PINs on our servers.</li>
            <li>We only receive a tokenized transaction confirmation and reference ID to activate your plan.</li>
          </ul>
        </div>

        <!-- Section 5 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">5.</span> Data Sharing & Third Parties
          </h2>
          <p>
            We do not share your store data with external parties except under the following strict conditions:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li><strong>Infrastructure Providers:</strong> Encrypted cloud hosting and database infrastructure (e.g. AWS / DigitalOcean / Supabase) operating under strict data processing agreements.</li>
            <li><strong>Legal Requirements:</strong> When compelled by valid legal processes, search warrants, or court orders issued by competent judicial authorities in Nigeria.</li>
          </ul>
        </div>

        <!-- Section 6 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">6.</span> Data Retention & Account Deletion
          </h2>
          <p>
            You have full control over your business records:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>You can export your inventory, sales history, and customer ledgers at any time in standard CSV formats.</li>
            <li>If you choose to close your account, you may request permanent deletion of your store database by emailing support@kluda.app. Upon verification, all records will be purged within 30 days.</li>
          </ul>
        </div>

        <!-- Section 7 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">7.</span> Security Measures
          </h2>
          <p>
            We deploy modern cybersecurity safeguards to prevent unauthorized access:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>All communication between your POS devices and our servers is encrypted using TLS 1.3 encryption.</li>
            <li>Owner passwords and staff PINs are hashed using cryptographic algorithms before storage.</li>
            <li>Granular staff role permissions restrict access so cashiers only see sales counters and cannot view store profit margins or modify system settings.</li>
          </ul>
        </div>

        <!-- Section 8 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">8.</span> Changes to this Policy
          </h2>
          <p>
            We may periodically update this Privacy Policy as new retail features are introduced. Material changes will be communicated via in-app dashboard notices or by email to registered store owners.
          </p>
        </div>

        <!-- Section 9 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">9.</span> Contact Our Privacy Officer
          </h2>
          <p>
            For privacy inquiries, data export requests, or security disclosures, please reach out to:
          </p>
          <p class="font-mono text-xs font-semibold text-emerald-700 dark:text-emerald-400">
            support@kluda.app
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
