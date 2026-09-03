<script setup lang="ts">
useHead({
  title: 'Terms of Service — Kluda Retail POS',
  meta: [
    {
      name: 'description',
      content: 'Kluda Terms of Service: terms governing POS usage, offline mode, local device storage disclaimer, subscriptions, and merchant data ownership.'
    }
  ]
})
</script>

<template>
  <div class="space-y-12 pb-24 overflow-hidden">
    <!-- Header -->
    <section class="relative pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto space-y-4">
      <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-black tracking-wide uppercase">
        <UIcon name="i-lucide-scale" class="w-3.5 h-3.5" />
        <span>Legal Agreement</span>
      </div>

      <h1 class="text-4xl sm:text-5xl font-black text-(--ui-text-highlighted) tracking-tight">
        Terms of Service
      </h1>

      <p class="text-sm text-(--ui-text-muted)">
        Effective Date: September 1, 2026 • Last updated: September 2026
      </p>
    </section>

    <!-- Critical Highlights Callout Banners -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
      <!-- Offline & Storage Loss Alert -->
      <div class="p-6 rounded-2xl border border-amber-300 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-950/20 shadow-xs space-y-2">
        <div class="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-bold text-sm">
          <UIcon name="i-lucide-alert-triangle" class="w-5 h-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <span>IMPORTANT NOTICE: Offline Mode & Local Storage Cache</span>
        </div>
        <p class="text-xs sm:text-sm text-amber-950 dark:text-amber-100/90 leading-relaxed">
          Kluda POS includes an offline-first mesh engine engineered strictly for operational continuity during cellular or broadband internet disruptions.
          Transactions completed offline are temporarily stored directly on your physical hardware using your browser's local cache (IndexedDB).
          <strong>If you clear your browser cookies, wipe site data, use aggressive phone "storage optimizer/booster" cleaner utilities, or use private/incognito browsing before reconnecting to the internet to sync with the cloud, un-synced transactions will be wiped permanently from your device. Kluda cannot recover data deleted locally from your device hardware before it reaches our cloud servers.</strong>
        </p>
      </div>

      <!-- Zero-Selling Guarantee Alert -->
      <div class="p-6 rounded-2xl border border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/20 shadow-xs space-y-2">
        <div class="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
          <UIcon name="i-lucide-shield-check" class="w-5 h-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>DATA SOVEREIGNTY: We Never Sell Your Store's Data</span>
        </div>
        <p class="text-xs sm:text-sm text-emerald-950 dark:text-emerald-100/90 leading-relaxed">
          Kluda does not sell, rent, broker, license, or monetize your store's sales records, product pricing, customer ledgers, or business financials to third-party advertisers, lenders, or competitors. Your business records remain exclusively yours. We only disclose records when strictly compelled by a mandatory judicial warrant or lawful court order.
        </p>
      </div>
    </section>

    <!-- Structured Terms Content -->
    <section class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="rounded-3xl border border-(--ui-border) bg-(--ui-bg-elevated) shadow-xs p-6 sm:p-10 space-y-8 text-sm text-(--ui-text) leading-relaxed">
        <!-- Section 1 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">1.</span> Acceptance of Terms
          </h2>
          <p>
            These Terms of Service ("Terms") constitute a legally binding agreement between you ("Merchant", "User", "you") and Kluda ("Kluda", "we", "us", "our"). By registering an account, installing the Progressive Web Application (PWA), or using our Point of Sale (POS) and inventory software, you acknowledge that you have read, understood, and agreed to be bound by these Terms.
          </p>
        </div>

        <!-- Section 2 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">2.</span> Account Registration & Staff Security
          </h2>
          <p>
            To use Kluda, you must create an account providing accurate store information. You are solely responsible for safeguarding your login credentials and staff checkout PINs.
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>You agree to notify us immediately if you suspect unauthorized access to your account or cashier registers.</li>
            <li>Store owners are responsible for all sales, inventory adjustments, and cash drawer reconciliations logged under their staff member profiles.</li>
          </ul>
        </div>

        <!-- Section 3 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">3.</span> Offline Operations & Device Cache Policy
          </h2>
          <p>
            Kluda is built to keep retail counters ringing when connectivity drops. However, offline operations operate under fundamental browser storage mechanics:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li><strong>Temporary Local Storage:</strong> Sales made during internet downtime are queued in local browser IndexedDB storage until internet access is restored.</li>
            <li><strong>Risk of Device Data Deletion:</strong> If you reset your device, uninstall the browser, clear browsing history/cookies, or run aggressive third-party device cleaner applications (e.g. CleanMaster or memory cleaners) before syncing, un-synced sales will be erased permanently from your hardware.</li>
            <li><strong>Merchant Responsibility:</strong> You agree to connect your POS device to internet connectivity at regular intervals (at minimum daily at shift close) to ensure cloud backups and data synchronization.</li>
          </ul>
        </div>

        <!-- Section 4 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">4.</span> Hardware, Printers & Barcode Scanners
          </h2>
          <p>
            Kluda interfaces with external hardware including device cameras, USB barcode readers, and wireless ESC/POS thermal receipt printers via WebBluetooth and WebUSB standards:
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li>Kluda does not manufacture third-party printers or scanners and makes no warranties regarding physical hardware failure, mechanical paper jams, or Bluetooth hardware drops.</li>
            <li>WebBluetooth printing is officially supported on Google Chrome and Chromium browsers on Android, Windows, and macOS. iOS Safari does not natively support WebBluetooth standards at this time.</li>
          </ul>
        </div>

        <!-- Section 5 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">5.</span> Subscriptions, Sachet Pricing & Cancellations
          </h2>
          <p>
            Kluda offers both free tier operations and paid subscription tiers (including daily passes, weekly, monthly, and annual plans):
          </p>
          <ul class="list-disc pl-5 space-y-1.5 text-xs text-(--ui-text-muted)">
            <li><strong>Sachet Passes:</strong> 24-hour daily passes and short-term access tickets activate immediately upon payment confirmation and remain valid for the purchased duration.</li>
            <li><strong>Free Trials:</strong> Plans with free trials automatically grant full tier access for the designated duration. If you have previously utilized a free trial on any tier, trial privileges will not apply to subsequent registrations.</li>
            <li><strong>Billing & Renewals:</strong> Monthly and annual subscriptions renew automatically via Paystack unless cancelled prior to the renewal date.</li>
            <li><strong>Refund Policy:</strong> All subscription fees and pass payments are non-refundable once activated, as digital POS access is provisioned immediately.</li>
          </ul>
        </div>

        <!-- Section 6 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">6.</span> Data Ownership & Acceptable Use
          </h2>
          <p>
            You retain 100% ownership of all business records, inventory counts, product pricing, customer lists, and financial transactions entered into Kluda. You agree not to use Kluda to record illegal transactions, distribute malicious software, or attempt to reverse engineer our proprietary sync engine.
          </p>
        </div>

        <!-- Section 7 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">7.</span> Limitation of Liability
          </h2>
          <p>
            To the maximum extent permitted by applicable law, Kluda and its creators shall not be liable for any indirect, incidental, special, or consequential damages — including loss of profits, data loss due to local cache wiping, hardware failure, or business interruption — arising out of the use or inability to use our services.
          </p>
        </div>

        <!-- Section 8 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">8.</span> Governing Law & Jurisdiction
          </h2>
          <p>
            These Terms shall be governed by and construed in accordance with the laws of the Federal Republic of Nigeria, without regard to conflict of law principles. Any dispute arising out of or related to these Terms shall be resolved through friendly negotiation, or submitted to competent courts in Nigeria.
          </p>
        </div>

        <!-- Section 9 -->
        <div class="space-y-3">
          <h2 class="text-lg font-bold text-(--ui-text-highlighted) flex items-center gap-2">
            <span class="text-emerald-600 dark:text-emerald-400 font-mono">9.</span> Contact Us
          </h2>
          <p>
            If you have questions or inquiries regarding these Terms of Service, please contact us at:
          </p>
          <p class="font-mono text-xs font-semibold text-emerald-700 dark:text-emerald-400">
            support@kluda.app
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
