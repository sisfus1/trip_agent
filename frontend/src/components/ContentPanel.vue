<script setup>
import PlaceCard from './PlaceCard.vue'

defineProps({
  cards: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close'])
</script>

<template>
  <div class="flex flex-col h-full bg-neutral-50 dark:bg-[#1a1a1a] border-l border-neutral-200 dark:border-neutral-800 transition-colors duration-200">
    <!-- Panel header -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
      <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">推荐目的地</h3>
      <button
        @click="emit('close')"
        class="p-1 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
        title="关闭面板"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Cards list -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <PlaceCard
        v-for="(card, idx) in cards"
        :key="idx"
        :card="card"
      />
      <div v-if="!cards.length" class="flex items-center justify-center h-full">
        <p class="text-sm text-neutral-400 dark:text-neutral-500">暂无推荐内容</p>
      </div>
    </div>
  </div>
</template>
