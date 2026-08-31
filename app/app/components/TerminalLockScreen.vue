<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { db, type LocalStaffMember } from "~/utils/db";

const auth = useAuthStore();
const { isTerminalLocked, unlockTerminal, verifyStaffPin } = usePinAuth();

const enteredPin = ref("");
const isChecking = ref(false);
const isShaking = ref(false);
const errorMessage = ref("");
const maxPinLength = 4;

const currentUser = computed(() => {
  return auth.staff;
});

const displayName = computed(() => {
  if (!auth.staff) return "Terminal User";
  return `${auth.staff.first_name || ""} ${auth.staff.last_name || ""}`.trim() || auth.staff.role || "Staff";
});

const roleLabel = computed(() => {
  if (!auth.staff) return "";
  return auth.staff.role === "owner" ? "Store Owner" : "Cashier / Staff";
});

function handleNumber(num: string) {
  if (enteredPin.value.length < maxPinLength && !isChecking.value) {
    enteredPin.value += num;
    errorMessage.value = "";
    if (enteredPin.value.length === maxPinLength) {
      setTimeout(() => {
        submitPin();
      }, 150);
    }
  }
}

function handleBackspace() {
  if (enteredPin.value.length > 0 && !isChecking.value) {
    enteredPin.value = enteredPin.value.slice(0, -1);
    errorMessage.value = "";
  }
}

function handleClear() {
  enteredPin.value = "";
  errorMessage.value = "";
}

function triggerError(msg: string) {
  errorMessage.value = msg;
  isShaking.value = true;
  if (typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate([80, 50, 80]);
  }
  setTimeout(() => {
    isShaking.value = false;
    enteredPin.value = "";
  }, 600);
}

async function submitPin() {
  if (enteredPin.value.length !== maxPinLength) return;
  isChecking.value = true;

  try {
    let target: LocalStaffMember | undefined = undefined;
    if (auth.staff?.staff_id) {
      target = await db.staffMembers.get(auth.staff.staff_id);
    }

    if (!target && auth.staff) {
      target = {
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
      };
    }

    if (!target || !target.pin_hash || !target.pin_salt) {
      unlockTerminal();
      return;
    }

    const isValid = await verifyStaffPin(enteredPin.value, target);
    if (isValid) {
      enteredPin.value = "";
      errorMessage.value = "";
      unlockTerminal();
    } else {
      triggerError("Incorrect PIN. Please try again.");
    }
  } catch (err) {
    triggerError("Verification failed. Please try again.");
  } finally {
    isChecking.value = false;
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (!isTerminalLocked.value) return;
  if (e.key >= "0" && e.key <= "9") {
    handleNumber(e.key);
  } else if (e.key === "Backspace") {
    handleBackspace();
  } else if (e.key === "Escape" || e.key === "c" || e.key === "C") {
    handleClear();
  }
}

onMounted(() => {
  if (typeof window !== "undefined") {
    window.addEventListener("keydown", handleKeyDown);
  }
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("keydown", handleKeyDown);
  }
});

function handleLogout() {
  unlockTerminal();
  auth.logout(true);
}
</script>

<template>
  <Transition name="lock-fade">
    <div
      v-if="isTerminalLocked && auth.isLoggedIn"
      class="fixed inset-0 z-[999999] flex flex-col items-center justify-between bg-zinc-950 text-white p-6 select-none overflow-y-auto"
    >
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div class="w-full max-w-sm flex items-center justify-between z-10 pt-2">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl bg-zinc-900 border border-emerald-500/30 flex items-center justify-center shadow-lg shadow-emerald-500/10">
            <UIcon name="i-lucide-shield-check" class="size-4 text-emerald-400" />
          </div>
          <span class="text-xs font-bold tracking-wider uppercase text-zinc-400">Terminal Locked</span>
        </div>

        <button
          type="button"
          class="text-xs font-semibold text-zinc-400 hover:text-white transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-zinc-900 border border-transparent hover:border-zinc-800"
          @click="handleLogout"
        >
          <UIcon name="i-lucide-log-out" class="size-3.5" />
          <span>Switch User</span>
        </button>
      </div>

      <div class="w-full max-w-xs flex flex-col items-center my-auto z-10 py-6">
        <div class="relative mb-4">
          <div class="w-20 h-20 rounded-3xl bg-gradient-to-tr from-zinc-900 to-zinc-800 border-2 border-emerald-500/40 flex items-center justify-center text-2xl font-black text-emerald-400 shadow-2xl shadow-emerald-500/20 ring-4 ring-emerald-500/10">
            {{ displayName.charAt(0).toUpperCase() }}
          </div>
          <div class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 text-zinc-950 flex items-center justify-center font-bold text-[10px] shadow-lg border-2 border-zinc-950">
            <UIcon name="i-lucide-lock" class="size-3 stroke-[2.5]" />
          </div>
        </div>

        <h2 class="text-xl font-bold text-white tracking-tight text-center">
          {{ displayName }}
        </h2>
        <p class="text-xs text-zinc-400 font-medium mt-0.5 tracking-wide">
          {{ roleLabel }}
        </p>

        <div class="flex items-center justify-center gap-4 my-6" :class="{ 'animate-shake': isShaking }">
          <div
            v-for="i in 4"
            :key="i"
            class="w-4 h-4 rounded-full transition-all duration-200"
            :class="[
              enteredPin.length >= i
                ? 'bg-emerald-400 scale-110 shadow-lg shadow-emerald-500/50 ring-2 ring-emerald-400/30'
                : 'bg-zinc-800 border border-zinc-700'
            ]"
          />
        </div>

        <p v-if="errorMessage" class="text-xs font-semibold text-rose-400 text-center mb-4 animate-bounce">
          {{ errorMessage }}
        </p>
        <p v-else class="text-xs text-zinc-500 text-center mb-4">
          Enter your 4-digit PIN to unlock
        </p>

        <div class="grid grid-cols-3 gap-3 w-full max-w-[280px]">
          <button
            v-for="n in ['1', '2', '3', '4', '5', '6', '7', '8', '9']"
            :key="n"
            type="button"
            class="h-16 rounded-2xl bg-zinc-900/90 hover:bg-zinc-800 active:scale-95 border border-zinc-800/80 hover:border-zinc-700 text-xl font-semibold text-zinc-100 flex items-center justify-center transition-all shadow-sm"
            @click="handleNumber(n)"
          >
            {{ n }}
          </button>

          <button
            type="button"
            class="h-16 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900 active:scale-95 border border-transparent text-xs font-bold uppercase tracking-wider text-zinc-400 hover:text-zinc-200 flex items-center justify-center transition-all"
            @click="handleClear"
          >
            Clear
          </button>

          <button
            type="button"
            class="h-16 rounded-2xl bg-zinc-900/90 hover:bg-zinc-800 active:scale-95 border border-zinc-800/80 hover:border-zinc-700 text-xl font-semibold text-zinc-100 flex items-center justify-center transition-all shadow-sm"
            @click="handleNumber('0')"
          >
            0
          </button>

          <button
            type="button"
            class="h-16 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900 active:scale-95 border border-transparent text-zinc-400 hover:text-zinc-200 flex items-center justify-center transition-all"
            @click="handleBackspace"
          >
            <UIcon name="i-lucide-delete" class="size-5" />
          </button>
        </div>
      </div>

      <div class="text-[11px] text-zinc-600 text-center z-10 pb-2">
        Protected with Secure Local Authentication
      </div>
    </div>
  </Transition>
</template>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}

.animate-shake {
  animation: shake 0.4s ease-in-out;
}

.lock-fade-enter-active,
.lock-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.lock-fade-enter-from,
.lock-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
