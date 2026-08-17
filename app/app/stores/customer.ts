import { defineStore } from "pinia";
import { db, type LocalCustomer, type LocalDebtor } from "@/utils/db";

export interface Customer {
  customer_id: string;
  fullname: string;
  phone: string;
  email?: string;
  address?: string;
  created_at: string;
  status: string;
}

export const useCustomerStore = defineStore("customers", () => {
  const customers = ref<LocalCustomer[]>([]);
  const debtors = ref<LocalDebtor[]>([]);
  const loading = ref(false);
  const config = useRuntimeConfig();
  const apiBase = config.public.apiBase;
  const auth = useAuthStore();
  const online = useOnline();

  function getCustomerUrl(path = '') {
    const storeId = auth.store_id || auth.staff?.store_id || ''
    return `${apiBase}/${storeId}/customer${path}`
  }

  function getDebtorUrl(path = '') {
    const storeId = auth.store_id || auth.staff?.store_id || ''
    return `${apiBase}/${storeId}/debt${path}`
  }


  async function fetchCustomers() {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) {
      const cached = await db.customers.toArray()
      if (cached.length > 0) customers.value = cached
      return
    }

    try {
      const response = await $fetch<Customer[]>(getCustomerUrl('/'), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${auth.token ?? ""}`,
        },
      });

      if (response && Array.isArray(response)) {
        const mapped: LocalCustomer[] = response.map((c) => ({
          customer_id: c.customer_id,
          fullname: c.fullname,
          phone: c.phone,
          email: c.email ?? "",
          address: c.address ?? "",
          created_at: c.created_at,
          status: c.status,
        }));
        customers.value = mapped;

        await db.customers.clear();
        if (mapped.length > 0) {
          await db.customers.bulkPut(mapped);
        }

        return mapped;
      }
    } catch (error) {
      console.error("Error fetching customers:", error);
      const cached = await db.customers.toArray();
      if (cached.length > 0) {
        customers.value = cached;
      }
    }
  }

  async function fetchDebtors() {
    const storeId = auth.store_id || auth.staff?.store_id
    if (!storeId) {
      const cached = await db.debtors.toArray()
      if (cached.length > 0) debtors.value = cached
      return
    }

    try {
      const response = await $fetch(getDebtorUrl('/'), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${auth.token ?? ""}`,
        },
      });

      if (response && Array.isArray(response)) {
        const mapped: LocalDebtor[] = response.map((d: any) => ({
          debtor_id: d.debtor_id ?? d.customer_id,
          customer_name: d.customer?.fullname ?? "",
          customer_id: d.customer?.customer_id ?? d.customer_id,
          amount: d.amount,
          note: d.note ?? "",
          status: d.status,
          created_at: d.created_at,
        }));
        debtors.value = mapped;

        await db.debtors.clear();
        if (mapped.length > 0) {
          await db.debtors.bulkPut(mapped);
        }

        return mapped;
      }
    } catch (error) {
      console.error("Error fetching debtors:", error);
      const cached = await db.debtors.toArray();
      if (cached.length > 0) {
        debtors.value = cached;
      }
    }
  }


  async function addCustomer(customerData: Partial<Customer>) {
    loading.value = true;
    try {
      const response = await $fetch<Customer>(getCustomerUrl('/'), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token ?? ""}`,
        },
        body: customerData,
      });

      if (response) {
        const mapped: LocalCustomer = {
          customer_id: response.customer_id,
          fullname: response.fullname,
          email: response.email || "",
          phone: response.phone || "",
          address: response.address || "",
          created_at: response.created_at,
          status: response.status,
        };
        customers.value.unshift(mapped);
        await db.customers.put(mapped);
        return mapped;
      }
    } finally {
      loading.value = false;
    }
  }


  async function updateCustomer(
    customer_id: string,
    data: Partial<LocalCustomer>
  ) {
    loading.value = true;
    try {
      await $fetch(getCustomerUrl(`/${customer_id}`), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token ?? ""}`,
        },
        body: data,
      });

      const idx = customers.value.findIndex(
        (c) => c.customer_id === customer_id
      );
      if (idx !== -1) {
        const updated: LocalCustomer = {
          ...customers.value[idx]!,
          ...data,
        };
        customers.value[idx] = updated;
        await db.customers.put(updated);
      }
    } finally {
      loading.value = false;
    }
  }


  async function deleteCustomer(customer_id: string) {
    loading.value = true;
    try {
      await $fetch(getCustomerUrl(`/${customer_id}`), {
        method: "DELETE",
        credentials: "include",
        headers: { Authorization: `Bearer ${auth.token ?? ""}` },
      });

      const idx = customers.value.findIndex(
        (c) => c.customer_id === customer_id
      );
      if (idx !== -1) {
        if ( await db.customers.get(customer_id)){
          await db.customers.delete(customer_id);
        }
        customers.value.splice(idx, 1)
      }
    } finally {
      loading.value = false;
    }
  }


  async function updateDebtor(
    debtor_id: string,
    data: Partial<LocalDebtor>
  ) {
    loading.value = true;
    try {
      await $fetch(getDebtorUrl(`/${debtor_id}`), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token ?? ""}`,
        },
        body: data,
      });

      const idx = debtors.value.findIndex((d) => d.debtor_id === debtor_id);
      if (idx !== -1) {
        const updated: LocalDebtor = { ...debtors.value[idx]!, ...data };
        debtors.value[idx] = updated;
        await db.debtors.put(updated);
      }
    } finally {
      loading.value = false;
    }
  }

  async function deleteDebtor(debtor_id: string) {
    loading.value = true;
    try {
      await $fetch(getDebtorUrl(`/${debtor_id}`), {
        method: "DELETE",
        headers: { Authorization: `Bearer ${auth.token ?? ""}` },
      });

      const idx = debtors.value.findIndex((d) => d.debtor_id === debtor_id);
      if (idx !== -1) {
        const updated: LocalDebtor = { ...debtors.value[idx]!, status: "paid" };
        debtors.value[idx] = updated;
        await db.debtors.put(updated);
      }
    } finally {
      loading.value = false;
    }
  }

  // ── WebSocket helpers ──────────────────────────────────────────────────

  async function appendCustomerFromWs(raw: any) {
    const c: LocalCustomer = {
      customer_id: raw.customer_id,
      fullname: raw.fullname,
      phone: raw.phone ?? "",
      email: raw.email ?? "",
      address: raw.address ?? "",
      created_at: raw.created_at,
      status: raw.status,
    };
    const exists = customers.value.some((x) => x.customer_id === c.customer_id);
    if (!exists) {
      customers.value.unshift(c);
      await db.customers.put(c);
    }
  }

  async function updateCustomerFromWs(raw: any) {
    const c: LocalCustomer = {
      customer_id: raw.customer_id,
      fullname: raw.fullname,
      phone: raw.phone ?? "",
      email: raw.email ?? "",
      address: raw.address ?? "",
      created_at: raw.created_at,
      status: raw.status,
    };
    const idx = customers.value.findIndex((x) => x.customer_id === c.customer_id);
    if (idx !== -1) {
      customers.value[idx] = c;
    } else {
      customers.value.unshift(c);
    }
    await db.customers.put(c);
  }

  async function removeCustomerFromWs(customer_id: string) {
    const idx = customers.value.findIndex((c) => c.customer_id === customer_id);
    if (idx !== -1) {
      customers.value[idx] = { ...customers.value[idx]!, status: "inactive" };
      await db.customers.put(customers.value[idx]!);
    }
  }

  async function appendDebtFromWs(raw: any) {
    const d: LocalDebtor = {
      debtor_id: raw.debtor_id,
      customer_name: raw.customer?.fullname ?? raw.customer_name ?? "",
      customer_id: raw.customer_id,
      amount: raw.amount,
      note: raw.note ?? "",
      status: raw.status,
      created_at: raw.created_at,
    };
    const exists = debtors.value.some((x) => x.debtor_id === d.debtor_id);
    if (!exists) {
      debtors.value.unshift(d);
      await db.debtors.put(d);
    }
  }

  async function updateDebtFromWs(raw: any) {
    const d: LocalDebtor = {
      debtor_id: raw.debtor_id,
      customer_name: raw.customer?.fullname ?? raw.customer_name ?? "",
      customer_id: raw.customer_id,
      amount: raw.amount,
      note: raw.note ?? "",
      status: raw.status,
      created_at: raw.created_at,
    };
    const idx = debtors.value.findIndex((x) => x.debtor_id === d.debtor_id);
    if (idx !== -1) {
      debtors.value[idx] = d;
    } else {
      debtors.value.unshift(d);
    }
    await db.debtors.put(d);
  }

  async function removeDebtFromWs(debtor_id: string) {
    const idx = debtors.value.findIndex((d) => d.debtor_id === debtor_id);
    if (idx !== -1) {
      debtors.value[idx] = { ...debtors.value[idx]!, status: "paid" };
      await db.debtors.put(debtors.value[idx]!);
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────

  async function init() {
    const customer_cached = await db.customers.toArray();
    customers.value = customer_cached;

    const debtor_cached = await db.debtors.toArray();
    debtors.value = debtor_cached;

    if (online.value) {
      await fetchCustomers();
      await fetchDebtors();
    }
  }

  init();

  return {
    customers,
    debtors,
    loading,
    fetchCustomers,
    fetchDebtors,
    addCustomer,
    updateCustomer,
    deleteCustomer,
    updateDebtor,
    deleteDebtor,
    appendCustomerFromWs,
    updateCustomerFromWs,
    removeCustomerFromWs,
    appendDebtFromWs,
    updateDebtFromWs,
    removeDebtFromWs,
  };
});
