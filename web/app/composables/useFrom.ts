
export const useForm = <T extends Record<string, any>>(initialForm: T)=>{
    const form = ref(initialForm)
    const reset = () => {
        form.value = initialForm
    }

    return {form, reset}
}