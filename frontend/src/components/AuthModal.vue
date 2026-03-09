<script setup>
import { ref, nextTick, onMounted } from 'vue'

const emit = defineEmits(['close', 'login-success'])

const isLoginMode = ref(true)
const authUsername = ref('')
const authPassword = ref('')
const authCaptcha = ref('')
const actualCaptchaStr = ref('')
const authError = ref('')
const authLoading = ref(false)
const captchaCanvas = ref(null)

const toggleAuthMode = () => {
  isLoginMode.value = !isLoginMode.value
  authPassword.value = ''
  authCaptcha.value = ''
  authError.value = ''
  generateAndDrawCaptcha()
}

const generateAndDrawCaptcha = () => {
  const chars = '0123456789'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  actualCaptchaStr.value = code

  nextTick(() => {
    if (!captchaCanvas.value) return
    const canvas = captchaCanvas.value
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    ctx.fillStyle = '#f3f4f6'
    ctx.fillRect(0, 0, width, height)

    // Check dark mode
    if (document.documentElement.classList.contains('dark')) {
      ctx.fillStyle = '#262626'
      ctx.fillRect(0, 0, width, height)
    }

    for (let i = 0; i < 5; i++) {
      ctx.strokeStyle = `rgba(${Math.random()*200},${Math.random()*200},${Math.random()*200}, 0.4)`
      ctx.beginPath()
      ctx.moveTo(Math.random() * width, Math.random() * height)
      ctx.lineTo(Math.random() * width, Math.random() * height)
      ctx.stroke()
    }

    for (let i = 0; i < 30; i++) {
      ctx.fillStyle = `rgba(120, 120, 120, ${Math.random() * 0.4})`
      ctx.beginPath()
      ctx.arc(Math.random() * width, Math.random() * height, 1, 0, 2 * Math.PI)
      ctx.fill()
    }

    ctx.font = 'bold 22px -apple-system, sans-serif'
    ctx.textBaseline = 'middle'
    for (let i = 0; i < code.length; i++) {
      const x = 15 + i * 20
      const y = height / 2
      ctx.save()
      ctx.translate(x, y)
      ctx.fillStyle = document.documentElement.classList.contains('dark')
        ? `hsl(${Math.random() * 360}, 50%, 65%)`
        : `hsl(${Math.random() * 360}, 50%, 40%)`
      ctx.fillText(code[i], -10, 2)
      ctx.restore()
    }
  })
}

const handleAuth = async () => {
  if (authCaptcha.value.trim() !== actualCaptchaStr.value) {
    authError.value = '验证码错误'
    generateAndDrawCaptcha()
    authCaptcha.value = ''
    return
  }

  authError.value = ''
  authLoading.value = true

  try {
    if (isLoginMode.value) {
      const formData = new URLSearchParams()
      formData.append('username', authUsername.value)
      formData.append('password', authPassword.value)
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      })
      if (!res.ok) throw new Error('账号或密码错误')
      const data = await res.json()
      emit('login-success', { accessToken: data.access_token, username: authUsername.value })
    } else {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername.value, password: authPassword.value }),
      })
      if (!res.ok) {
        if (res.status === 400) throw new Error('用户名已存在')
        throw new Error('注册失败')
      }
      // Auto login after register
      isLoginMode.value = true
      authCaptcha.value = actualCaptchaStr.value
      await handleAuth()
      return
    }
  } catch (err) {
    authError.value = err.message
    generateAndDrawCaptcha()
    authCaptcha.value = ''
  } finally {
    authLoading.value = false
  }
}

onMounted(generateAndDrawCaptcha)
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="emit('close')">
    <div class="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 p-8 rounded-2xl shadow-xl w-[22rem] transition-colors duration-200">
      <h2 class="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-6 text-center">
        {{ isLoginMode ? '欢迎回来' : '创建账户' }}
      </h2>

      <form @submit.prevent="handleAuth" class="space-y-4">
        <div>
          <label class="block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">用户名</label>
          <input
            v-model="authUsername"
            type="text"
            required
            class="w-full bg-neutral-100 dark:bg-neutral-800 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-600 rounded-lg px-4 py-2.5 text-sm text-neutral-900 dark:text-neutral-100 focus:outline-none transition-colors"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">密码</label>
          <input
            v-model="authPassword"
            type="password"
            required
            class="w-full bg-neutral-100 dark:bg-neutral-800 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-600 rounded-lg px-4 py-2.5 text-sm text-neutral-900 dark:text-neutral-100 focus:outline-none transition-colors"
          />
        </div>

        <!-- Captcha -->
        <div>
          <label class="block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">安全验证码</label>
          <div class="flex items-center gap-3">
            <input
              v-model="authCaptcha"
              type="text"
              maxlength="4"
              required
              placeholder="输入验证码"
              class="w-1/2 bg-neutral-100 dark:bg-neutral-800 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-600 rounded-lg px-4 py-2.5 text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none tracking-widest text-center transition-colors"
            />
            <div
              class="h-10 w-1/2 rounded-lg overflow-hidden cursor-pointer bg-neutral-100 dark:bg-neutral-800 flex relative group"
              @click="generateAndDrawCaptcha"
              title="点击刷新"
            >
              <canvas ref="captchaCanvas" width="100" height="40" class="w-full h-full"></canvas>
              <div class="absolute inset-0 bg-black/20 hidden group-hover:flex items-center justify-center">
                <span class="text-[10px] text-white font-medium tracking-wider">刷新</span>
              </div>
            </div>
          </div>
        </div>

        <p v-if="authError" class="text-red-500 text-xs text-center font-medium bg-red-50 dark:bg-red-900/20 py-1.5 rounded mt-2">{{ authError }}</p>

        <button
          type="submit"
          class="w-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-medium py-2.5 rounded-lg hover:opacity-90 transition-opacity flex justify-center items-center mt-6"
        >
          <span v-if="authLoading" class="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-2"></span>
          {{ isLoginMode ? '登录' : '注册' }}
        </button>
      </form>

      <p class="mt-5 text-center text-xs text-neutral-400 cursor-pointer hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors" @click="toggleAuthMode">
        {{ isLoginMode ? '还没有账户？去注册' : '已有账户？去登录' }}
      </p>
    </div>
  </div>
</template>
