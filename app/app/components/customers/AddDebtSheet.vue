<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  preselectedCustomerId?: string
}>()

const emit = defineEmits<{
  (e: 'debt-added'): void
}>()

const toast = useToast()
const customerStore = useCustomerStore()
const {customers} = storeToRefs(customerStore)

const isSubmitting = ref(false)
const selectedCustomerId = ref<string>('')
const amountNaira = ref<number | null>(null)
const note = ref('')
const staffNote = ref('')

watch(
  () => [open.value, props.preselectedCustomerId],
  ([isOpen, preId]) => {
    if (isOpen) {
      selectedCustomerId.value = (preId as string) || ''
      amountNaira.value = null
      note.value = ''
      staffNote.value = ''
    }
  },
  { immediate: true }
)

const customerOptions = computed(() => {
  return customers.value.map((c) => ({
    label: `${c.fullname} (${c.phone || 'No phone'})`,
    value: c.customer_id,
  }))
})

async function handleSubmit() {
  if (!selectedCustomerId.value) {
    toast.add({
      title: 'Customer Required',
      description: 'Please select a customer to record debt for',
      color: 'warning',
    })
    return
  }

  if (!amountNaira.value || amountNaira.value <= 0) {
    toast.add({
      title: 'Invalid Amount',
      description: 'Please enter a valid debt amount greater than 0',
      color: 'warning',
    })
    return
  }

  isSubmitting.value = true
  try {
    const amountKobo = Math.round(Number(amountNaira.value) * 100)
    await customerStore.addDebt({
      customer_id: selectedCustomerId.value,
      amount: amountKobo,
      note: note.value.trim() || undefined,
      staff_note: staffNote.value.trim() || undefined,
    })

    toast.add({
      title: 'Debt recorded',
      description: `Debt of ₦${Number(amountNaira.value).toLocaleString()} recorded successfully`,
      color: 'success',
      icon: 'i-lucide-check-circle',
    })

    open.value = false
    emit('debt-added')
  } catch (err: any) {
    toast.add({
      title: 'Failed to record debt',
      description: err?.data?.detail ?? 'Unknown server error',
      color: 'error',
      icon: 'i-lucide-alert-circle',
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AppBottomSheet
    v-model="open"
    title="Record Debt"
    description="Manually record a debt or credit balance for a customer."
  >
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <UFormField label="Select Customer" required>
        <USelect
          v-model="selectedCustomerId"
          :items="customerOptions"
          value-key="value"
          label-key="label"
    
          placeholder="Choose customer..."
          class="w-full"
        />
      </UFormField>

      <UFormField label="Debt Amount (₦)" required>
        <UInput
          v-model.number="amountNaira"
          type="number"
          min="1"
          step="0.01"
          placeholder="0.00"
          icon="i-lucide-banknote"
          autofocus
        />
      </UFormField>

      <UFormField label="Note / Reason">
        <UInput
          v-model="note"
          placeholder="e.g. Bought provisions on credit, lent cash from till..."
        />
      </UFormField>

      <div class="flex justify-end gap-2 pt-2">
        <UButton
          variant="outline"
          color="neutral"
          type="button"
          @click="open = false"
        >
          Cancel
        </UButton>
        <UButton :loading="isSubmitting" type="submit" color="primary">
          <UIcon name="i-lucide-plus" class="size-4 mr-1" />
          Record Debt
        </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
