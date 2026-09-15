import { ref } from "vue";

export interface PinAuthOptions {
  title?: string;
  description?: string;
  requiredPermission?: string;
}

export interface PinModalState {
  isOpen: boolean;
  title: string;
  description: string;
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
const terminalUnlockProof = ref<string | null>(null);

export function getTerminalUnlockProof(): string | null {
  return terminalUnlockProof.value;
}

export function setTerminalUnlockProof(proof: string | null) {
  terminalUnlockProof.value = proof;
}

export function clearTerminalUnlockProof() {
  terminalUnlockProof.value = null;
}

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

  async function verifyPin(pin: string): Promise<boolean> {
    if (!auth.user?.pin_hash || !auth.user?.pin_salt) return false;
    const computed = await computeSha256(pin, auth.user.pin_salt);
    return computed === auth.user.pin_hash;
  }

  async function setPinOnline(
    pin: string,
  ): Promise<{ success: boolean; message?: string }> {
    const storeId =
      auth.store_id ||
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
        if (auth.user) {
          auth.user.has_pin = true;
          auth.user.pin_hash = res.pin_hash || null;
          auth.user.pin_salt = res.pin_salt || null;
          if (import.meta.client) {
            localStorage.setItem("pos_user", JSON.stringify(auth.user));
            localStorage.setItem("has_set_pin", "true");
          }
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
      auth.user &&
      !auth.user.has_pin &&
      !auth.user.pin_hash &&
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

  function unlockTerminal(proof?: string | null) {
    if (import.meta.client) {
      sessionStorage.setItem("pos_unlocked", "true");
    }
    if (proof) {
      terminalUnlockProof.value = proof;
    }
    isTerminalLocked.value = false;
  }

  function lockTerminal() {
    if (import.meta.client) {
      sessionStorage.removeItem("pos_unlocked");
    }
    terminalUnlockProof.value = null;
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
    terminalUnlockProof,
    getTerminalUnlockProof,
    setTerminalUnlockProof,
    clearTerminalUnlockProof,
    computeSha256,
    verifyPin,
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
