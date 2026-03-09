<template>
  <div class="bg-white dark:bg-neutral-800 rounded-xl overflow-hidden border border-neutral-200 dark:border-neutral-700 transition-colors duration-200">
    <!-- Image -->
    <div class="h-40 bg-neutral-100 dark:bg-neutral-700 relative w-full overflow-hidden">
      <img
        v-if="card.image"
        :src="card.image"
        :alt="card.name"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-neutral-100 dark:bg-neutral-700">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-neutral-300 dark:text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V4a2 2 0 00-2-2H6a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>

      <!-- Rating badge -->
      <div v-if="card.rating" class="absolute top-2.5 right-2.5 bg-white dark:bg-neutral-800 px-2 py-0.5 flex items-center gap-1 rounded-md text-xs font-medium text-neutral-700 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-600">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-amber-500" viewBox="0 0 20 20" fill="currentColor">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        {{ card.rating }}
      </div>
    </div>

    <!-- Content -->
    <div class="p-4">
      <h3 class="font-medium text-sm text-neutral-900 dark:text-neutral-100 leading-tight">{{ card.name }}</h3>
      <p v-if="card.description" class="text-xs text-neutral-500 dark:text-neutral-400 mt-1.5 leading-relaxed line-clamp-2">
        {{ card.description }}
      </p>

      <!-- Tags -->
      <div v-if="card.tags && card.tags.length" class="mt-3 flex flex-wrap gap-1.5">
        <span
          v-for="tag in card.tags"
          :key="tag"
          class="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 text-[11px] rounded-full"
        >
          {{ tag }}
        </span>
      </div>

      <!-- Price -->
      <div v-if="card.price" class="mt-3 pt-2.5 border-t border-neutral-100 dark:border-neutral-700">
        <span class="text-sm font-medium text-neutral-900 dark:text-neutral-100">{{ card.price }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  card: {
    type: Object,
    required: true,
    default: () => ({
      name: 'Unknown Place',
      image: '',
      rating: null,
      description: '',
      tags: [],
      price: '',
    }),
  },
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
