<script setup lang="ts">
import { ref, computed, watch } from "vue";
import {
  customerTabs,
  customerStatusColors,
} from "~/components/customers/types";
import AddCustomerSheet from "~/components/customers/AddCustomerSheet.vue";
import EditCustomerSheet from "~/components/customers/EditCustomerSheet.vue";
import EditDebtSheet from "~/components/customers/EditDebtSheet.vue";
import AddDebtSheet from "~/components/customers/AddDebtSheet.vue";
import CustomerDetailModal from "~/components/customers/CustomerDetailModal.vue";
import DebtsTab from "~/components/customers/DebtsTab.vue";

const auth = useAuthStore();
const { format } = useFormatCurrency();
const toast = useToast();
const customerStore = useCustomerStore();

const { customers, debtors: debts, loading } = storeToRefs(customerStore);

const activeTab = ref<"customers" | "debts">("customers");
const search = ref("");

// Modal States & Selected Items
const showAddModal = ref(false);
const showAddDebtModal = ref(false);
const showEditModal = ref(false);
const showEditDebtModal = ref(false);
const showDetailModal = ref(false);
const showDeleteModal = ref(false);

const selectedCustomer = ref<any>(null);
const selectedDebt = ref<any>(null);
const deletingCustomerId = ref<string | null>(null);
const isDeletingCustomer = ref(false);

// Pagination & Filtering
const currentPage = ref(1);
const pageSize = ref(15);

const filteredCustomers = computed(() => {
  if (!search.value) return customers.value;
  const q = search.value.toLowerCase();
  return customers.value.filter(
    (c) =>
      c.fullname.toLowerCase().includes(q) ||
      (c.email && c.email.toLowerCase().includes(q)) ||
      (c.phone && c.phone.includes(q)),
  );
});

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredCustomers.value.length / pageSize.value)),
);

const paginatedCustomers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredCustomers.value.slice(start, start + pageSize.value);
});

const totalOutstanding = computed(() =>
  debts.value
    .filter((d) => d.status !== "paid")
    .reduce((sum, d) => sum + d.amount, 0),
);

watch([search, activeTab], () => {
  currentPage.value = 1;
});

function openCustomerDetail(customer: any) {
  selectedCustomer.value = customer;
  showDetailModal.value = true;
}

function openEditCustomer(customer: any) {
  selectedCustomer.value = customer;
  showEditModal.value = true;
}

function openDeleteCustomer(id: string) {
  deletingCustomerId.value = id;
  showDeleteModal.value = true;
}

async function handleDeleteCustomer() {
  if (!deletingCustomerId.value) return;
  isDeletingCustomer.value = true;
  try {
    await customerStore.deleteCustomer(deletingCustomerId.value);
    toast.add({ title: "Customer deactivated", color: "success" });
    showDeleteModal.value = false;
    showDetailModal.value = false;
  } catch (err: any) {
    toast.add({
      title: "Failed to deactivate",
      description: err?.data?.detail ?? "Unknown error",
      color: "error",
    });
  } finally {
    isDeletingCustomer.value = false;
  }
}

function openEditDebt(debt: any) {
  selectedDebt.value = debt;
  showEditDebtModal.value = true;
}
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-highlighted">
          Customers &amp; Debts
        </h2>
        <p class="text-sm text-muted">
          {{ customers.length }} customers • Outstanding:
          <span class="text-amber-500 font-semibold">{{
            format(totalOutstanding)
            }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <UButton v-if="activeTab === 'debts'" color="warning" class="p-2.5 cursor-pointer" icon="i-lucide-plus"
          @click="showAddDebtModal = true">
          Record Debt
        </UButton>
        <UButton v-else-if="
          customerStore &&
          (auth.hasPermission('create:customer') ||
            auth.hasPermission('manage:user'))
        " class="p-2.5 cursor-pointer" icon="i-lucide-user-plus" @click="showAddModal = true">
          Add Customer
        </UButton>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div class="flex gap-2">
      <button v-for="tab in customerTabs" :key="tab.value" :class="[
        'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer',
        activeTab === tab.value
          ? 'bg-green-500/10 text-green-600 dark:text-green-400 ring-1 ring-green-500/20'
          : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)',
      ]" @click="activeTab = tab.value as 'customers' | 'debts'">
        <UIcon :name="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Search Input -->
    <UInput v-model="search" :placeholder="activeTab === 'customers'
        ? 'Search customers by name, phone, email...'
        : 'Search debts by customer name...'
      " icon="i-lucide-search" class="max-w-sm" />

    <!-- Tab 1: Customers -->
    <div v-if="activeTab === 'customers'" class="space-y-4">
      <!-- Desktop Table View (>= md) -->
      <div class="hidden md:block rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                  Customer
                </th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                  Contact
                </th>
                <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                  Status
                </th>
                <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              <!-- Empty State -->
              <tr v-if="filteredCustomers.length === 0">
                <td colspan="4" class="text-center py-12 px-4">
                  <UIcon name="i-lucide-user-x" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
                  <p class="text-sm font-semibold text-(--ui-text-highlighted)">
                    No customers found
                  </p>
                  <p class="text-xs text-(--ui-text-dimmed) mt-1">
                    Try adjusting your search query or add a new customer
                  </p>
                </td>
              </tr>

              <!-- Customer Rows -->
              <tr v-for="customer in paginatedCustomers" :key="customer.customer_id"
                class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition cursor-pointer"
                @click="openCustomerDetail(customer)">
                <td class="py-3 px-4">
                  <div class="flex items-center gap-3">
                    <UAvatar :text="customer.fullname
                        .split(' ')
                        .map((n: string) => n[0])
                        .join('')
                      " size="sm" />
                    <div>
                      <p class="font-medium text-(--ui-text-highlighted)">
                        {{ customer.fullname }}
                      </p>
                      <p class="text-xs text-(--ui-text-dimmed)">
                        Since {{ customer.created_at }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <p class="text-xs text-(--ui-text-muted)">
                    {{ customer.email || "—" }}
                  </p>
                  <p class="text-xs text-(--ui-text-dimmed)">
                    {{ customer.phone }}
                  </p>
                </td>
                <td class="py-3 px-4 text-center">
                  <UBadge :color="customerStatusColors[customer.status] as any" variant="subtle" size="xs"
                    class="capitalize">
                    {{ customer.status }}
                  </UBadge>
                </td>
                <td class="py-3 px-4 text-right">
                  <div class="flex items-center justify-end gap-1">
                    <UButton variant="ghost" color="neutral" size="xs" icon="i-lucide-eye" title="View Details"
                      @click.stop="openCustomerDetail(customer)" />
                    <UButton variant="ghost" color="primary" size="xs" icon="i-lucide-pencil" title="Edit"
                      @click.stop="openEditCustomer(customer)" />
                    <UButton variant="ghost" color="error" size="xs" icon="i-lucide-user-x" title="Deactivate"
                      @click.stop="openDeleteCustomer(customer.customer_id)" />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mobile Card List View (< md) -->
      <div class="block md:hidden space-y-3">
        <div v-if="filteredCustomers.length === 0"
          class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)">
          <UIcon name="i-lucide-user-x" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
          <p class="text-sm font-semibold text-(--ui-text-highlighted)">
            No customers found
          </p>
          <p class="text-xs text-(--ui-text-dimmed) mt-1">
            Try adjusting your search query or add a new customer
          </p>
        </div>

        <div v-for="customer in paginatedCustomers" :key="customer.customer_id"
          class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-xs space-y-3">
          <!-- Top: Avatar, Name, Status -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-3 min-w-0">
              <UAvatar :text="customer.fullname
                  .split(' ')
                  .map((n: string) => n[0])
                  .join('')
                " size="md" />
              <div class="min-w-0">
                <h3 class="font-bold text-sm text-(--ui-text-highlighted) truncate">
                  {{ customer.fullname }}
                </h3>
                <p class="text-[11px] text-(--ui-text-dimmed)">
                  Since {{ customer.created_at }}
                </p>
              </div>
            </div>

            <UBadge :color="customerStatusColors[customer.status] as any" variant="subtle" size="xs"
              class="shrink-0 capitalize">
              {{ customer.status }}
            </UBadge>
          </div>

          <!-- Middle: Contact Info -->
          <div class="space-y-1.5 py-2 px-3 rounded-xl bg-(--ui-bg-accented)/30 border border-(--ui-border)/40 text-xs">
            <div v-if="customer.phone" class="flex items-center justify-between gap-2">
              <span class="text-(--ui-text-dimmed) text-[11px] flex items-center gap-1">
                <UIcon name="i-lucide-phone" class="size-3" />
                Phone:
              </span>
              <a :href="`tel:${customer.phone}`" class="font-mono text-emerald-500 font-bold hover:underline">
                {{ customer.phone }}
              </a>
            </div>
            <div v-if="customer.email" class="flex items-center justify-between gap-2">
              <span class="text-(--ui-text-dimmed) text-[11px] flex items-center gap-1">
                <UIcon name="i-lucide-mail" class="size-3" />
                Email:
              </span>
              <a :href="`mailto:${customer.email}`"
                class="text-(--ui-text-highlighted) font-medium truncate max-w-[200px] hover:underline">
                {{ customer.email }}
              </a>
            </div>
            <div v-if="customer.address"
              class="flex items-start justify-between gap-2 pt-1 border-t border-(--ui-border)/30">
              <span class="text-(--ui-text-dimmed) text-[11px] shrink-0">Address:</span>
              <span class="text-(--ui-text-muted) text-right truncate">{{
                customer.address
                }}</span>
            </div>
          </div>

          <!-- Bottom: Action Buttons -->
          <div class="grid grid-cols-3 gap-2 pt-1">
            <UButton variant="outline" color="neutral" size="xs" icon="i-lucide-eye"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openCustomerDetail(customer)">
              Details
            </UButton>
            <UButton variant="outline" color="primary" size="xs" icon="i-lucide-pencil"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openEditCustomer(customer)">
              Edit
            </UButton>
            <UButton variant="outline" color="error" size="xs" icon="i-lucide-user-x"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openDeleteCustomer(customer.customer_id)">
              Delete
            </UButton>
          </div>
        </div>
      </div>

      <!-- Pagination Controls -->
      <div v-if="filteredCustomers.length > pageSize"
        class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 text-xs text-(--ui-text-muted)">
        <p>
          Showing
          <span class="font-bold text-(--ui-text-highlighted)">{{
            (currentPage - 1) * pageSize + 1
            }}</span>
          to
          <span class="font-bold text-(--ui-text-highlighted)">{{
            Math.min(currentPage * pageSize, filteredCustomers.length)
            }}</span>
          of
          <span class="font-bold text-(--ui-text-highlighted)">{{
            filteredCustomers.length
            }}</span>
          customers
        </p>

        <div class="flex items-center gap-1.5">
          <UButton size="xs" variant="outline" color="neutral" icon="i-lucide-chevron-left" :disabled="currentPage <= 1"
            @click="currentPage--">
            Previous
          </UButton>

          <span
            class="px-3 py-1 rounded-lg bg-(--ui-bg-elevated) border border-(--ui-border) font-bold text-(--ui-text-highlighted) font-mono">
            {{ currentPage }} / {{ totalPages }}
          </span>

          <UButton size="xs" variant="outline" color="neutral" trailing-icon="i-lucide-chevron-right"
            :disabled="currentPage >= totalPages" @click="currentPage++">
            Next
          </UButton>
        </div>
      </div>
    </div>

    <!-- Tab 2: Debts -->
    <div v-else-if="activeTab === 'debts'">
      <DebtsTab :debts="debts" :search="search" @edit-debt="openEditDebt" @add-debt="showAddDebtModal = true" />
    </div>

    <!-- Sub-component Modals & Sheets -->
    <AddCustomerSheet v-model="showAddModal" @customer-added="customerStore.fetchCustomers()" />

    <AddDebtSheet v-model="showAddDebtModal"  @debt-added="customerStore.fetchDebtors()" />

    <EditCustomerSheet v-model="showEditModal" :customer="selectedCustomer"
      @customer-updated="customerStore.fetchCustomers()" />

    <EditDebtSheet v-model="showEditDebtModal" :debt="selectedDebt" @debt-updated="customerStore.fetchDebtors()" />

    <CustomerDetailModal v-model="showDetailModal" :customer="selectedCustomer" :debts="debts" @edit="openEditCustomer"
      @delete="openDeleteCustomer" />

    <!-- Customer Deactivate Confirm Modal -->
    <UModal v-model:open="showDeleteModal" title="Deactivate Customer">
      <template #body>
        <div class="p-5 space-y-4">
          <p class="text-sm text-(--ui-text-muted)">
            This will mark the customer as <strong>inactive</strong>. They will
            not be deleted from the database.
          </p>
          <div class="flex justify-end gap-2">
            <UButton variant="outline" color="neutral" @click="showDeleteModal = false">
              Cancel
            </UButton>
            <UButton color="error" :loading="isDeletingCustomer" @click="handleDeleteCustomer">
              Delete
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
