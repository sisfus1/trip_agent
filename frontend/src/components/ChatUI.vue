<template>
  <div class="flex flex-col h-screen w-full bg-slate-950 text-white font-sans overflow-hidden">
    <!-- Header: 具有毛玻璃质感的顶级标题 -->
    <header class="flex items-center justify-between p-5 bg-slate-900/60 backdrop-blur-lg border-b border-slate-800 z-10 box-border">
      <div class="flex items-center space-x-3">
        <h1 class="text-2xl font-extrabold bg-gradient-to-r from-sky-400 via-indigo-400 to-purple-500 bg-clip-text text-transparent tracking-tight">
          Vibe Travel Pilot
        </h1>
      </div>
      
      <div class="flex items-center space-x-6">
        <!-- API Key Input -->
        <input 
          v-model="apiKey" 
          type="password" 
          placeholder="DeepSeek API Key..." 
          class="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-36 shadow-inner"
        />

        <!-- WebSocket 状态指示灯 -->
        <div class="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-700 shadow-inner">
          <span class="relative flex h-3 w-3">
            <span v-if="isConnected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3" :class="isConnected ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'"></span>
          </span>
          <span class="text-xs font-medium text-slate-300">{{ isConnected ? 'Online' : 'Offline' }}</span>
        </div>

        <!-- 动态双模切换开关 (Text / Voice) -->
        <div class="flex bg-slate-900 rounded-full p-1 border border-slate-700 shadow-xl relative">
          <div class="absolute inset-y-1 w-1/2 bg-gradient-to-r transition-all duration-300 ease-in-out rounded-full shadow-md z-0"
               :class="mode === 'text' ? 'translate-x-0 from-sky-600 to-indigo-600' : 'translate-x-full from-indigo-600 to-purple-600'">
          </div>
          <button 
            @click="switchMode('text')" 
            class="relative z-10 px-5 py-1.5 rounded-full text-sm font-semibold transition-colors duration-200"
            :class="mode === 'text' ? 'text-white' : 'text-slate-400 hover:text-slate-200'"
          >
            Text
          </button>
          <button 
            @click="switchMode('voice')" 
            class="relative z-10 px-5 py-1.5 rounded-full text-sm font-semibold transition-colors duration-200"
            :class="mode === 'voice' ? 'text-white' : 'text-slate-400 hover:text-slate-200'"
          >
            Voice
          </button>
        </div>
      </div>
    </header>

    <!-- Chat Area -->
    <main class="flex-1 overflow-y-auto p-6 space-y-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black box-border" ref="chatContainer">
      <div class="flex flex-col space-y-6 max-w-4xl mx-auto w-full">
        <div v-for="(msg, idx) in messages" :key="idx" 
             class="flex w-full" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <div 
            class="max-w-[75%] rounded-2xl px-5 py-3.5 shadow-lg relative break-words"
            :class="msg.role === 'user' 
              ? 'bg-gradient-to-br from-indigo-600 to-sky-600 text-white rounded-tr-sm' 
              : 'bg-slate-800 text-slate-100 border border-slate-700/50 rounded-tl-sm'"
          >
            <p class="leading-relaxed">{{ msg.content }}</p>
          </div>
        </div>
      </div>
    </main>

    <!-- Input Area (Text Mode) -->
    <transition name="fade-slide" mode="out-in">
      <footer v-if="mode === 'text'" class="p-6 bg-slate-900/80 backdrop-blur-xl border-t border-slate-800 z-10 box-border">
        <form @submit.prevent="sendMessage" class="flex items-center space-x-3 max-w-4xl mx-auto w-full">
          <div class="relative flex-1">
            <input 
              v-model="inputText" 
              type="text" 
              placeholder="Tell me about your dream destination..." 
              class="w-full bg-slate-950 border border-slate-700 rounded-full pl-6 pr-12 py-3.5 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/50 transition-all font-medium shadow-inner"
            />
          </div>
          <button 
            type="submit" 
            :disabled="!isConnected || !inputText.trim()"
            class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 text-white rounded-full p-3.5 transition-all duration-200 shadow-[0_0_15px_rgba(79,70,229,0.4)] flex-shrink-0 active:scale-95"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 rotate-90" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </form>
      </footer>

      <!-- Voice Area (Voice Mode) -->
      <footer v-else class="p-10 flex flex-col justify-center items-center bg-slate-900/80 backdrop-blur-xl border-t border-slate-800 z-10 box-border">
        <div class="relative">
          <!-- 录音时的波动发光背景 -->
          <div v-if="isRecording" class="absolute inset-0 bg-purple-500 rounded-full blur-xl animate-pulse opacity-50"></div>
          <button 
            @click="toggleVoiceRecording"
            class="relative z-10 h-24 w-24 rounded-full flex items-center justify-center transition-all duration-300 ease-[cubic-bezier(0.175,0.885,0.32,1.275)]"
            :class="isRecording ? 'bg-red-500 shadow-[0_0_40px_rgba(239,68,68,0.6)] scale-110' : 'bg-purple-600 shadow-[0_0_20px_rgba(147,51,234,0.4)] hover:scale-105 hover:bg-purple-500'"
          >
            <svg v-if="!isRecording" xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <div v-else class="flex space-x-1">
              <div class="w-1.5 h-6 bg-white rounded-full animate-bounce" style="animation-delay: -0.3s"></div>
              <div class="w-1.5 h-8 bg-white rounded-full animate-bounce" style="animation-delay: -0.15s"></div>
              <div class="w-1.5 h-6 bg-white rounded-full animate-bounce"></div>
            </div>
          </button>
        </div>
        <p class="mt-6 text-sm font-medium" :class="isRecording ? 'text-red-400 animate-pulse' : 'text-purple-400'">
          {{ isRecording ? 'Listening (Voice Mode)...' : 'Tap to speak' }}
        </p>
      </footer>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const mode = ref('text') // 'text' | 'voice'
const isConnected = ref(false)
const messages = ref([
  { role: 'assistant', content: 'Hello! I am your Vibe Travel Pilot. Please provide your DeepSeek API Key in the top right, then tell me where you would like to travel.' }
])
const inputText = ref('')
const apiKey = ref('')
const isRecording = ref(false)
const chatContainer = ref(null)

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
  // 动态获取主机名与协议以兼容本地开发(5173/8000)与生产环境(HF Spaces reverse proxy)
  const host = window.location.hostname
  const port = window.location.port
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  
  // 如果是本地 Vite 开发服务器 (5173)，则强制指向本地 FastAPI (8000)
  // 如果是生产环境 (端口非 5173，或者是 HF Spaces 这种去除了端口的 HTTPS)，则直接复用当前 host
  const wsHost = port === '5173' ? `${host}:8000` : window.location.host
  
  const wsUrl = mode.value === 'text' 
    ? `${protocol}//${wsHost}/ws/chat` 
    : `${protocol}//${wsHost}/ws/gemini-live`
    
  if (ws) {
    ws.onclose = null // 防止主动关闭触发重连
    ws.close()
  }
  
  if (keepAliveInterval) clearInterval(keepAliveInterval)
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
  
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    isConnected.value = true
    reconnectAttempts = 0
    // WebSocket Keep-Alive 机制：每 25 秒给后端发一次 ping
    keepAliveInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN && mode.value === 'text') {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
  }

  ws.onmessage = (event) => {
    if (mode.value === 'text' || mode.value === 'voice') {
      try {
        const data = event.data
        if (data === '{"type":"pong"}') return // 忽略心跳包回应
        
        // 渲染消息到界面
        messages.value.push({ role: 'assistant', content: data })
        scrollToBottom()
        
        // 全双工语音合成: 当处于 Voice 模式且收到最终规划时，唤起 TTS 大声朗读
        if (mode.value === 'voice' && data.includes('[Final Travel Plan Generated]')) {
           const cleanTextForSpeech = data.replace(/🎉 \[Final Travel Plan Generated\]/g, '').trim()
           const utterance = new SpeechSynthesisUtterance(cleanTextForSpeech);
           utterance.lang = 'en-US';
           utterance.rate = 1.0;
           utterance.pitch = 1.0;
           // 确保兼容性
           if (window.speechSynthesis) {
               window.speechSynthesis.speak(utterance);
           }
        }
        
      } catch(e) {
        console.error("Message parsing error:", e)
      }
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    if (keepAliveInterval) clearInterval(keepAliveInterval)
    
    // 自动重连机制（指数退避）
    const timeout = Math.min(10000, 1000 * Math.pow(2, reconnectAttempts))
    reconnectAttempts++
    console.log(`WebSocket closed. Reconnecting in ${timeout}ms...`)
    reconnectTimeout = setTimeout(connectWebSocket, timeout)
  }
  
  ws.onerror = (err) => {
    console.error("WebSocket encountered error: ", err)
  }
}

const switchMode = (newMode) => {
  if (mode.value === newMode) return
  mode.value = newMode
  isConnected.value = false
  reconnectAttempts = 0 // 切模式重置重连次数
  connectWebSocket()
}

const sendMessage = () => {
  if (!inputText.value.trim() || !ws || ws.readyState !== WebSocket.OPEN) return
  if (!apiKey.value.trim()) {
    messages.value.push({ role: 'assistant', content: '⚠️ Please enter your Gemini API Key in the top right corner before sending a message.' })
    scrollToBottom()
    return
  }
  
  messages.value.push({ role: 'user', content: inputText.value })
  scrollToBottom()
  
  // 发送时将 api_key 与查询文本打死为 json 或者自定义格式，这里我们用 JSON
  const payload = {
    type: "query",
    query: inputText.value,
    api_key: apiKey.value
  }
  ws.send(JSON.stringify(payload))
  inputText.value = ''
}

const toggleVoiceRecording = () => {
  if (isRecording.value) {
    // 强制提早结束录音
    if (window.recognitionInstance) {
      window.recognitionInstance.stop()
    }
    isRecording.value = false
    return
  }

  // 检查浏览器兼容性
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Sorry, your browser doesn't support the Web Speech API. Please try Google Chrome or Safari on HTTPS.");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US'; // 默认使用英文，以适配大语言模型的初始设定
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording.value = true;
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    inputText.value = transcript;
    
    // 如果获得了完整的识别结果，直接当做用户发送消息
    if (inputText.value.trim()) {
       messages.value.push({ role: 'assistant', content: `🎤 (Voice): "${transcript}"` })
       sendMessage();
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
    isRecording.value = false;
    if (event.error === 'not-allowed') {
       alert("Microphone access was denied. Please allow microphone permissions in your browser.");
    }
  };

  recognition.onend = () => {
    isRecording.value = false;
  };

  // 保存实例以供停止
  window.recognitionInstance = recognition;
  try {
    recognition.start();
  } catch(e) {
    console.error("Recognition start failed: ", e);
    isRecording.value = false;
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
  clearTimeout(keepAliveInterval)
})
</script>

<style scoped>
/* 组件级切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 隐藏自带的滚动条，使用自定义毛病风格如果需要可以替换 */
main::-webkit-scrollbar {
  width: 6px;
}
main::-webkit-scrollbar-track {
  background: transparent;
}
main::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 10px;
}
</style>
