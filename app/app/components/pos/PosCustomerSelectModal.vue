<script setup lang="ts">
import { ref, computed } from "vue";

const props = defineProps<{
  open: boolean;
  customers: any[];
}>();

const emit = defineEmits<{
  (e: "update:open", val: boolean): void;
  (e: "select", customer: any): void;
}>();

const search = ref("");

const filteredCustomers = computed(() => {
  if (!search.value) return props.customers;
  const q = search.value.toLowerCase().trim();
  return props.customers.filter(
    (c) =>
      (c.fullname && c.fullname.toLowerCase().includes(q)) ||
      (c.email && c.email.toLowerCase().includes(q)) ||
      (c.phone && c.phone.includes(q))
  );
});

function handleSelect(customer: any) {
  emit("select", customer);
  emit("update:open", false);
  search.value = "";
}
</script>

<template>
  <AppBottomSheet
    :model-value="open"
    title="Link Customer"
    description="Search and assign a registered customer to this order."
    @update:model-value="emit('update:open', $event)"
  >
    <div class="space-y-4">
      <UInput
        v-model="search"
        placeholder="Search customers by name, phone or email..."
        icon="i-lucide-search"
        autofocus
      />

      <div class="space-y-2 max-h-64 overflow-y-auto">
        <template v-if="filteredCustomers.length === 0">
          <p class="text-xs text-(--ui-text-dimmed) text-center py-6">
            No customers found matching "{{ search }}"
          </p>
        </template>

        <button
          v-for="customer in filteredCustomers"
          :key="customer.customer_id"
          type="button"
          class="flex items-center gap-3 w-full p-3 rounded-lg text-left hover:bg-(--ui-bg-accented) transition cursor-pointer"
          @click="handleSelect(customer)"
        >
          <UAvatar
            :text="
              customer.fullname
                ? customer.fullname
                    .split(' ')
                    .map((n: string) => n[0])
                    .join('')
                : 'C'
            "
            size="sm"
          />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-(--ui-text-highlighted) truncate">
              {{ customer.fullname }}
            </p>
            <p class="text-xs text-(--ui-text-dimmed) truncate">
              {{ customer.phone || 'No phone' }} • {{ customer.email || 'No email' }}
            </p>
          </div>
        </button>
      </div>
    </div>
  </AppBottomSheet>
</template>
