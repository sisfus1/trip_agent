<script setup>
import { ref, onMounted, watch } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatPanel from './components/ChatPanel.vue'
import ContentPanel from './components/ContentPanel.vue'
import AuthModal from './components/AuthModal.vue'

// --- Theme ---
const isDark = ref(localStorage.getItem('theme') === 'dark')
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}
const applyTheme = () => {
  document.documentElement.classList.toggle('dark', isDark.value)
}
onMounted(applyTheme)

// --- Auth ---
const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(localStorage.getItem('currentUser') || '')
const showAuthModal = ref(!token.value)

const onLoginSuccess = ({ accessToken, username }) => {
  token.value = accessToken
  currentUser.value = username
  localStorage.setItem('token', accessToken)
  localStorage.setItem('currentUser', username)
  showAuthModal.value = false
  loadSessions()
}
const logout = () => {
  token.value = ''
  currentUser.value = ''
  localStorage.removeItem('token')
  localStorage.removeItem('currentUser')
  showAuthModal.value = true
  sessions.value = []
  activeSessionId.value = null
}

// --- Sessions ---
const sessions = ref([])
const activeSessionId = ref(null)

const authHeaders = () => ({ Authorization: `Bearer ${token.value}` })

const loadSessions = async () => {
  if (!token.value) return
  try {
    const res = await fetch('/api/sessions', { headers: authHeaders() })
    if (res.ok) sessions.value = await res.json()
  } catch (e) {
    console.error('Failed to load sessions:', e)
  }
}

const createSession = async () => {
  if (!token.value) { showAuthModal.value = true; return }
  try {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话' }),
    })
    if (res.ok) {
      const session = await res.json()
      sessions.value.unshift(session)
      activeSessionId.value = session.id
    }
  } catch (e) {
    console.error('Failed to create session:', e)
  }
}

const selectSession = (id) => {
  activeSessionId.value = id
}

const deleteSession = async (id) => {
  try {
    await fetch(`/api/sessions/${id}`, { method: 'DELETE', headers: authHeaders() })
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (activeSessionId.value === id) {
      activeSessionId.value = sessions.value.length ? sessions.value[0].id : null
    }
  } catch (e) {
    console.error('Failed to delete session:', e)
  }
}

onMounted(loadSessions)

// --- WebSocket ---
const isConnected = ref(false)

// --- Dynamic Panel ---
const showCards = ref(false)
const activeCards = ref([])

const onCardsReceived = (cards) => {
  activeCards.value = cards
  showCards.value = true
}
const closePanel = () => {
  showCards.value = false
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-white dark:bg-[#1e1e1e] text-neutral-900 dark:text-neutral-100 transition-colors duration-200">
    <!-- Sidebar -->
    <Sidebar
      :current-user="currentUser"
      :is-dark="isDark"
      :token="token"
      :sessions="sessions"
      :active-session-id="activeSessionId"
      @toggle-theme="toggleTheme"
      @logout="logout"
      @show-auth="showAuthModal = true"
      @new-session="createSession"
      @select-session="selectSession"
      @delete-session="deleteSession"
    />

    <!-- Main workspace -->
    <div class="flex flex-1 min-w-0 relative">
      <ChatPanel
        class="min-w-0 transition-all duration-300 ease-in-out border-r border-neutral-200 dark:border-neutral-800"
        :class="showCards ? 'w-1/2' : 'w-full'"
        :token="token"
        :current-user="currentUser"
        :is-connected="isConnected"
        @update:is-connected="isConnected = $event"
        @show-auth="showAuthModal = true"
        @cards-received="onCardsReceived"
      />
      <transition name="panel-slide">
        <ContentPanel
          v-if="showCards"
          class="w-1/2 min-w-0"
          :cards="activeCards"
          @close="closePanel"
        />
      </transition>
    </div>

    <!-- Auth Modal -->
    <AuthModal
      v-if="showAuthModal && !token"
      @close="showAuthModal = false"
      @login-success="onLoginSuccess"
    />
  </div>
</template>

<style>
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: all 0.3s ease-in-out;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
</style>
