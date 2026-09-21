import { ref } from 'vue'

interface AndroidToastState {
  show: boolean
  message: string
  icon?: string
}

const toastState = ref<AndroidToastState>({
  show: false,
  message: '',
  icon: undefined
})

let timer: any = null

export function useAndroidToast() {
  function showToast(message: string, icon?: string, duration = 2200) {
    if (timer) clearTimeout(timer)
    toastState.value = {
      show: true,
      message,
      icon
    }
    timer = setTimeout(() => {
      toastState.value.show = false
    }, duration)
  }

  return {
    toastState,
    showToast
  }
}
