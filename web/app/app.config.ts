export default defineAppConfig({
  ui: {
    colors: {
      primary: 'green',
      neutral: 'slate'
    },
    button: {
      defaultVariants: {
        size: 'lg'
      }
    },
    input: {
      slots: {
        root: 'w-full',
        base: "w-full"
      },
      defaultVariants: {
        size: 'lg'
      }
    },
    select: {
      slots: {
        base: 'w-full',
      },
      defaultVariants: {
        size: 'lg'
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
    }
  }
})
