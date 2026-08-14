<script setup lang="ts">
const props = defineProps<{
  title: string
  value: string | number
  subtitle?: string
  icon: string
  trend?: number
  color?: 'green' | 'blue' | 'amber' | 'rose' | 'violet'
}>()

const colorClasses = computed<{ bg: string; text: string; icon: string }>(() => {
  const map: Record<'green' | 'blue' | 'amber' | 'rose' | 'violet', { bg: string, text: string, icon: string }> = {
    green: { bg: 'bg-green-500/10', text: 'text-green-600 dark:text-green-400', icon: 'bg-green-500/15' },
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-600 dark:text-blue-400', icon: 'bg-blue-500/15' },
    amber: { bg: 'bg-amber-500/10', text: 'text-amber-600 dark:text-amber-400', icon: 'bg-amber-500/15' },
    rose: { bg: 'bg-rose-500/10', text: 'text-rose-600 dark:text-rose-400', icon: 'bg-rose-500/15' },
    violet: { bg: 'bg-violet-500/10', text: 'text-violet-600 dark:text-violet-400', icon: 'bg-violet-500/15' }
  }
  return map[props.color || 'green']
})
</script>

<template>
  <div class="card-hover rounded-xl border border-(--ui-border) bg-(--ui-bg-elevated) p-5">
    <div class="flex items-start justify-between">
      <div class="space-y-2">
        <p class="text-sm font-medium text-(--ui-text-muted)">{{ title }}</p>
        <p class="text-2xl font-bold text-(--ui-text-highlighted) animate-count">{{ value }}</p>
        <div v-if="trend !== undefined" class="flex items-center gap-1 text-xs font-medium">
          <UIcon
            :name="trend >= 0 ? 'i-lucide-trending-up' : 'i-lucide-trending-down'"
            :class="[trend >= 0 ? 'text-green-500' : 'text-rose-500', 'w-3.5 h-3.5']"
          />
          <span :class="trend >= 0 ? 'text-green-600 dark:text-green-400' : 'text-rose-600 dark:text-rose-400'">
            {{ Math.abs(trend) }}%
          </span>
          <span class="text-(--ui-text-dimmed)">vs last week</span>
        </div>
        <p v-else-if="subtitle" class="text-xs text-(--ui-text-dimmed)">{{ subtitle }}</p>
      </div>
      <div :class="['flex items-center justify-center w-11 h-11 rounded-xl', colorClasses.icon]">
        <UIcon :name="icon" :class="['w-5 h-5', colorClasses.text]" />
      </div>
    </div>
  </div>
</template>
