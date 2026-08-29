<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'

const props = withDefaults(
  defineProps<{
    modelValue: string
    variant?: 'dark' | 'email-light'
  }>(),
  {
    variant: 'email-light'
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const { apiFetch } = useAdminApi()
const isUploadingImage = ref(false)

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Underline,
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: 'text-emerald-600 underline font-medium'
      }
    }),
    Image.configure({
      HTMLAttributes: {
        class: 'max-w-full rounded-lg my-3 border border-slate-200 shadow-xs'
      }
    })
  ],
  editorProps: {
    attributes: {
      class: props.variant === 'email-light'
        ? 'focus:outline-none min-h-[360px] p-6 text-slate-800 leading-relaxed font-sans text-sm max-w-none'
        : 'prose prose-invert prose-sm sm:prose-base focus:outline-none min-h-[260px] p-4 text-zinc-100 max-w-none'
    }
  },
  onUpdate: () => {
    if (editor.value) {
      emit('update:modelValue', editor.value.getHTML())
    }
  }
})

watch(() => props.modelValue, (newVal) => {
  if (editor.value && editor.value.getHTML() !== newVal) {
    editor.value.commands.setContent(newVal, false)
  }
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})

function setLink() {
  if (!editor.value) return
  const prevUrl = editor.value.getAttributes('link').href
  const url = window.prompt('Enter URL:', prevUrl)
  if (url === null) return
  if (url === '') {
    editor.value.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }
  editor.value.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

function insertSnippet(type: string) {
  if (!editor.value) return
  if (type === 'callout') {
    editor.value.chain().focus().insertContent(`
      <blockquote style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0;">
        <p style="margin: 0 0 4px 0; font-size: 11px; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">✨ PRO TIP / HIGHLIGHT</p>
        <p style="margin: 0; color: #334155;">Type your key takeaway or critical store update information here.</p>
      </blockquote>
    `).run()
  } else if (type === 'warning') {
    editor.value.chain().focus().insertContent(`
      <div style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #f59e0b; background-color: #fffbeb; border-radius: 0 8px 8px 0;">
        <div style="font-weight: 700; color: #b45309; font-size: 13px; margin-bottom: 4px;">⚠️ Important Notice</div>
        <p style="margin: 0; font-size: 13px; color: #78350f;">Cashier terminals must synchronize before the end of the business day.</p>
      </div>
    `).run()
  } else if (type === 'button') {
    editor.value.chain().focus().insertContent(`
      <p style="margin: 20px 0;">
        <a href="https://app.kluda.app" style="display: inline-block; background-color: #059669; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 14px;">Open Merchant Portal &rarr;</a>
      </p>
    `).run()
  } else if (type === 'table') {
    editor.value.chain().focus().insertContent(`
      <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
        <thead>
          <tr style="background-color: #f8fafc;">
            <th style="border: 1px solid #e2e8f0; padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; color: #0f172a;">Feature</th>
            <th style="border: 1px solid #e2e8f0; padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; color: #0f172a;">Availability</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="border: 1px solid #e2e8f0; padding: 10px 12px; font-size: 13px; color: #334155;">Multi-Counter Offline Sync</td>
            <td style="border: 1px solid #e2e8f0; padding: 10px 12px; font-size: 13px; color: #059669; font-weight: 600;">Enabled</td>
          </tr>
          <tr>
            <td style="border: 1px solid #e2e8f0; padding: 10px 12px; font-size: 13px; color: #334155;">Cloud Receipt Printing</td>
            <td style="border: 1px solid #e2e8f0; padding: 10px 12px; font-size: 13px; color: #059669; font-weight: 600;">All Branches</td>
          </tr>
        </tbody>
      </table>
    `).run()
  }
}

async function handleImageUpload(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files || !target.files[0] || !editor.value) return
  const file = target.files[0]

  isUploadingImage.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await apiFetch<{ url: string }>('/admin/campaigns/media/upload', {
      method: 'POST',
      body: formData
    })
    if (res?.url) {
      editor.value.chain().focus().setImage({ src: res.url }).run()
    }
  } catch {
    alert('Failed to upload image')
  } finally {
    isUploadingImage.value = false
    target.value = ''
  }
}

defineExpose({
  insertSnippet,
  editor
})
</script>

<template>
  <div class="border border-zinc-800 rounded-xl bg-zinc-950 overflow-hidden flex flex-col focus-within:border-emerald-500/50 transition-colors">
    <div v-if="editor" class="flex flex-wrap items-center justify-between gap-1 p-2 bg-zinc-900/90 border-b border-zinc-800 text-xs">
      <div class="flex flex-wrap items-center gap-1">
        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('bold') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Bold"
          @click="editor.chain().focus().toggleBold().run()"
        >
          <UIcon name="i-lucide-bold" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('italic') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Italic"
          @click="editor.chain().focus().toggleItalic().run()"
        >
          <UIcon name="i-lucide-italic" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('underline') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Underline"
          @click="editor.chain().focus().toggleUnderline().run()"
        >
          <UIcon name="i-lucide-underline" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('strike') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Strikethrough"
          @click="editor.chain().focus().toggleStrike().run()"
        >
          <UIcon name="i-lucide-strikethrough" class="w-4 h-4" />
        </button>

        <div class="h-4 w-px bg-zinc-800 mx-1" />

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('heading', { level: 1 }) ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Heading 1"
          @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        >
          <UIcon name="i-lucide-heading-1" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('heading', { level: 2 }) ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Heading 2"
          @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        >
          <UIcon name="i-lucide-heading-2" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('bulletList') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Bullet List"
          @click="editor.chain().focus().toggleBulletList().run()"
        >
          <UIcon name="i-lucide-list" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('orderedList') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Ordered List"
          @click="editor.chain().focus().toggleOrderedList().run()"
        >
          <UIcon name="i-lucide-list-ordered" class="w-4 h-4" />
        </button>

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('blockquote') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Blockquote"
          @click="editor.chain().focus().toggleBlockquote().run()"
        >
          <UIcon name="i-lucide-quote" class="w-4 h-4" />
        </button>

        <div class="h-4 w-px bg-zinc-800 mx-1" />

        <button
          type="button"
          :class="['p-1.5 rounded hover:bg-zinc-800 transition-colors', editor.isActive('link') ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400']"
          title="Insert Link"
          @click="setLink"
        >
          <UIcon name="i-lucide-link" class="w-4 h-4" />
        </button>

        <label class="p-1.5 rounded hover:bg-zinc-800 transition-colors cursor-pointer text-zinc-400 hover:text-emerald-400 flex items-center gap-1" title="Upload & Insert Cloudinary Image">
          <UIcon :name="isUploadingImage ? 'i-lucide-loader-2' : 'i-lucide-image'" :class="['w-4 h-4', isUploadingImage ? 'animate-spin text-emerald-400' : '']" />
          <span class="text-[11px] font-medium hidden sm:inline">Image</span>
          <input type="file" accept="image/*" class="hidden" @change="handleImageUpload" />
        </label>
      </div>

      <div class="flex items-center gap-1">
        <button
          type="button"
          class="p-1.5 rounded hover:bg-zinc-800 transition-colors text-zinc-400"
          title="Undo"
          @click="editor.chain().focus().undo().run()"
        >
          <UIcon name="i-lucide-undo" class="w-4 h-4" />
        </button>

        <button
          type="button"
          class="p-1.5 rounded hover:bg-zinc-800 transition-colors text-zinc-400"
          title="Redo"
          @click="editor.chain().focus().redo().run()"
        >
          <UIcon name="i-lucide-redo" class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div v-if="variant === 'email-light'" class="bg-zinc-950 p-4 md:p-5 flex justify-center overflow-y-auto max-h-[460px]">
      <div class="w-full max-w-[620px] bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden flex flex-col">
        <div class="bg-slate-900 px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-slate-950 text-sm font-mono">K</div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-bold text-white tracking-tight">Kluda</span>
              <span class="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">RETAIL POS</span>
            </div>
          </div>
          <span class="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Email Body Canvas</span>
        </div>

        <div class="tiptap-email-canvas flex-1">
          <EditorContent :editor="editor" />
        </div>

        <div class="bg-slate-50 px-6 py-3 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>&copy; Kluda Inc. All rights reserved.</span>
          <span>Merchant Control Center</span>
        </div>
      </div>
    </div>

    <EditorContent v-else :editor="editor" class="flex-1 overflow-y-auto" />
  </div>
</template>

<style>
.tiptap-email-canvas .tiptap {
  min-height: 320px;
  padding: 24px 28px;
  color: #334155;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
}

.tiptap-email-canvas .tiptap:focus {
  outline: none;
}

.tiptap-email-canvas .tiptap h1 {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 14px 0;
  line-height: 1.3;
}

.tiptap-email-canvas .tiptap h2 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 16px 0 12px 0;
  line-height: 1.3;
}

.tiptap-email-canvas .tiptap h3 {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin: 14px 0 10px 0;
}

.tiptap-email-canvas .tiptap p {
  margin: 0 0 14px 0;
  color: #334155;
}

.tiptap-email-canvas .tiptap strong {
  color: #0f172a;
  font-weight: 600;
}

.tiptap-email-canvas .tiptap ul,
.tiptap-email-canvas .tiptap ol {
  padding-left: 20px;
  margin: 0 0 14px 0;
  color: #334155;
}

.tiptap-email-canvas .tiptap li {
  margin-bottom: 6px;
}

.tiptap-email-canvas .tiptap blockquote {
  margin: 16px 0;
  padding: 12px 16px;
  border-left: 4px solid #059669;
  background-color: #f8fafc;
  color: #1e293b;
  border-radius: 0 8px 8px 0;
}

.tiptap-email-canvas .tiptap table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
}

.tiptap-email-canvas .tiptap th,
.tiptap-email-canvas .tiptap td {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  font-size: 13px;
  color: #334155;
}

.tiptap-email-canvas .tiptap th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #0f172a;
}
</style>
