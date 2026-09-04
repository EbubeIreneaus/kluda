<script setup lang="ts">
import { type Customer } from "@/stores/customer";

const auth = useAuthStore();
const { format } = useFormatCurrency();
const toast = useToast();
const { api } = useApi();

const isAddingCustomer = ref(false);
const activeTab = ref("customers");
const search = ref("");

const showAddModal = ref(false);

const showEditModal = ref(false);
const editingCustomer = ref<any>(null);

const isDeletingCustomer = ref(false);
const showDeleteModal = ref(false);
const deletingCustomerId = ref<string | null>(null);

const showDetailSlideover = ref(false);
const selectedCustomer = ref<any>(null);

const showEditDebtModal = ref(false);
const editingDebt = ref<any>(null);
const isSavingDebt = ref(false);

const isMarkingPaid = ref<string | null>(null);

const customerStore = useCustomerStore();
const {
  customers,
  debtors: debts,
  loading,
} = storeToRefs(customerStore);

const { formData: newCustomer, reset: resetNewCustomerForm, empties: emptiesCustomerValue } = useForm({
  fullname: "",
  email: "",
  phone: "",
  address: "",
});

const editForm = ref({
  fullname: "",
  phone: "",
  email: "",
  address: "",
  status: "active",
});

function openEditCustomer(customer: any) {
  editingCustomer.value = customer;
  editForm.value = {
    fullname: customer.fullname,
    phone: customer.phone,
    email: customer.email,
    address: customer.address,
    status: customer.status,
  };
  showEditModal.value = true;
}

async function handleEditCustomer() {
  if (!editingCustomer.value) return;
  try {
    loading.value = true;
    await customerStore.updateCustomer(editingCustomer.value.customer_id, editForm.value);
    toast.add({ title: "Customer updated", color: "success" });
    showEditModal.value = false;
  } catch (err: any) {
    toast.add({
      title: "Failed to update",
      description: err?.data?.detail ?? "Unknown error",
      color: "error",
    });
  } finally {
    loading.value = false;
  }
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
    showDetailSlideover.value = false;
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

async function handleAddCustomer() {
  if (emptiesCustomerValue.value.includes("fullname")) return;
  isAddingCustomer.value = true;
  try {
    const res = await api<Customer>(`/${auth.store_id}/customer`, { method: "POST", body: newCustomer.value });
    customerStore.addCustomer(res);
    toast.add({
      title: "Customer added",
      description: newCustomer.value.fullname,
      color: "success",
    });
    showAddModal.value = false;
    resetNewCustomerForm();
  } catch (error: any) {
    toast.add({
      title: "Failed to add customer",
      description: error.data?.detail || "Unknown server error",
      color: "error",
    });
  } finally {
    isAddingCustomer.value = false;
  }
}

function openEditDebt(debt: any) {
  editingDebt.value = { ...debt };
  showEditDebtModal.value = true;
}

async function handleEditDebt() {
  if (!editingDebt.value) return;
  isSavingDebt.value = true;
  try {
    await customerStore.updateDebtor(editingDebt.value.debtor_id, {
      amount: editingDebt.value.amount,
      status: editingDebt.value.status,
      note: editingDebt.value.note,
    });
    toast.add({ title: "Debt updated", color: "success" });
    showEditDebtModal.value = false;
  } catch (err: any) {
    toast.add({
      title: "Failed to update debt",
      description: err?.data?.detail ?? "Unknown error",
      color: "error",
    });
  } finally {
    isSavingDebt.value = false;
  }
}

async function markAsPaid(debt: any) {
  isMarkingPaid.value = debt.debtor_id;
  try {
    await customerStore.deleteDebtor(debt.debtor_id);
    toast.add({
      title: "Debt resolved",
      description: `${debt.customer_name} — ${format(debt.amount)}`,
      color: "success",
    });
  } catch (err: any) {
    toast.add({
      title: "Failed to mark as paid",
      description: err?.data?.detail ?? "Unknown error",
      color: "error",
    });
  } finally {
    isMarkingPaid.value = null;
  }
}

const filteredCustomers = computed(() => {
  if (!search.value) return customers.value;
  const q = search.value.toLowerCase();
  return customers.value.filter(
    (c) =>
      c.fullname.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      c.phone.includes(q)
  );
});

const currentPage = ref(1);
const pageSize = ref(15);

const totalPages = computed(() => Math.max(1, Math.ceil(filteredCustomers.value.length / pageSize.value)));

const paginatedCustomers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredCustomers.value.slice(start, start + pageSize.value);
});

watch([search, activeTab], () => {
  currentPage.value = 1;
});

const filteredDebts = computed(() => {
  if (!search.value) return debts.value;
  const q = search.value.toLowerCase();
  return debts.value.filter(
    (d) =>
      d.customer_name.toLowerCase().includes(q) ||
      d.debtor_id.toLowerCase().includes(q)
  );
});

const totalOutstanding = computed(() =>
  debts.value
    .filter((d) => d.status !== "paid")
    .reduce((sum, d) => sum + d.amount, 0)
);

function openCustomerDetail(customer: any) {
  selectedCustomer.value = customer;
  showDetailSlideover.value = true;
}

const debtStatusColors: Record<string, string> = {
  unpaid: "warning",
  overdue: "error",
  paid: "success",
};

const customerStatusColors: Record<string, string> = {
  active: "success",
  inactive: "neutral",
};

const tabs = [
  { label: "Customers", value: "customers", icon: "i-lucide-users" },
  { label: "Debts", value: "debts", icon: "i-lucide-banknote" },
];

const statusOptions = [
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
];

const debtStatusOptions = [
  { label: "Unpaid", value: "unpaid" },
  { label: "Overdue", value: "overdue" },
  { label: "Paid", value: "paid" },
];
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-bold text-highlighted">Customers &amp; Debts</h2>
        <p class="text-sm text-muted">
          {{ customers.length }} customers • Outstanding:
          <span class="text-amber-500 font-semibold">{{ format(totalOutstanding) }}</span>
        </p>
      </div>
      <UButton class="p-2.5" v-if="customerStore && (auth.hasPermission('create:customer') || auth.hasPermission('manage:user'))" icon="i-lucide-user-plus" @click="showAddModal = true">
        Add Customer
      </UButton>
    </div>

    <div class="flex gap-2">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
          activeTab === tab.value
            ? 'bg-green-500/10 text-green-600 dark:text-green-400 ring-1 ring-green-500/20'
            : 'text-(--ui-text-muted) hover:bg-(--ui-bg-accented)',
        ]"
        @click="activeTab = tab.value"
      >
        <UIcon :name="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
      </button>
    </div>

    <UInput
      v-model="search"
      :placeholder="activeTab === 'customers' ? 'Search customers...' : 'Search debts...'"
      icon="i-lucide-search"
      class="max-w-sm"
    />

    <div v-if="activeTab === 'customers'" class="space-y-4">
      <!-- Desktop Table View (>= md) -->
      <div class="hidden md:block rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-(--ui-border) bg-(--ui-bg-accented)/30">
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Customer</th>
                <th class="text-left py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Contact</th>
                <th class="text-center py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Status</th>
                <th class="text-right py-3 px-4 font-medium text-(--ui-text-dimmed) text-xs uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="customer in paginatedCustomers"
                :key="customer.customer_id"
                class="border-b border-(--ui-border)/50 last:border-0 hover:bg-(--ui-bg-accented)/30 transition cursor-pointer"
                @click="openCustomerDetail(customer)"
              >
                <td class="py-3 px-4">
                  <div class="flex items-center gap-3">
                    <UAvatar
                      :text="customer.fullname.split(' ').map((n: string) => n[0]).join('')"
                      size="sm"
                    />
                    <div>
                      <p class="font-medium text-(--ui-text-highlighted)">{{ customer.fullname }}</p>
                      <p class="text-xs text-(--ui-text-dimmed)">Since {{ customer.created_at }}</p>
                    </div>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <p class="text-xs text-(--ui-text-muted)">{{ customer.email }}</p>
                  <p class="text-xs text-(--ui-text-dimmed)">{{ customer.phone }}</p>
                </td>
                <td class="py-3 px-4 text-center">
                  <UBadge :color="customerStatusColors[customer.status] as any" variant="subtle" size="xs">
                    {{ customer.status }}
                  </UBadge>
                </td>
                <td class="py-3 px-4 text-right">
                  <div class="flex items-center justify-end gap-1">
                    <UButton
                      variant="ghost"
                      color="neutral"
                      size="xs"
                      icon="i-lucide-eye"
                      @click.stop="openCustomerDetail(customer)"
                    />
                    <UButton
                      variant="ghost"
                      color="primary"
                      size="xs"
                      icon="i-lucide-pencil"
                      @click.stop="openEditCustomer(customer)"
                    />
                    <UButton
                      variant="ghost"
                      color="error"
                      size="xs"
                      icon="i-lucide-user-x"
                      @click.stop="openDeleteCustomer(customer.customer_id)"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mobile Card List View (< md) -->
      <div class="block md:hidden space-y-3">
        <div
          v-if="filteredCustomers.length === 0"
          class="text-center py-12 px-4 rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated)"
        >
          <UIcon name="i-lucide-user-x" class="size-10 text-(--ui-text-dimmed) mx-auto mb-2" />
          <p class="text-sm font-semibold text-(--ui-text-highlighted)">No customers found</p>
          <p class="text-xs text-(--ui-text-dimmed) mt-1">Try adjusting your search query or add a new customer</p>
        </div>

        <div
          v-for="customer in paginatedCustomers"
          :key="customer.customer_id"
          class="rounded-2xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4 shadow-sm space-y-3"
        >
          <!-- Top: Avatar, Name, Status -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-3 min-w-0">
              <UAvatar
                :text="customer.fullname.split(' ').map((n: string) => n[0]).join('')"
                size="md"
              />
              <div class="min-w-0">
                <h3 class="font-bold text-sm text-(--ui-text-highlighted) truncate">
                  {{ customer.fullname }}
                </h3>
                <p class="text-[11px] text-(--ui-text-dimmed)">
                  Since {{ customer.created_at }}
                </p>
              </div>
            </div>

            <UBadge :color="customerStatusColors[customer.status] as any" variant="subtle" size="xs" class="shrink-0 capitalize">
              {{ customer.status }}
            </UBadge>
          </div>

          <!-- Middle: Contact Quick Links (Tap to Call / Email) -->
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
              <a :href="`mailto:${customer.email}`" class="text-(--ui-text-highlighted) font-medium truncate max-w-[200px] hover:underline">
                {{ customer.email }}
              </a>
            </div>
            <div v-if="customer.address" class="flex items-start justify-between gap-2 pt-1 border-t border-(--ui-border)/30">
              <span class="text-(--ui-text-dimmed) text-[11px] shrink-0">Address:</span>
              <span class="text-(--ui-text-muted) text-right truncate">{{ customer.address }}</span>
            </div>
          </div>

          <!-- Bottom: Action Buttons -->
          <div class="grid grid-cols-3 gap-2 pt-1">
            <UButton
              variant="outline"
              color="neutral"
              size="xs"
              icon="i-lucide-eye"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openCustomerDetail(customer)"
            >
              Details
            </UButton>
            <UButton
              variant="outline"
              color="primary"
              size="xs"
              icon="i-lucide-pencil"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openEditCustomer(customer)"
            >
              Edit
            </UButton>
            <UButton
              variant="outline"
              color="error"
              size="xs"
              icon="i-lucide-user-x"
              class="flex items-center justify-center gap-1 py-2 text-xs font-medium rounded-xl"
              @click="openDeleteCustomer(customer.customer_id)"
            >
              Delete
            </UButton>
          </div>
        </div>
      </div>

      <!-- Pagination Controls -->
      <div
        v-if="filteredCustomers.length > pageSize"
        class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 text-xs text-(--ui-text-muted)"
      >
        <p>
          Showing
          <span class="font-bold text-(--ui-text-highlighted)">{{ (currentPage - 1) * pageSize + 1 }}</span>
          to
          <span class="font-bold text-(--ui-text-highlighted)">{{ Math.min(currentPage * pageSize, filteredCustomers.length) }}</span>
          of
          <span class="font-bold text-(--ui-text-highlighted)">{{ filteredCustomers.length }}</span>
          customers
        </p>

        <div class="flex items-center gap-1.5">
          <UButton
            size="xs"
            variant="outline"
            color="neutral"
            icon="i-lucide-chevron-left"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            Previous
          </UButton>

          <span class="px-3 py-1 rounded-lg bg-(--ui-bg-elevated) border border-(--ui-border) font-bold text-(--ui-text-highlighted) font-mono">
            {{ currentPage }} / {{ totalPages }}
          </span>

          <UButton
            size="xs"
            variant="outline"
            color="neutral"
            trailing-icon="i-lucide-chevron-right"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            Next
          </UButton>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'debts'" class="space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4">
          <p class="text-xs text-(--ui-text-dimmed)">Total Outstanding</p>
          <p class="text-xl font-bold text-amber-500 mt-1">{{ format(totalOutstanding) }}</p>
        </div>
        <div class="rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-4">
          <p class="text-xs text-(--ui-text-dimmed)">Unpaid Debts</p>
          <p class="text-xl font-bold text-(--ui-text-highlighted) mt-1">
            {{ debts.filter((d) => d.status === "unpaid").length }}
          </p>
        </div>
      </div>

      <div class="space-y-3">
        <div
          v-for="debt in filteredDebts"
          :key="debt.debtor_id"
          :class="[
            'rounded-xl border p-4 transition-all',
            debt.status === 'overdue'
              ? 'border-rose-500/30 bg-rose-500/5'
              : 'border-(--ui-border) bg-(--ui-bg-elevated)',
          ]"
        >
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <UAvatar
                :text="debt.customer_name.split(' ').map((n: string) => n[0]).join('')"
                size="sm"
              />
              <div>
                <p class="font-medium text-(--ui-text-highlighted)">{{ debt.customer_name }}</p>
                <p v-if="debt.note" class="text-xs text-(--ui-text-dimmed) mt-0.5">{{ debt.note }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-lg font-bold text-(--ui-text-highlighted)">{{ format(debt.amount) }}</p>
              <UBadge :color="debtStatusColors[debt.status] as any" variant="subtle" size="xs">
                {{ debt.status }}
              </UBadge>
            </div>
          </div>
          <div class="flex items-center justify-between mt-3 pt-3 border-t border-(--ui-border)/50">
            <span class="text-xs text-(--ui-text-dimmed)">Created: {{ debt.created_at }}</span>
            <div class="flex items-center gap-2">
              <UButton
                size="xs"
                variant="ghost"
                color="primary"
                icon="i-lucide-pencil"
                @click="openEditDebt(debt)"
              />
              <UButton
                v-if="debt.status !== 'paid'"
                size="xs"
                variant="soft"
                color="success"
                icon="i-lucide-check"
                :loading="isMarkingPaid === debt.debtor_id"
                @click="markAsPaid(debt)"
              >
                Mark Paid
              </UButton>
              <UBadge v-else color="success" variant="subtle" size="xs">
                <UIcon name="i-lucide-check-circle" class="w-3 h-3 mr-1" />
                Resolved
              </UBadge>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AppBottomSheet
      v-model="showAddModal"
      title="Add Customer"
      description="Register a new customer for store sales and credit tracking."
    >
      <form class="space-y-4" @submit.prevent="handleAddCustomer">
        <UFormField label="Full Name" required>
          <UInput v-model="newCustomer.fullname" placeholder="e.g. Adebayo Femi" />
        </UFormField>
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Email">
            <UInput v-model="newCustomer.email" type="email" placeholder="email@example.com" />
          </UFormField>
          <UFormField label="Phone" required>
            <UInput v-model="newCustomer.phone" placeholder="08012345678" />
          </UFormField>
        </div>
        <UFormField label="Address">
          <UTextarea v-model="newCustomer.address" placeholder="Customer address..." :rows="2" />
        </UFormField>
        <div class="flex justify-end gap-2 pt-2">
          <UButton variant="outline" color="neutral" @click="showAddModal = false">Cancel</UButton>
          <UButton :loading="isAddingCustomer" type="submit">Add Customer</UButton>
        </div>
      </form>
    </AppBottomSheet>

    <AppBottomSheet
      v-model="showEditModal"
      title="Edit Customer"
      description="Update contact details or customer status."
    >
      <form class="space-y-4" @submit.prevent="handleEditCustomer">
        <UFormField label="Full Name" required>
          <UInput v-model="editForm.fullname" placeholder="Full name" />
        </UFormField>
        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Email">
            <UInput v-model="editForm.email" type="email" placeholder="email@example.com" />
          </UFormField>
          <UFormField label="Phone">
            <UInput v-model="editForm.phone" placeholder="08012345678" />
          </UFormField>
        </div>
        <UFormField label="Address">
          <UTextarea v-model="editForm.address" placeholder="Customer address..." :rows="2" />
        </UFormField>
        <UFormField label="Status">
          <USelect v-model="editForm.status" :options="statusOptions" value-key="value" label-key="label" />
        </UFormField>
        <div class="flex justify-end gap-2 pt-2">
          <UButton variant="outline" color="neutral" @click="showEditModal = false">Cancel</UButton>
          <UButton :loading="loading" type="submit">Save Changes</UButton>
        </div>
      </form>
    </AppBottomSheet>

    <UModal v-model:open="showDeleteModal" title="Deactivate Customer">
      <template #body>
        <div class="p-5 space-y-4">
          <p class="text-sm text-(--ui-text-muted)">
            This will mark the customer as <strong>inactive</strong>. They will not be deleted from the database.
          </p>
          <div class="flex justify-end gap-2">
            <UButton variant="outline" color="neutral" @click="showDeleteModal = false">Cancel</UButton>
            <UButton color="error" :loading="isDeletingCustomer" @click="handleDeleteCustomer">
              Deactivate
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <AppBottomSheet
      v-model="showEditDebtModal"
      title="Edit Debt"
      description="Update customer balance or debt status."
    >
      <form class="space-y-4" @submit.prevent="handleEditDebt" v-if="editingDebt">
        <UFormField label="Amount (Kobo)">
          <UInput v-model.number="editingDebt.amount" type="number" min="0" />
        </UFormField>
        <UFormField label="Note">
          <UInput v-model="editingDebt.note" placeholder="Optional staff note" />
        </UFormField>
        <UFormField label="Status">
          <USelect v-model="editingDebt.status" :options="debtStatusOptions" value-key="value" label-key="label" />
        </UFormField>
        <div class="flex justify-end gap-2 pt-2">
          <UButton variant="outline" color="neutral" @click="showEditDebtModal = false">Cancel</UButton>
          <UButton :loading="isSavingDebt" type="submit">Save Changes</UButton>
        </div>
      </form>
    </AppBottomSheet>

    <AppFullScreenModal
      v-model="showDetailSlideover"
      :title="selectedCustomer?.fullname || 'Customer'"
      description="Customer profile and active debt records."
    >
      <div v-if="selectedCustomer" class="space-y-5">
        <div class="flex items-center gap-4">
          <UAvatar
            :text="selectedCustomer.fullname.split(' ').map((n: string) => n[0]).join('')"
            size="lg"
          />
          <div>
            <h3 class="text-lg font-semibold text-(--ui-text-highlighted)">
              {{ selectedCustomer.fullname }}
            </h3>
            <UBadge
              :color="customerStatusColors[selectedCustomer.status] as any"
              variant="subtle"
              size="xs"
            >{{ selectedCustomer.status }}</UBadge>
          </div>
        </div>

        <div class="space-y-3 text-sm">
          <div class="flex items-center gap-3 text-(--ui-text-muted)">
            <UIcon name="i-lucide-mail" class="w-4 h-4 text-(--ui-text-dimmed)" />
            {{ selectedCustomer.email }}
          </div>
          <div class="flex items-center gap-3 text-(--ui-text-muted)">
            <UIcon name="i-lucide-phone" class="w-4 h-4 text-(--ui-text-dimmed)" />
            {{ selectedCustomer.phone }}
          </div>
          <div class="flex items-center gap-3 text-(--ui-text-muted)">
            <UIcon name="i-lucide-map-pin" class="w-4 h-4 text-(--ui-text-dimmed)" />
            {{ selectedCustomer.address || "Not Provided" }}
          </div>
        </div>

        <div class="flex gap-2">
          <UButton
            size="sm"
            variant="soft"
            color="primary"
            icon="i-lucide-pencil"
            @click="openEditCustomer(selectedCustomer); showDetailSlideover = false"
          >
            Edit
          </UButton>
          <UButton
            size="sm"
            variant="soft"
            color="error"
            icon="i-lucide-user-x"
            @click="openDeleteCustomer(selectedCustomer.customer_id); showDetailSlideover = false"
          >
            Deactivate
          </UButton>
        </div>

        <div>
          <p class="text-xs font-medium text-(--ui-text-dimmed) uppercase mb-2">Active Debts</p>
          <div class="space-y-2">
            <div
              v-for="debt in debts.filter(
                (d) => d.customer_id === selectedCustomer.customer_id && d.status !== 'paid'
              )"
              :key="debt.debtor_id"
              class="flex items-center justify-between p-3 rounded-lg bg-(--ui-bg-accented)/50"
            >
              <div>
                <p class="text-sm font-medium text-(--ui-text-highlighted)">{{ format(debt.amount) }}</p>
                <p v-if="debt.note" class="text-xs text-(--ui-text-dimmed)">{{ debt.note }}</p>
              </div>
              <UBadge :color="debtStatusColors[debt.status] as any" variant="subtle" size="xs">
                {{ debt.status }}
              </UBadge>
            </div>
            <p
              v-if="!debts.filter((d) => d.customer_id === selectedCustomer.customer_id && d.status !== 'paid').length"
              class="text-sm text-(--ui-text-dimmed) text-center py-4"
            >
              No active debts
            </p>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <UButton variant="outline" color="neutral" @click="showDetailSlideover = false">Close</UButton>
        </div>
      </template>
    </AppFullScreenModal>
  </div>
</template>
