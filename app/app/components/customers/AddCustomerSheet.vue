<script setup lang="ts">
import { ref, watch } from "vue";
import { type Customer } from "@/stores/customer";

const open = defineModel<boolean>({ default: false });
const emit = defineEmits<{
  (e: "customer-added"): void;
}>();

const auth = useAuthStore();
const toast = useToast();
const { api } = useApi();
const customerStore = useCustomerStore();

const isSubmitting = ref(false);

const { formData: form, reset: resetForm } = useForm({
  fullname: "",
  email: undefined,
  phone: undefined,
  address: undefined,
});

watch(open, (isOpen) => {
  if (isOpen) {
    resetForm();
  }
});

async function handleSubmit() {
  if (!form.value.fullname.trim()) {
    toast.add({
      title: "Validation Error",
      description: "Customer full name is required",
      color: "warning",
    });
    return;
  }

  isSubmitting.value = true;
  try {
    await customerStore.addCustomer(form.value);
    toast.add({
      title: "Customer added",
      description: form.value.fullname,
      color: "success",
    });
    open.value = false;
    emit("customer-added");
  } catch (error: any) {
    toast.add({
      title: "Failed to add customer",
      description: error.data?.detail || "Unknown server error",
      color: "error",
    });
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <AppBottomSheet
    v-model="open"
    title="Add Customer"
    description="Register a new customer for store sales and credit tracking."
  >
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <UFormField label="Full Name" required>
        <UInput v-model="form.fullname" placeholder="e.g. Adebayo Femi" />
      </UFormField>
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="Email">
          <UInput
            v-model="form.email"
            type="email"
            placeholder="email@example.com"
          />
        </UFormField>
        <UFormField label="Phone" required>
          <UInput v-model="form.phone" placeholder="08012345678" />
        </UFormField>
      </div>
      <UFormField label="Address">
        <UTextarea
          v-model="form.address"
          placeholder="Customer address..."
          :rows="2"
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
        <UButton :loading="isSubmitting" type="submit"> Add Customer </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
