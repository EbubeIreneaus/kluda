<script setup lang="ts">
const { apiFetch } = useAdminApi()
const { hasPermission } = useAdminPermission()
const toast = useToast()

interface FAQItem {
  id: number
  question: string
  answer: string
  category: string
  display_order: number
  is_published: boolean
  created_at: string
  updated_at: string
}

const faqs = ref<FAQItem[]>([])
const isLoading = ref(true)
const isModalOpen = ref(false)
const isSubmitting = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('all')
const editingFaq = ref<FAQItem | null>(null)

const form = reactive({
  question: '',
  answer: '',
  category: 'general',
  display_order: 1,
  is_published: true
})

const categories = [
  { label: 'General', value: 'general' },
  { label: 'Offline & Sync', value: 'offline' },
  { label: 'Hardware & Printers', value: 'hardware' },
  { label: 'Pricing & Billing', value: 'billing' }
]

async function fetchFaqs() {
  isLoading.value = true
  try {
    const data = await apiFetch<FAQItem[]>('/admin/faqs')
    faqs.value = data || []
  } catch (err: any) {
    faqs.value = []
    toast.add({
      title: 'Error loading FAQs',
      description: err?.data?.detail || 'Could not load FAQ records',
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

const filteredFaqs = computed(() => {
  return faqs.value.filter((faq) => {
    const matchesCat = selectedCategory.value === 'all' || faq.category === selectedCategory.value
    const q = searchQuery.value.toLowerCase().trim()
    const matchesSearch = !q || faq.question.toLowerCase().includes(q) || faq.answer.toLowerCase().includes(q)
    return matchesCat && matchesSearch
  })
})

function openCreateModal() {
  editingFaq.value = null
  form.question = ''
  form.answer = ''
  form.category = selectedCategory.value === 'all' ? 'general' : selectedCategory.value
  form.display_order = (faqs.value.length ? Math.max(...faqs.value.map(f => f.display_order)) + 1 : 1)
  form.is_published = true
  isModalOpen.value = true
}

function openEditModal(faq: FAQItem) {
  editingFaq.value = faq
  form.question = faq.question
  form.answer = faq.answer
  form.category = faq.category
  form.display_order = faq.display_order
  form.is_published = faq.is_published
  isModalOpen.value = true
}

async function handleSaveFaq() {
  if (!form.question.trim() || !form.answer.trim()) {
    toast.add({ title: 'Validation Error', description: 'Question and Answer are required.', color: 'warning' })
    return
  }

  isSubmitting.value = true
  try {
    if (editingFaq.value) {
      await apiFetch(`/admin/faqs/${editingFaq.value.id}`, {
        method: 'PUT',
        body: {
          question: form.question.trim(),
          answer: form.answer.trim(),
          category: form.category,
          display_order: Number(form.display_order),
          is_published: form.is_published
        }
      })
      toast.add({ title: 'FAQ Updated', description: 'Changes saved and Redis cache invalidated.', color: 'success' })
    } else {
      await apiFetch('/admin/faqs', {
        method: 'POST',
        body: {
          question: form.question.trim(),
          answer: form.answer.trim(),
          category: form.category,
          display_order: Number(form.display_order),
          is_published: form.is_published
        }
      })
      toast.add({ title: 'FAQ Created', description: 'New question published to marketing site.', color: 'success' })
    }
    isModalOpen.value = false
    await fetchFaqs()
  } catch (err: any) {
    toast.add({
      title: 'Action Failed',
      description: err?.data?.detail || 'Could not save FAQ item.',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

async function togglePublished(faq: FAQItem) {
  try {
    await apiFetch(`/admin/faqs/${faq.id}`, {
      method: 'PUT',
      body: { is_published: !faq.is_published }
    })
    faq.is_published = !faq.is_published
    toast.add({
      title: faq.is_published ? 'FAQ Published' : 'FAQ Un-published',
      description: 'Public cache invalidated.',
      color: 'success'
    })
  } catch (err: any) {
    toast.add({ title: 'Error', description: err?.data?.detail || 'Failed to toggle status.', color: 'error' })
  }
}

async function handleDeleteFaq(faq: FAQItem) {
  if (!confirm(`Are you sure you want to delete this FAQ: "${faq.question}"?`)) return

  try {
    await apiFetch(`/admin/faqs/${faq.id}`, {
      method: 'DELETE'
    })
    toast.add({ title: 'FAQ Deleted', description: 'Item removed from database and cache.', color: 'success' })
    await fetchFaqs()
  } catch (err: any) {
    toast.add({ title: 'Error', description: err?.data?.detail || 'Failed to delete FAQ.', color: 'error' })
  }
}

onMounted(() => {
  fetchFaqs()
})
</script>

<template>
  <div class="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
      <div>
        <h1 class="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
          <UIcon name="i-lucide-help-circle" class="size-7 text-emerald-400" />
          Frequently Asked Questions (CMS)
        </h1>
        <p class="text-xs text-zinc-400 mt-1">
          Manage questions and answers displayed on Kluda's marketing and pricing pages. Cached in Redis for instant performance.
        </p>
      </div>

      <UButton
        v-if="hasPermission('manage:settings')"
        color="primary"
        icon="i-lucide-plus"
        class="font-bold shrink-0 shadow-lg shadow-emerald-500/20"
        @click="openCreateModal"
      >
        Add FAQ Item
      </UButton>
    </div>

    <!-- Filters & Search Bar -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
        <button
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer"
          :class="selectedCategory === 'all' ? 'bg-emerald-500 text-zinc-950 shadow-sm' : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'"
          @click="selectedCategory = 'all'"
        >
          All ({{ faqs.length }})
        </button>
        <button
          v-for="cat in categories"
          :key="cat.value"
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer"
          :class="selectedCategory === cat.value ? 'bg-emerald-500 text-zinc-950 shadow-sm' : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'"
          @click="selectedCategory = cat.value"
        >
          {{ cat.label }}
        </button>
      </div>

      <div class="w-full sm:w-72">
        <UInput
          v-model="searchQuery"
          icon="i-lucide-search"
          placeholder="Search questions..."
          size="sm"
        />
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="isLoading" class="space-y-3">
      <div v-for="i in 4" :key="i" class="h-24 rounded-2xl bg-zinc-900/50 border border-zinc-800 animate-pulse" />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredFaqs.length === 0"
      class="text-center py-16 px-4 rounded-3xl border border-dashed border-zinc-800 bg-zinc-900/30"
    >
      <UIcon name="i-lucide-help-circle" class="size-12 text-zinc-600 mx-auto mb-3" />
      <h3 class="text-base font-bold text-zinc-300">No FAQs Found</h3>
      <p class="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
        No questions match the current filter. Create a new question or adjust your search keywords.
      </p>
    </div>

    <!-- FAQ Items List -->
    <div v-else class="space-y-3">
      <div
        v-for="faq in filteredFaqs"
        :key="faq.id"
        class="p-5 rounded-2xl border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-900/70 transition flex flex-col sm:flex-row sm:items-start justify-between gap-4"
      >
        <div class="space-y-2 flex-1">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-zinc-800 text-zinc-300 border border-zinc-700">
              #{{ faq.display_order }}
            </span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {{ faq.category }}
            </span>
            <button
              type="button"
              class="px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition border"
              :class="faq.is_published ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' : 'bg-rose-500/15 text-rose-300 border-rose-500/30'"
              @click="togglePublished(faq)"
            >
              {{ faq.is_published ? '● Published' : '○ Draft / Hidden' }}
            </button>
          </div>

          <h3 class="text-sm font-bold text-white leading-snug">
            {{ faq.question }}
          </h3>

          <p class="text-xs text-zinc-400 leading-relaxed">
            {{ faq.answer }}
          </p>
        </div>

        <div class="flex items-center gap-1.5 shrink-0 self-end sm:self-start pt-1">
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-edit"
            @click="openEditModal(faq)"
          />
          <UButton
            size="xs"
            variant="ghost"
            color="error"
            icon="i-lucide-trash-2"
            @click="handleDeleteFaq(faq)"
          />
        </div>
      </div>
    </div>

    <!-- Create / Edit Modal -->
    <AdminBottomSheet
      v-model="isModalOpen"
      :title="editingFaq ? 'Edit FAQ Item' : 'Create New FAQ'"
      description="Add or update frequently asked questions for merchants"
      max-width="max-w-lg"
    >
      <form id="faq-form" @submit.prevent="handleSaveFaq" class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Question <span class="text-rose-400">*</span></label>
          <UInput v-model="form.question" placeholder="e.g. Can I use Kluda POS when my shop has no internet?" size="sm" required />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-zinc-300">Category</label>
            <select
              v-model="form.category"
              class="w-full bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            >
              <option v-for="cat in categories" :key="cat.value" :value="cat.value">
                {{ cat.label }}
              </option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-medium text-zinc-300">Display Order</label>
            <UInput v-model.number="form.display_order" type="number" min="1" size="sm" />
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-medium text-zinc-300">Answer Explanation <span class="text-rose-400">*</span></label>
          <textarea
            v-model="form.answer"
            rows="4"
            placeholder="Provide a clear, reassuring answer for retail store merchants..."
            class="w-full bg-zinc-950 border border-zinc-800 text-xs rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500"
            required
          />
        </div>

        <div class="flex items-center justify-between p-3 rounded-xl bg-zinc-950 border border-zinc-800">
          <label class="text-xs font-bold text-zinc-200 flex items-center gap-2 cursor-pointer">
            <input
              v-model="form.is_published"
              type="checkbox"
              class="rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-0 size-4 cursor-pointer"
            />
            Publish to Website immediately
          </label>
          <span class="text-[10px] text-zinc-500">
            {{ form.is_published ? 'Visible to public' : 'Hidden from public' }}
          </span>
        </div>
      </form>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="isModalOpen = false" />
          <UButton
            form="faq-form"
            type="submit"
            label="Save FAQ"
            icon="i-lucide-save"
            color="primary"
            size="sm"
            :loading="isSubmitting"
          />
        </div>
      </template>
    </AdminBottomSheet>
  </div>
</template>
