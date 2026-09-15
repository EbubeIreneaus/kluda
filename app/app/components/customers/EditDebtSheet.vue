<script setup lang="ts">
import { ref, watch } from 'vue'
import { debtStatusOptions } from './types'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  debt: any
}>()

const emit = defineEmits<{
  (e: 'debt-updated'): void
}>()

const toast = useToast()
const customerStore = useCustomerStore()

const isSubmitting = ref(false)
const form = ref({
  amountNaira: 0,
  note: '',
  status: 'unpaid',
})

watch(
  () => props.debt,
  (d) => {
    if (d) {
      form.value = {
        amountNaira: (d.amount || 0) / 100,
        note: d.note || '',
        status: d.status || 'unpaid',
      }
    }
  },
  { immediate: true }
)

async function handleSubmit() {
  if (!props.debt?.debtor_id) return

  isSubmitting.value = true
  try {
    const amountKobo = Math.round(Number(form.value.amountNaira) * 100)
    await customerStore.updateDebtor(props.debt.debtor_id, {
      amount: amountKobo,
      status: form.value.status,
      note: form.value.note,
    })
    toast.add({
      title: 'Debt updated',
      description: 'Customer debt updated successfully',
      color: 'success',
      icon: 'i-lucide-check-circle',
    })
    open.value = false
    emit('debt-updated')
  } catch (err: any) {
    toast.add({
      title: 'Failed to update debt',
      description: err?.data?.detail ?? 'Unknown error',
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
    title="Edit Debt"
    description="Update customer balance or debt status."
  >
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <UFormField label="Amount (₦)" required>
        <UInput
          v-model.number="form.amountNaira"
          type="number"
          min="0"
          step="0.01"
          placeholder="0.00"
          icon="i-lucide-banknote"
        />
      </UFormField>
      <UFormField label="Note">
        <UInput v-model="form.note" placeholder="Optional note" />
      </UFormField>
      <UFormField label="Status">
        <USelect
          v-model="form.status"
          :options="debtStatusOptions"
          value-key="value"
          label-key="label"
        />
      </UFormField>
      <div class="flex justify-end gap-2 pt-2">
        <UButton variant="outline" color="neutral" type="button" @click="open = false">
          Cancel
        </UButton>
        <UButton :loading="isSubmitting" type="submit" color="primary">
          Save Changes
        </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
