import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { db, type LocalProduct } from "~/utils/db";

export const useProductsStore = defineStore("products", () => {
  const products = ref<LocalProduct[]>([]);
  const isInitialized = ref(false);
  const isLoading = ref(false);

  const auth = useAuthStore();
  const { api } = useApi();

  async function fetchProducts(search?: string) {
    const storeId = auth.store_id;
    if (!storeId) {
      const localItems = await db.products.toArray();
      if (localItems.length > 0) products.value = localItems;
      return;
    }

    isLoading.value = true;
    try {
      const url = search
        ? `/${storeId}/product?search=${encodeURIComponent(search)}`
        : `/${storeId}/product`;
      const res = await api<any[]>(url);
      if (res && Array.isArray(res)) {
        const mapped: LocalProduct[] = res.map((p: any) => ({
          slug: p.slug,
          name: p.name,
          unit_price: p.unit_price,
          cost_price: p.cost_price || 0,
          max_discount: p.max_discount || 0,
          barcode_id: p.barcode_id || "",
          quantities: p.quantities ?? 0,
          unit_in: p.unit_in || "pcs",
          deleted: p.deleted || false,
          description: p.description || "",
        }));

        products.value = mapped;
        await db.products.clear();
        if (mapped.length > 0) {
          await db.products.bulkPut(mapped);
        }
      }
    } catch (err: any) {
      const statusCode =
        err?.response?.status ?? err?.statusCode ?? err?.status;
      if (statusCode === 401 || statusCode === 403 || statusCode === 422) {
        return;
      }
      const localItems = await db.products.toArray();
      if (localItems.length > 0) {
        products.value = localItems;
      }
    } finally {
      isLoading.value = false;
    }
  }

  async function init() {
    const cached = await db.products.toArray();
    if (cached.length > 0) {
      products.value = cached;
    }

    if (import.meta.client && window.navigator.onLine) {
      await fetchProducts();
    }
    isInitialized.value = true;
  }

  async function deductStock(
    items: {
      stock_slug?: string;
      slug?: string;
      quantities?: number;
      qty?: number;
    }[],
  ) {
    for (const item of items) {
      const slug = item.stock_slug || item.slug;
      const qty = item.quantities ?? item.qty ?? 0;
      if (!slug || qty <= 0) continue;

      const prod = products.value.find((p) => p.slug === slug);
      if (prod) {
        prod.quantities = Math.max(0, prod.quantities - qty);
        await db.products.put(JSON.parse(JSON.stringify(prod)));
      }
    }
  }

  async function addProduct(productData: Partial<LocalProduct>) {
    const storeId = auth.store_id;
    if (!storeId) throw new Error("No store ID");

    try {
      const res = await api<any>(`/${storeId}/product`, {
        method: "POST",
        body: productData,
      });

      if (res) {
        const newProduct: LocalProduct = {
          slug: res.slug,
          name: res.name,
          unit_price: res.unit_price,
          cost_price: res.cost_price || 0,
          max_discount: res.max_discount || 0,
          barcode_id: res.barcode_id || "",
          quantities: res.quantities ?? 0,
          unit_in: res.unit_in || "pcs",
          deleted: res.deleted || false,
          description: res.description || "",
        };

        const exists = products.value.some((p) => p.slug === newProduct.slug);
        if (!exists) {
          products.value.unshift(newProduct);
          await db.products.put(JSON.parse(JSON.stringify(newProduct)));
        }
        return newProduct;
      }
    } catch (err) {
      throw err;
    }
  }

  async function addQuickProduct(data: {
    name: string;
    barcode_id?: string | null;
    unit_price: number;
    cost_price?: number;
    unit_in?: string;
  }): Promise<LocalProduct> {
    const rawBarcode = data.barcode_id ? data.barcode_id.trim() : "";
    const cleanName = data.name.trim();
    const tempSlug = rawBarcode
      ? `quick_${rawBarcode}`
      : `quick_${cleanName.toLowerCase().replace(/[^a-z0-9]/g, "-")}_${Date.now()}`;

    const localProd: LocalProduct = {
      slug: tempSlug,
      name: cleanName,
      unit_price: data.unit_price,
      cost_price: data.cost_price || 0,
      max_discount: 0,
      barcode_id: rawBarcode,
      quantities: 0,
      unit_in: data.unit_in || "piece",
      deleted: false,
      is_offline_new: true,
    };

    // 1. Immediately save to reactive state and local IndexedDB
    const existingIdx = products.value.findIndex(
      (p) =>
        (rawBarcode && p.barcode_id === rawBarcode) ||
        p.slug === tempSlug ||
        p.name.toLowerCase() === cleanName.toLowerCase(),
    );

    if (existingIdx !== -1) {
      products.value[existingIdx] = {
        ...products.value[existingIdx],
        ...localProd,
      };
      await db.products.put(JSON.parse(JSON.stringify(products.value[existingIdx])));
      return products.value[existingIdx];
    } else {
      products.value.unshift(localProd);
      await db.products.put(JSON.parse(JSON.stringify(localProd)));
    }

    // 2. Persist to API if online
    const storeId = auth.store_id;
    if (storeId && typeof navigator !== "undefined" && navigator.onLine) {
      try {
        const res = await api<any>(`/${storeId}/product`, {
          method: "POST",
          body: {
            name: cleanName,
            barcode_id: rawBarcode || undefined,
            unit_price: data.unit_price,
            cost_price: data.cost_price || 0,
            quantities: 0,
            unit_in: data.unit_in || "piece",
          },
        });
        if (res && res.slug) {
          localProd.slug = res.slug;
          localProd.is_offline_new = false;
          // Update in memory and local IndexedDB with true server slug
          const idx = products.value.findIndex(p => p.slug === tempSlug);
          if (idx !== -1) {
            products.value[idx] = { ...localProd };
          }
          await db.products.delete(tempSlug);
          await db.products.put(JSON.parse(JSON.stringify(localProd)));
        }
      } catch {
        // If offline or network downtime, is_offline_new remains true and atomic sales sync will handle creation
      }
    }

    return localProd;
  }

  async function updateProduct(
    slug: string,
    updateData: Partial<LocalProduct>,
  ) {
    const storeId = auth.store_id;
    if (!storeId) throw new Error("No store ID");

    try {
      const res = await api<any>(`/${storeId}/product/${slug}`, {
        method: "PUT",
        body: updateData,
      });

      if (res) {
        const idx = products.value.findIndex((p) => p.slug === slug);
        const updatedProduct: LocalProduct = {
          slug: res.slug || slug,
          name: res.name || updateData.name || "",
          unit_price: res.unit_price ?? updateData.unit_price ?? 0,
          cost_price: res.cost_price ?? updateData.cost_price ?? 0,
          max_discount: res.max_discount ?? updateData.max_discount ?? 0,
          barcode_id: res.barcode_id ?? updateData.barcode_id ?? "",
          quantities: res.quantities ?? updateData.quantities ?? 0,
          unit_in: res.unit_in ?? updateData.unit_in ?? "pcs",
          deleted: res.deleted ?? updateData.deleted ?? false,
          description: res.description ?? updateData.description ?? "",
        };

        if (idx !== -1) {
          products.value[idx] = updatedProduct;
        }
        await db.products.put(updatedProduct);
        return updatedProduct;
      }
    } catch (err) {
      throw err;
    }
  }

  async function adjustStock(payload: {
    stock_slug: string;
    quantity: number;
    action_type: "addition" | "subtract";
    reason: string;
    note?: string;
  }) {
    const storeId = auth.store_id;
    if (!storeId) throw new Error("No store ID");

    try {
      const res = await api<any>(`/${storeId}/product/stock-history`, {
        method: "POST",
        body: payload,
      });
      if (res) {
        const prod = products.value.find((p) => p.slug === payload.stock_slug);
        if (prod) {
          if (payload.action_type === "addition") {
            prod.quantities =
              Number(prod.quantities) + Number(payload.quantity);
          } else {
            prod.quantities = Math.max(
              0,
              Number(prod.quantities) - Number(payload.quantity),
            );
          }
          await db.products.put(JSON.parse(JSON.stringify(prod)));
        }
      }
      return res;
    } catch (err) {
      throw err;
    }
  }

  async function deleteProduct(slug: string) {
    const storeId = auth.store_id;
    if (!storeId) throw new Error("No store ID");

    try {
      await api(`/${storeId}/product/${slug}`, {
        method: "DELETE",
      });
      products.value = products.value.filter((p) => p.slug !== slug);
      await db.products.delete(slug);
    } catch (err) {
      throw err;
    }
  }

  async function fetchStockHistory(slug?: string) {
    const storeId = auth.store_id;
    if (!storeId) return [];

    try {
      const url = slug
        ? `/${storeId}/product/stock-history?slug=${encodeURIComponent(slug)}`
        : `/${storeId}/product/stock-history`;
      return await api<any[]>(url);
    } catch (err) {
      return [];
    }
  }

  function getByBarcode(barcode: string): LocalProduct | undefined {
    if (!barcode) return undefined;
    const clean = barcode.trim().toLowerCase();
    return products.value.find(
      (p) => p.barcode_id && p.barcode_id.trim().toLowerCase() === clean,
    );
  }

  const productCount = computed(
    () => products.value.filter((p) => !p.deleted).length,
  );
  const lowStockProducts = computed(() =>
    products.value.filter((p) => !p.deleted && p.quantities <= 10),
  );

  async function appendFromWs(raw: any) {
    const product: LocalProduct = {
      slug: raw.slug,
      name: raw.name,
      unit_price: raw.unit_price,
      cost_price: raw.cost_price || 0,
      max_discount: raw.max_discount || 0,
      barcode_id: raw.barcode_id || "",
      quantities: raw.quantities ?? 0,
      unit_in: raw.unit_in || "pcs",
      deleted: raw.deleted || false,
      description: raw.description || "",
    };
    const exists = products.value.some((p) => p.slug === product.slug);
    if (!exists) {
      products.value.unshift(product);
      await db.products.put(product);
    }
  }

  async function updateFromWs(raw: any) {
    const product: LocalProduct = {
      slug: raw.slug,
      name: raw.name,
      unit_price: raw.unit_price,
      cost_price: raw.cost_price || 0,
      max_discount: raw.max_discount || 0,
      barcode_id: raw.barcode_id || "",
      quantities: raw.quantities ?? 0,
      unit_in: raw.unit_in || "pcs",
      deleted: raw.deleted || false,
      description: raw.description || "",
    };
    const idx = products.value.findIndex((p) => p.slug === product.slug);
    if (idx !== -1) {
      products.value[idx] = product;
    } else {
      products.value.unshift(product);
    }
    await db.products.put(product);
  }

  async function removeFromWs(slug: string) {
    products.value = products.value.filter((p) => p.slug !== slug);
    await db.products.delete(slug);
  }

  init();

  return {
    products,
    isInitialized,
    isLoading,
    productCount,
    lowStockProducts,
    fetchProducts,
    addProduct,
    addQuickProduct,
    updateProduct,
    deleteProduct,
    adjustStock,
    fetchStockHistory,
    getByBarcode,
    deductStock,
    appendFromWs,
    updateFromWs,
    removeFromWs,
    init,
  };
});

export const useProductStore = useProductsStore;
