<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'

const props = defineProps({
  token: String,
  currentUser: String,
  isConnected: Boolean,
})
const emit = defineEmits(['update:is-connected', 'show-auth', 'cards-received'])

const messages = ref([
  { role: 'assistant', content: '你好！我是你的 Trip Agent 旅行规划助手。登录后即可开始规划你的梦想旅程。' }
])
const inputText = ref('')
const chatContainer = ref(null)
const isPersistent = ref(true)

let ws = null
let keepAliveInterval = null
let reconnectTimeout = null
let reconnectAttempts = 0

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const connectWebSocket = () => {
  if (!props.token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsHost = window.location.host
  const wsUrl = `${protocol}//${wsHost}/ws/chat`

  if (ws) {
    ws.onclose = null
    ws.close()
  }

  if (keepAliveInterval) clearInterval(keepAliveInterval)
  if (reconnectTimeout) clearTimeout(reconnectTimeout)

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    emit('update:is-connected', true)
    reconnectAttempts = 0
    keepAliveInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
  }

  ws.onmessage = (event) => {
    try {
      const raw = event.data
      if (raw === '{"type":"pong"}') return

      let parsed
      try {
        parsed = JSON.parse(raw)
      } catch {
        messages.value.push({ role: 'assistant', content: raw })
        scrollToBottom()
        return
      }

      if (parsed.message) {
        messages.value.push({ role: 'assistant', content: parsed.message })
        scrollToBottom()
      }

      if (parsed.cards && Array.isArray(parsed.cards) && parsed.cards.length > 0) {
        emit('cards-received', parsed.cards)
      }
    } catch (e) {
      console.error("Message handling error:", e)
    }
  }

  ws.onclose = () => {
    emit('update:is-connected', false)
    if (keepAliveInterval) clearInterval(keepAliveInterval)
    const timeout = Math.min(10000, 1000 * Math.pow(2, reconnectAttempts))
    reconnectAttempts++
    reconnectTimeout = setTimeout(connectWebSocket, timeout)
  }

  ws.onerror = (err) => {
    console.error("WebSocket error:", err)
  }
}

const sendMessage = () => {
  if (!inputText.value.trim() || !ws || ws.readyState !== WebSocket.OPEN) return
  if (!props.token) {
    emit('show-auth')
    return
  }

  messages.value.push({ role: 'user', content: inputText.value })
  scrollToBottom()

  ws.send(JSON.stringify({
    type: "query",
    query: inputText.value,
    token: props.token,
    is_persistent: isPersistent.value,
  }))
  inputText.value = ''
}

// Connect on mount if token exists
onMounted(connectWebSocket)

// Reconnect when token changes (e.g. after login)
watch(() => props.token, (newToken) => {
  if (newToken) {
    reconnectAttempts = 0
    connectWebSocket()
  } else {
    if (ws) { ws.onclose = null; ws.close() }
    emit('update:is-connected', false)
  }
})

onUnmounted(() => {
  if (ws) { ws.onclose = null; ws.close() }
  if (keepAliveInterval) clearInterval(keepAliveInterval)
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header bar -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
      <h2 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Trip Agent</h2>
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span v-if="isConnected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2" :class="isConnected ? 'bg-emerald-500' : 'bg-neutral-400'"></span>
        </span>
        <span class="text-xs text-neutral-400">{{ isConnected ? '已连接' : '离线' }}</span>
      </div>
    </div>

    <!-- Messages -->
    <main ref="chatContainer" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
      <div class="max-w-2xl mx-auto w-full space-y-4">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="flex w-full"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed break-words"
            :class="msg.role === 'user'
              ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-br-sm'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-bl-sm'"
          >
            {{ msg.content }}
          </div>
        </div>
      </div>
    </main>

    <!-- Input -->
    <div class="px-5 py-4 border-t border-neutral-200 dark:border-neutral-800 shrink-0">
      <form @submit.prevent="sendMessage" class="flex items-center gap-3 max-w-2xl mx-auto w-full">
        <input
          id="chat-input"
          v-model="inputText"
          type="text"
          placeholder="描述你的理想旅行目的地..."
          class="flex-1 bg-neutral-100 dark:bg-neutral-800 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-600 rounded-xl px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none transition-colors"
        />
        <button
          id="btn-send"
          type="submit"
          :disabled="!isConnected || !inputText.trim()"
          class="shrink-0 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl p-3 disabled:opacity-30 hover:opacity-80 active:scale-95 transition-all"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </form>
    </div>
  </div>
</template>
