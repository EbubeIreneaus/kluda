export default defineAppConfig({
  ui: {
    colors: {
      primary: 'green',
      neutral: 'slate'
    },
    button: {
      defaultVariants: {
        size: '2xl'
      }
    },

    input: {
      slots: {
        root: 'w-full',
        base: "w-full min-h-10"
      },
      defaultVariants: {
        size: 'xl'
      }
    },
    select: {
      slots: {
        base: 'w-full min-h-10',
      },
      defaultVariants: {
        size: 'xl'
      }
    },
    textarea: {
      defaultVariants: {
        size: 'lg'
      },
      slots: {
        root: 'w-full',
      }
    },
    formField: {
      defaultVariants: {
        size: 'lg'
      }
    },
  }
})
