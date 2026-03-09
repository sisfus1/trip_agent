<script setup>
defineProps({
  currentUser: String,
  isDark: Boolean,
  token: String,
  sessions: { type: Array, default: () => [] },
  activeSessionId: { type: String, default: null },
})
const emit = defineEmits([
  'toggle-theme', 'logout', 'show-auth',
  'new-session', 'select-session', 'delete-session',
])
</script>

<template>
  <aside class="flex flex-col w-64 shrink-0 h-full border-r border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#171717] transition-colors duration-200">
    <!-- New conversation button -->
    <div class="p-4">
      <button
        id="btn-new-chat"
        @click="emit('new-session')"
        class="flex items-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        <span>发起新对话</span>
      </button>
    </div>

    <!-- History list -->
    <div class="flex-1 overflow-y-auto px-3">
      <p class="text-xs text-neutral-400 dark:text-neutral-500 mt-1 mb-2 px-1 font-medium tracking-wide">我的内容</p>

      <div v-if="!sessions.length" class="px-1 text-xs text-neutral-400 dark:text-neutral-500 mt-4">
        暂无对话记录
      </div>

      <div
        v-for="s in sessions"
        :key="s.id"
        @click="emit('select-session', s.id)"
        class="group flex items-center justify-between px-3 py-2 rounded-lg mb-0.5 cursor-pointer text-sm transition-colors"
        :class="s.id === activeSessionId
          ? 'bg-neutral-200 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100'
          : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'"
      >
        <span class="truncate flex-1">{{ s.title }}</span>
        <button
          @click.stop="emit('delete-session', s.id)"
          class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-neutral-300 dark:hover:bg-neutral-700 transition-all shrink-0 ml-2"
          title="删除"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Bottom: user info & theme toggle -->
    <div class="p-4 border-t border-neutral-200 dark:border-neutral-800 space-y-3">
      <button
        id="btn-theme-toggle"
        @click="emit('toggle-theme')"
        class="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
      >
        <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <span>{{ isDark ? '浅色模式' : '深色模式' }}</span>
      </button>

      <div v-if="token" class="flex items-center justify-between">
        <span class="text-sm truncate text-neutral-600 dark:text-neutral-400">{{ currentUser }}</span>
        <button
          @click="emit('logout')"
          class="text-xs text-neutral-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
        >退出</button>
      </div>
      <button
        v-else
        @click="emit('show-auth')"
        class="w-full text-sm font-medium py-2 rounded-lg bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:opacity-90 transition-opacity"
      >登录</button>
    </div>
  </aside>
</template>
