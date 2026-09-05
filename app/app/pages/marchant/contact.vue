<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ layout: 'marchant' })

const auth = useAuthStore()
const toast = useToast()
const { api } = useApi()

interface ContactDetails {
  email?: string | null
  phone?: string | null
  whatsapp?: string | null
  address?: string | null
  hours?: string | null
  facebook?: string | null
  twitter?: string | null
  linkedin?: string | null
  instagram?: string | null
  youtube?: string | null
  tiktok?: string | null
}

const isLoading = ref(true)
const contact = ref<ContactDetails>({
  email: 'support@kluda.app',
  phone: '+234 800 000 0000',
  whatsapp: '2348000000000',
  address: 'Lagos, Nigeria',
  hours: 'Mon - Sat: 8:00 AM - 8:00 PM WAT',
  facebook: '',
  twitter: '',
  linkedin: '',
  instagram: '',
  youtube: '',
  tiktok: ''
})

async function fetchContactInfo() {
  isLoading.value = true
  try {
    const res = await api<ContactDetails>('/auth/contact-info')
    if (res && typeof res === 'object') {
      contact.value = {
        ...contact.value,
        ...res
      }
    }
  } catch {
    // Fallback defaults
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchContactInfo()
})

// Validation helper: verifies URL exists, is not null, and not empty string
function isValidUrl(val: string | null | undefined): boolean {
  return typeof val === 'string' && val.trim().length > 0
}

function normalizeUrl(url: string | null | undefined, platform: string): string {
  if (!url) return '#'
  const clean = url.trim()
  if (clean.startsWith('http://') || clean.startsWith('https://')) {
    return clean
  }
  if (platform === 'twitter') return `https://x.com/${clean.replace(/^@/, '')}`
  if (platform === 'facebook') return `https://facebook.com/${clean}`
  if (platform === 'instagram') return `https://instagram.com/${clean.replace(/^@/, '')}`
  if (platform === 'linkedin') return `https://linkedin.com/company/${clean}`
  if (platform === 'youtube') return `https://youtube.com/${clean.startsWith('@') ? clean : '@' + clean}`
  if (platform === 'tiktok') return `https://tiktok.com/@${clean.replace(/^@/, '')}`
  return `https://${clean}`
}

// Clean WhatsApp number (removes non-digits for wa.me)
const cleanWhatsappNumber = computed(() => {
  if (!contact.value.whatsapp) return ''
  return contact.value.whatsapp.replace(/[^0-9]/g, '')
})

const whatsappChatUrl = computed(() => {
  const number = cleanWhatsappNumber.value
  if (!number) return '#'
  const storeName = auth.current_store?.name || auth.stores?.[0]?.name || 'My Store'
  const merchantName = auth.fullName || auth.user?.fullname || 'Kluda Merchant'
  const text = encodeURIComponent(
    `Hello Kluda Support, I am reaching out from "${storeName}" (Merchant: ${merchantName}). I need assistance with:`
  )
  return `https://wa.me/${number}?text=${text}`
})

const activeSocials = computed(() => {
  const list = []
  if (isValidUrl(contact.value.whatsapp)) {
    list.push({
      key: 'whatsapp',
      name: 'WhatsApp Community',
      url: `https://wa.me/${cleanWhatsappNumber.value}`,
      icon: 'i-lucide-message-circle',
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500 hover:text-black'
    })
  }
  if (isValidUrl(contact.value.twitter)) {
    list.push({
      key: 'twitter',
      name: 'X (Twitter)',
      url: normalizeUrl(contact.value.twitter, 'twitter'),
      icon: 'i-lucide-twitter',
      color: 'text-sky-400 bg-sky-400/10 border-sky-400/20 hover:bg-sky-400 hover:text-black'
    })
  }
  if (isValidUrl(contact.value.facebook)) {
    list.push({
      key: 'facebook',
      name: 'Facebook',
      url: normalizeUrl(contact.value.facebook, 'facebook'),
      icon: 'i-lucide-facebook',
      color: 'text-blue-500 bg-blue-500/10 border-blue-500/20 hover:bg-blue-500 hover:text-white'
    })
  }
  if (isValidUrl(contact.value.instagram)) {
    list.push({
      key: 'instagram',
      name: 'Instagram',
      url: normalizeUrl(contact.value.instagram, 'instagram'),
      icon: 'i-lucide-instagram',
      color: 'text-pink-500 bg-pink-500/10 border-pink-500/20 hover:bg-pink-500 hover:text-white'
    })
  }
  if (isValidUrl(contact.value.linkedin)) {
    list.push({
      key: 'linkedin',
      name: 'LinkedIn',
      url: normalizeUrl(contact.value.linkedin, 'linkedin'),
      icon: 'i-lucide-linkedin',
      color: 'text-blue-400 bg-blue-400/10 border-blue-400/20 hover:bg-blue-400 hover:text-white'
    })
  }
  if (isValidUrl(contact.value.youtube)) {
    list.push({
      key: 'youtube',
      name: 'YouTube',
      url: normalizeUrl(contact.value.youtube, 'youtube'),
      icon: 'i-lucide-video',
      color: 'text-red-500 bg-red-500/10 border-red-500/20 hover:bg-red-500 hover:text-white'
    })
  }
  if (isValidUrl(contact.value.tiktok)) {
    list.push({
      key: 'tiktok',
      name: 'TikTok',
      url: normalizeUrl(contact.value.tiktok, 'tiktok'),
      icon: 'i-lucide-music',
      color: 'text-fuchsia-400 bg-fuchsia-400/10 border-fuchsia-400/20 hover:bg-fuchsia-400 hover:text-black'
    })
  }
  return list
})

function copyToClipboard(text: string | null | undefined, label: string) {
  if (!text) return
  if (import.meta.client && navigator.clipboard) {
    navigator.clipboard.writeText(text)
    toast.add({
      title: `${label} Copied`,
      description: `"${text}" copied to your clipboard`,
      color: 'success',
      icon: 'i-lucide-check-circle'
    })
  }
}

const faqs = [
  {
    q: 'My thermal receipt printer is not connecting. What should I check?',
    a: 'Ensure Bluetooth or USB is enabled on your device. In the POS Checkout or Settings modal, select "Pair Thermal Printer" and choose your printer model (58mm or 80mm). On iOS/iPhones, use Bluefy browser for Web Bluetooth support.'
  },
  {
    q: 'Can cashiers record sales when the store has no internet?',
    a: 'Yes! Kluda POS works fully offline. Transactions are stored locally in the register database and will automatically sync to your cloud portfolio the moment internet connectivity returns.'
  },
  {
    q: 'How do I add or manage cashiers and managers for my branches?',
    a: 'Head to "Store Branches" in the navigation, select your branch, and click "Manage Staff". You can assign granular permissions like "Record Sales", "Apply Discounts", or "Manage Inventory".'
  },
  {
    q: 'How do monthly sales quotas and subscription upgrades work?',
    a: 'Your monthly sales quota resets on the 1st of every calendar month. You can view real-time quota metrics on your Overview dashboard or upgrade anytime under "Billing & Plans".'
  }
]
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6 pb-16">
    <!-- Header Banner -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl border border-default bg-elevated shadow-xs">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 inline-flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Support Helpdesk
          </span>
          <span v-if="contact.hours" class="text-xs text-dimmed hidden sm:inline">
            {{ contact.hours }}
          </span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-black text-highlighted tracking-tight">
          Help & Merchant Support
        </h1>
        <p class="text-sm text-muted max-w-2xl">
          Get direct, fast assistance with your retail stores, POS registers, thermal printer hardware, and subscription billing.
        </p>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <a
          v-if="cleanWhatsappNumber"
          :href="whatsappChatUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          <UButton
            color="primary"
            size="lg"
            class="font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20"
          >
            <UIcon name="i-lucide-message-circle" class="w-5 h-5 mr-1.5" />
            Chat on WhatsApp
          </UButton>
        </a>
      </div>
    </div>

    <!-- Contact Channels Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 1. WhatsApp Channel (Primary Recommendation) -->
      <div class="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5 sm:p-6 space-y-4 flex flex-col justify-between shadow-xs relative overflow-hidden group">
        <div class="absolute -right-6 -bottom-6 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />
        
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="w-12 h-12 rounded-2xl bg-emerald-500 text-slate-950 flex items-center justify-center shadow-md shadow-emerald-500/20">
              <UIcon name="i-lucide-message-circle" class="w-6 h-6" />
            </div>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Fastest Reply
            </span>
          </div>

          <div>
            <h3 class="text-lg font-bold text-highlighted">WhatsApp Support</h3>
            <p class="text-xs text-muted mt-1 leading-relaxed">
              Instant help with checkout errors, sending screenshots of receipts, or troubleshooting thermal hardware.
            </p>
          </div>

          <div v-if="cleanWhatsappNumber" class="pt-1">
            <p class="font-mono text-sm font-bold text-emerald-400">
              {{ contact.whatsapp }}
            </p>
          </div>
        </div>

        <div class="space-y-2 pt-2">
          <a
            v-if="cleanWhatsappNumber"
            :href="whatsappChatUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="block w-full"
          >
            <UButton
              block
              color="primary"
              class="font-bold bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <UIcon name="i-lucide-external-link" class="w-4 h-4 mr-1.5" />
              Open WhatsApp Chat
            </UButton>
          </a>
          <UButton
            v-if="cleanWhatsappNumber"
            block
            variant="ghost"
            color="neutral"
            size="xs"
            class="text-xs text-dimmed hover:text-highlighted"
            @click="copyToClipboard(contact.whatsapp, 'WhatsApp Number')"
          >
            <UIcon name="i-lucide-copy" class="w-3.5 h-3.5 mr-1" />
            Copy WhatsApp Number
          </UButton>
        </div>
      </div>

      <!-- 2. Phone Helpline -->
      <div class="rounded-2xl border border-default bg-elevated p-5 sm:p-6 space-y-4 flex flex-col justify-between shadow-xs">
        <div class="space-y-3">
          <div class="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center">
            <UIcon name="i-lucide-phone-call" class="w-6 h-6" />
          </div>

          <div>
            <h3 class="text-lg font-bold text-highlighted">Phone Helpline</h3>
            <p class="text-xs text-muted mt-1 leading-relaxed">
              For urgent register interruptions or checkout downtime during active store retail hours.
            </p>
          </div>

          <div v-if="contact.phone" class="pt-1">
            <p class="font-mono text-sm font-bold text-highlighted">
              {{ contact.phone }}
            </p>
            <p v-if="contact.hours" class="text-[11px] text-dimmed mt-0.5">
              {{ contact.hours }}
            </p>
          </div>
        </div>

        <div class="space-y-2 pt-2">
          <a
            v-if="contact.phone"
            :href="`tel:${contact.phone}`"
            class="block w-full"
          >
            <UButton
              block
              variant="outline"
              color="neutral"
              class="font-bold border-default hover:bg-accented"
            >
              <UIcon name="i-lucide-phone" class="w-4 h-4 mr-1.5 text-amber-400" />
              Call Support
            </UButton>
          </a>
          <UButton
            v-if="contact.phone"
            block
            variant="ghost"
            color="neutral"
            size="xs"
            class="text-xs text-dimmed hover:text-highlighted"
            @click="copyToClipboard(contact.phone, 'Phone Number')"
          >
            <UIcon name="i-lucide-copy" class="w-3.5 h-3.5 mr-1" />
            Copy Phone Number
          </UButton>
        </div>
      </div>

      <!-- 3. Official Email Support -->
      <div class="rounded-2xl border border-default bg-elevated p-5 sm:p-6 space-y-4 flex flex-col justify-between shadow-xs">
        <div class="space-y-3">
          <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center">
            <UIcon name="i-lucide-mail" class="w-6 h-6" />
          </div>

          <div>
            <h3 class="text-lg font-bold text-highlighted">Email Support</h3>
            <p class="text-xs text-muted mt-1 leading-relaxed">
              Recommended for account billing inquiries, subscription adjustments, and formal requests.
            </p>
          </div>

          <div v-if="contact.email" class="pt-1">
            <p class="font-mono text-sm font-bold text-highlighted truncate" :title="contact.email">
              {{ contact.email }}
            </p>
            <p class="text-[11px] text-dimmed mt-0.5">
              Average response time: &lt; 4 hours
            </p>
          </div>
        </div>

        <div class="space-y-2 pt-2">
          <a
            v-if="contact.email"
            :href="`mailto:${contact.email}?subject=${encodeURIComponent('Kluda Merchant Support Request - ' + (auth.current_store?.name || 'Store Owner'))}`"
            class="block w-full"
          >
            <UButton
              block
              variant="outline"
              color="neutral"
              class="font-bold border-default hover:bg-accented"
            >
              <UIcon name="i-lucide-send" class="w-4 h-4 mr-1.5 text-indigo-400" />
              Send Email
            </UButton>
          </a>
          <UButton
            v-if="contact.email"
            block
            variant="ghost"
            color="neutral"
            size="xs"
            class="text-xs text-dimmed hover:text-highlighted"
            @click="copyToClipboard(contact.email, 'Email Address')"
          >
            <UIcon name="i-lucide-copy" class="w-3.5 h-3.5 mr-1" />
            Copy Email Address
          </UButton>
        </div>
      </div>
    </div>

    <!-- Office Location & Operational Information (if available) -->
    <div
      v-if="contact.address || contact.hours"
      class="rounded-2xl border border-default bg-elevated p-5 sm:p-6 shadow-xs"
    >
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div v-if="contact.address" class="flex items-start gap-3.5">
          <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center shrink-0 mt-0.5">
            <UIcon name="i-lucide-map-pin" class="w-5 h-5" />
          </div>
          <div>
            <h4 class="text-sm font-bold text-highlighted">Physical Office Location</h4>
            <p class="text-xs text-muted mt-0.5 leading-relaxed">
              {{ contact.address }}
            </p>
          </div>
        </div>

        <div v-if="contact.hours" class="flex items-start gap-3.5">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
            <UIcon name="i-lucide-clock" class="w-5 h-5" />
          </div>
          <div>
            <h4 class="text-sm font-bold text-highlighted">Support Working Hours</h4>
            <p class="text-xs text-muted mt-0.5 leading-relaxed">
              {{ contact.hours }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Official Social Media Channels (Strictly checks for valid, non-null, non-empty URLs) -->
    <div
      v-if="activeSocials.length > 0"
      class="rounded-2xl border border-default bg-elevated p-5 sm:p-6 space-y-4 shadow-xs"
    >
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-bold text-highlighted">
            Connect with Kluda on Social Media
          </h3>
          <p class="text-xs text-muted mt-0.5">
            Follow platform product announcements, release notes, and community updates.
          </p>
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 pt-1">
        <a
          v-for="social in activeSocials"
          :key="social.key"
          :href="social.url"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center gap-3 p-3 rounded-xl border border-default bg-(--ui-bg) hover:bg-accented transition group shadow-2xs cursor-pointer"
        >
          <div
            class="w-8 h-8 rounded-lg flex items-center justify-center border transition"
            :class="social.color"
          >
            <UIcon :name="social.icon" class="w-4 h-4" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-bold text-highlighted truncate group-hover:text-amber-400 transition">
              {{ social.name }}
            </p>
            <span class="text-[10px] text-dimmed flex items-center gap-0.5">
              Open link
              <UIcon name="i-lucide-arrow-up-right" class="w-3 h-3" />
            </span>
          </div>
        </a>
      </div>
    </div>

    <!-- Quick Help & Self-Service FAQs -->
    <div class="rounded-2xl border border-default bg-elevated p-5 sm:p-6 space-y-4 shadow-xs">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center justify-center">
          <UIcon name="i-lucide-help-circle" class="w-4 h-4" />
        </div>
        <div>
          <h3 class="text-base font-bold text-highlighted">Frequently Asked Questions</h3>
          <p class="text-xs text-muted">Quick solutions to common questions before reaching out.</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
        <div
          v-for="(faq, i) in faqs"
          :key="i"
          class="p-4 rounded-xl border border-default bg-(--ui-bg)/60 space-y-2"
        >
          <p class="text-xs font-bold text-highlighted flex items-start gap-2">
            <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{{ faq.q }}</span>
          </p>
          <p class="text-xs text-muted leading-relaxed pl-6">
            {{ faq.a }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
