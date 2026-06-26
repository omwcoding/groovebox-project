<script setup>
import { ref, onMounted } from 'vue'

const backendStatus = ref('checking')
const backendMessage = ref('')

async function checkBackend() {
  backendStatus.value = 'checking'
  try {
    const res = await fetch('http://127.0.0.1:5000/api/health')
    if (res.ok) {
      const data = await res.json()
      backendMessage.value = data.message || 'Connected successfully'
      backendStatus.value = 'connected'
    } else {
      throw new Error('Server returned an error status')
    }
  } catch (error) {
    backendMessage.value = 'Could not connect to the Flask server'
    backendStatus.value = 'error'
  }
}

onMounted(() => {
  checkBackend()
})
</script>

<template>
  <main class="flex flex-col items-center justify-center min-h-screen px-4">
    <!-- Outer Glow Container -->
    <div
      class="relative w-full max-w-2xl p-8 rounded-2xl bg-slate-900/50 border border-slate-800 shadow-2xl backdrop-blur-xl"
    >
      <!-- Glow effect -->
      <div
        class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur-xl opacity-20 transition duration-1000 group-hover:opacity-100"
      ></div>

      <div class="relative flex flex-col items-center text-center">
        <!-- Logo/Icon -->
        <div
          class="w-16 h-16 flex items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 mb-6 border border-emerald-500/20"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="w-8 h-8"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>

        <h1
          class="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent mb-2"
        >
          Groovebox Project
        </h1>
        <p class="text-slate-400 text-sm mb-8 max-w-md">
          A modern stack initialized with Vue 3 (Vite + TS + Tailwind CSS) and Flask (Python REST
          API).
        </p>

        <!-- Status Card -->
        <div class="w-full bg-slate-950/60 rounded-xl p-6 border border-slate-850 text-left mb-6">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Backend Integration Status
          </h2>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="relative flex h-3 w-3">
                <span
                  :class="{
                    'bg-yellow-400': backendStatus === 'checking',
                    'bg-emerald-400 animate-ping': backendStatus === 'connected',
                    'bg-rose-400': backendStatus === 'error',
                  }"
                  class="absolute inline-flex h-full w-full rounded-full opacity-75"
                ></span>
                <span
                  :class="{
                    'bg-yellow-500': backendStatus === 'checking',
                    'bg-emerald-500': backendStatus === 'connected',
                    'bg-rose-500': backendStatus === 'error',
                  }"
                  class="relative inline-flex rounded-full h-3 w-3"
                ></span>
              </span>
              <span class="text-sm font-medium text-slate-200">
                <template v-if="backendStatus === 'checking'">Checking connection...</template>
                <template v-else-if="backendStatus === 'connected'">Connected</template>
                <template v-else>Disconnected</template>
              </span>
            </div>

            <button
              @click="checkBackend"
              class="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
            >
              Retry
            </button>
          </div>

          <p class="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-900 font-mono">
            {{ backendMessage || 'Initial connection state.' }}
          </p>
        </div>

        <!-- Stack Details -->
        <div class="grid grid-cols-2 gap-4 w-full text-left">
          <div class="p-4 rounded-xl bg-slate-950/40 border border-slate-900">
            <h3 class="text-sm font-semibold text-emerald-400 mb-1">Frontend</h3>
            <ul class="text-xs text-slate-400 space-y-1">
              <li>• Vue 3 (Composition API)</li>
              <li>• Vite, TypeScript</li>
              <li>• Tailwind CSS v4</li>
              <li>• Pinia & Router</li>
            </ul>
          </div>
          <div class="p-4 rounded-xl bg-slate-950/40 border border-slate-900">
            <h3 class="text-sm font-semibold text-teal-400 mb-1">Backend</h3>
            <ul class="text-xs text-slate-400 space-y-1">
              <li>• Python Flask 3.x</li>
              <li>• Flask-Cors (Enabled)</li>
              <li>• python-dotenv</li>
              <li>• .venv Isolated Env</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
