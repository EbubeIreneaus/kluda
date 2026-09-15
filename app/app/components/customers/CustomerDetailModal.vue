<script setup lang="ts">
import { computed } from 'vue'
import { customerStatusColors, debtStatusColors } from './types'

const open = defineModel<boolean>({ default: false })
const props = defineProps<{
  customer: any
  debts: any[]
}>()

const emit = defineEmits<{
  (e: 'edit', customer: any): void
  (e: 'delete', customerId: string): void
}>()

const { format } = useFormatCurrency()

const activeDebts = computed(() => {
  if (!props.customer?.customer_id || !Array.isArray(props.debts)) return []
  return props.debts.filter(
    (d) => d.customer_id === props.customer.customer_id && d.status !== 'paid'
  )
})
</script>

<template>
  <AppFullScreenModal
    v-model="open"
    :title="customer?.fullname || 'Customer'"
    description="Customer profile and active debt records."
  >
    <div v-if="customer" class="space-y-5">
      <!-- Profile Header -->
      <div class="flex items-center gap-4">
        <UAvatar
          :text="customer.fullname.split(' ').map((n: string) => n[0]).join('')"
          size="lg"
        />
        <div>
          <h3 class="text-lg font-semibold text-(--ui-text-highlighted)">
            {{ customer.fullname }}
          </h3>
          <UBadge
            :color="customerStatusColors[customer.status] as any"
            variant="subtle"
            size="xs"
            class="capitalize"
          >
            {{ customer.status }}
          </UBadge>
        </div>
      </div>

      <!-- Contact Info -->
      <div class="space-y-3 text-sm">
        <div class="flex items-center gap-3 text-(--ui-text-muted)">
          <UIcon name="i-lucide-mail" class="w-4 h-4 text-(--ui-text-dimmed)" />
          {{ customer.email || 'No email provided' }}
        </div>
        <div class="flex items-center gap-3 text-(--ui-text-muted)">
          <UIcon name="i-lucide-phone" class="w-4 h-4 text-(--ui-text-dimmed)" />
          {{ customer.phone }}
        </div>
        <div class="flex items-center gap-3 text-(--ui-text-muted)">
          <UIcon name="i-lucide-map-pin" class="w-4 h-4 text-(--ui-text-dimmed)" />
          {{ customer.address || 'Not Provided' }}
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <UButton
          size="sm"
          variant="soft"
          color="primary"
          icon="i-lucide-pencil"
          @click="emit('edit', customer); open = false"
        >
          Edit
        </UButton>
        <UButton
          size="sm"
          variant="soft"
          color="error"
          icon="i-lucide-user-x"
          @click="emit('delete', customer.customer_id); open = false"
        >
          Deactivate
        </UButton>
      </div>

      <!-- Active Debts Section -->
      <div>
        <p class="text-xs font-medium text-(--ui-text-dimmed) uppercase mb-2">
          Active Debts
        </p>
        <div class="space-y-2">
          <div
            v-for="debt in activeDebts"
            :key="debt.debtor_id"
            class="flex items-center justify-between p-3 rounded-lg bg-(--ui-bg-accented)/50 border border-(--ui-border)"
          >
            <div>
              <p class="text-sm font-medium text-(--ui-text-highlighted)">
                {{ format(debt.amount) }}
              </p>
              <p v-if="debt.note" class="text-xs text-(--ui-text-dimmed)">
                {{ debt.note }}
              </p>
            </div>
            <UBadge :color="debtStatusColors[debt.status] as any" variant="subtle" size="xs">
              {{ debt.status }}
            </UBadge>
          </div>
          <p
            v-if="activeDebts.length === 0"
            class="text-sm text-(--ui-text-dimmed) text-center py-4"
          >
            No active debts
          </p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <UButton variant="outline" color="neutral" @click="open = false">
          Close
        </UButton>
      </div>
    </template>
  </AppFullScreenModal>
</template>
