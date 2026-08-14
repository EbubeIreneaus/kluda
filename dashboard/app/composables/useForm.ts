export const useForm = <T extends Record<string, any>>(initialForm: T) => {
  const formData = ref<T>(initialForm);
  const reset = () => {
    formData.value = initialForm;
  };

  const empties = computed(() => {
    const empty_arr: string[] = [];
    Object.keys(formData.value).forEach((key) => {
      if (
        formData.value[key] == null ||
        formData.value[key] == "" ||
        (Array.isArray(formData.value[key]) && formData.value[key].length < 1)
      ) {
        empty_arr.push(key);
      }
    });
    return empty_arr
  });
  return { formData, reset, empties };
};
