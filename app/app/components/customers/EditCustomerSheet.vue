<script setup lang="ts">
import { ref, watch } from "vue";
import { statusOptions } from "./types";

const open = defineModel<boolean>({ default: false });
const props = defineProps<{
  customer: any;
}>();

const emit = defineEmits<{
  (e: "customer-updated"): void;
}>();

const toast = useToast();
const customerStore = useCustomerStore();

const isSubmitting = ref(false);
const { formData: form, reset: resetForm } = useForm({
  fullname: undefined,
  phone: undefined,
  email: undefined,
  address: undefined,
  status: undefined,
});

watch(
  () => props.customer,
  (c) => {
    if (c) {
      form.value = {
        fullname: c.fullname,
        phone: c.phone,
        email: c.email,
        address: c.address,
        status: c.status,
      };
    }
  },
  { immediate: true },
);

async function handleSubmit() {
  if (!props.customer?.customer_id) return;

  isSubmitting.value = true;
  try {
    await customerStore.updateCustomer(props.customer.customer_id, form.value);
    toast.add({ title: "Customer updated", color: "success" });
    resetForm()
    open.value = false;
    emit("customer-updated");
  } catch (err: any) {
    toast.add({
      title: "Failed to update",
      description: err?.data?.detail ?? "Unknown error",
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
    title="Edit Customer"
    description="Update contact details or customer status."
  >
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <UFormField label="Full Name" required>
        <UInput v-model="form.fullname" placeholder="Full name" />
      </UFormField>
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="Email">
          <UInput
            v-model="form.email"
            type="email"
            placeholder="email@example.com"
          />
        </UFormField>
        <UFormField label="Phone">
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
      <UFormField label="Status">
        <USelect
          v-model="form.status"
          :options="statusOptions"
          value-key="value"
          label-key="label"
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
        <UButton :loading="isSubmitting" type="submit"> Save Changes </UButton>
      </div>
    </form>
  </AppBottomSheet>
</template>
