import { ref } from "vue";
import { db, type LocalStaffMember } from "~/utils/db";

export interface PinAuthOptions {
  title?: string;
  description?: string;
  targetStaffId?: string;
  requiredPermission?: string;
}

export interface PinModalState {
  isOpen: boolean;
  title: string;
  description: string;
  targetStaffId?: string;
  requiredPermission?: string;
  resolve?: (value: boolean) => void;
}

const modalState = ref<PinModalState>({
  isOpen: false,
  title: "Enter Terminal PIN",
  description: "Enter your 4-digit PIN to authorize this action",
});

const isSettingPinOpen = ref(false);
const isTerminalLocked = ref(false);

export function usePinAuth() {
  const auth = useAuthStore();
  const { api } = useApi();

  async function computeSha256(pin: string, salt: string): Promise<string> {
    if (
      typeof window === "undefined" ||
      !window.crypto ||
      !window.crypto.subtle
    ) {
      return "";
    }
    const encoder = new TextEncoder();
    const data = encoder.encode(pin + salt);
    const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function verifyStaffPin(
    pin: string,
    staff: LocalStaffMember,
  ): Promise<boolean> {
    if (!staff.pin_hash || !staff.pin_salt) return false;
    const computed = await computeSha256(pin, staff.pin_salt);
    return computed === staff.pin_hash;
  }

  async function syncStaffCredentials(): Promise<void> {
    const storeId = auth.store_id || auth.staff?.store_id;
    if (auth.staff && auth.staff.staff_id && (auth.staff as any).pin_hash) {
      try {
        await db.staffMembers.put({
          staff_id: auth.staff.staff_id,
          first_name: auth.staff.first_name,
          last_name: auth.staff.last_name,
          role: auth.staff.role,
          email: auth.staff.email,
          permission: auth.staff.permission || [],
          pin_hash: (auth.staff as any).pin_hash || null,
          pin_salt: (auth.staff as any).pin_salt || null,
          has_pin: true,
          status: auth.staff.status,
        });
      } catch {}
    }

    if (!storeId || (typeof navigator !== "undefined" && !navigator.onLine))
      return;
    try {
      const staffList = await api<any[]>(`/${storeId}/staff`);
      if (Array.isArray(staffList) && staffList.length > 0) {
        const localMembers: LocalStaffMember[] = staffList
          .filter((s) => s && s.staff_id)
          .map((s) => ({
            staff_id: s.staff_id,
            first_name: s.first_name,
            last_name: s.last_name,
            role: s.role,
            email: s.email,
            permission: s.permission || [],
            pin_hash: s.pin_hash || null,
            pin_salt: s.pin_salt || null,
            has_pin: !!s.has_pin || !!s.pin_hash,
            status: s.status,
          }));
        if (localMembers.length > 0) {
          await db.staffMembers.bulkPut(localMembers);
        }
      }
    } catch {}
  }

  async function setPinOnline(
    pin: string,
  ): Promise<{ success: boolean; message?: string }> {
    const storeId =
      auth.store_id ||
      auth.staff?.store_id ||
      (import.meta.client ? localStorage.getItem("pos_store_id") : null);
    if (!storeId) return { success: false, message: "No store ID found" };
    try {
      const res = await api<{
        status?: string;
        success?: boolean;
        message?: string;
        pin_hash?: string;
        pin_salt?: string;
        has_pin?: boolean;
      }>(`/${storeId}/staff/pin`, {
        method: "POST",
        body: { pin },
      });
      if (
        res?.status === "ok" ||
        res?.success ||
        res?.has_pin ||
        res?.message
      ) {
        if (!auth.staff && import.meta.client) {
          const cached = localStorage.getItem("pos_staff");
          if (cached) {
            try {
              auth.staff = JSON.parse(cached);
            } catch {}
          }
        }
        if (auth.staff) {
          auth.staff.has_pin = true;
          auth.staff.pin_hash = res.pin_hash || null;
          auth.staff.pin_salt = res.pin_salt || null;
          if (import.meta.client) {
            localStorage.setItem("pos_staff", JSON.stringify(auth.staff));
            localStorage.setItem("has_set_pin", "true");
          }
          if (res.pin_hash && res.pin_salt && auth.staff.staff_id) {
            try {
              await db.staffMembers.put({
                staff_id: auth.staff.staff_id,
                first_name: auth.staff.first_name,
                last_name: auth.staff.last_name,
                role: auth.staff.role,
                email: auth.staff.email,
                permission: auth.staff.permission || [],
                pin_hash: res.pin_hash,
                pin_salt: res.pin_salt,
                has_pin: true,
                status: auth.staff.status,
              });
            } catch {}
          }
        }
        if (import.meta.client) {
          localStorage.setItem("has_set_pin", "true");
        }
        return {
          success: true,
          message: res.message || "PIN updated successfully",
        };
      }
      return {
        success: false,
        message: res?.message || "Failed to update PIN",
      };
    } catch (err: any) {
      return {
        success: false,
        message: err?.data?.detail || err?.message || "Failed to update PIN",
      };
    }
  }

  function requirePinAuth(options?: PinAuthOptions): Promise<boolean> {
    if (
      auth.staff &&
      !auth.staff.has_pin &&
      !(auth.staff as any)?.pin_hash &&
      localStorage.getItem("has_set_pin") !== "true"
    ) {
      openSetPinModal();
      return Promise.resolve(false);
    }

    return new Promise((resolve) => {
      modalState.value = {
        isOpen: true,
        title: options?.title || "Enter Terminal PIN",
        description:
          options?.description ||
          "Enter your 4-digit PIN to authorize this action",
        targetStaffId: options?.targetStaffId,
        requiredPermission: options?.requiredPermission,
        resolve,
      };
    });
  }

  async function withPinAuth<T>(
    action: () => T | Promise<T>,
    options?: PinAuthOptions,
  ): Promise<T | null> {
    const isAuthorized = await requirePinAuth(options);
    if (!isAuthorized) return null;
    return await action();
  }

  function checkTerminalLock() {
    if (import.meta.client && auth.isLoggedIn) {
      const isUnlocked = sessionStorage.getItem("pos_unlocked") === "true";
      if (!isUnlocked) {
        isTerminalLocked.value = true;
      }
    }
  }

  function unlockTerminal() {
    if (import.meta.client) {
      sessionStorage.setItem("pos_unlocked", "true");
    }
    isTerminalLocked.value = false;
  }

  function lockTerminal() {
    if (import.meta.client) {
      sessionStorage.removeItem("pos_unlocked");
    }
    isTerminalLocked.value = true;
  }

  function openSetPinModal() {
    isSettingPinOpen.value = true;
  }

  function closeSetPinModal() {
    isSettingPinOpen.value = false;
  }

  return {
    modalState,
    isSettingPinOpen,
    isTerminalLocked,
    computeSha256,
    verifyStaffPin,
    syncStaffCredentials,
    setPinOnline,
    requirePinAuth,
    withPinAuth,
    checkTerminalLock,
    unlockTerminal,
    lockTerminal,
    openSetPinModal,
    closeSetPinModal,
  };
}
