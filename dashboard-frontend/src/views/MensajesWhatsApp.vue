<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-7 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div>
          <p class="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">Comunicación operativa</p>
          <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">Mensajes WhatsApp</h1>
          <p class="mt-1 text-sm text-slate-500">Audios y mensajes recibidos, con sus transcripciones locales.</p>
        </div>
        <button
          type="button"
          :disabled="loading"
          class="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          @click="fetchMessages"
        >
          <svg class="h-4 w-4" :class="{ 'animate-spin': loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M20 11a8.1 8.1 0 00-15.5-2M4 4v5h5M4 13a8.1 8.1 0 0015.5 2M20 20v-5h-5" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
          </svg>
          {{ loading ? 'Actualizando' : 'Actualizar' }}
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <div v-if="error" class="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {{ error }}
      </div>

      <div v-if="loading && messages.length === 0" class="grid gap-4">
        <div v-for="index in 4" :key="index" class="h-40 animate-pulse rounded-2xl border border-slate-200 bg-white" />
      </div>

      <div v-else-if="messages.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
        <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-2xl">💬</div>
        <h2 class="font-semibold text-slate-800">Todavía no hay mensajes</h2>
        <p class="mt-1 text-sm text-slate-500">Los mensajes sincronizados aparecerán aquí.</p>
      </div>

      <div v-else class="grid gap-4">
        <article
          v-for="message in messages"
          :key="message.id"
          class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
        >
          <div class="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="truncate font-semibold text-slate-900">{{ message.group_display_name }}</span>
                <span v-if="isAudio(message)" class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">Audio</span>
              </div>
              <p class="mt-1 truncate text-sm text-slate-500">{{ senderLabel(message) }}</p>
            </div>
            <time class="shrink-0 text-xs font-medium text-slate-400" :datetime="message.timestamp">
              {{ formatDate(message.timestamp) }}
            </time>
          </div>

          <div class="px-5 py-5">
            <template v-if="isAudio(message)">
              <div v-if="message.transcription_status === 'completed' && message.transcription" class="flex gap-3">
                <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-lg">🎙️</div>
                <div>
                  <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">Transcripción</p>
                  <p class="whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ message.transcription }}</p>
                </div>
              </div>
              <div v-else-if="['pending', 'processing'].includes(message.transcription_status)" class="flex items-center gap-3 text-sm text-amber-700">
                <span class="h-2.5 w-2.5 animate-pulse rounded-full bg-amber-400" />
                <span class="font-medium">Transcribiendo…</span>
              </div>
              <div v-else-if="message.transcription_status === 'failed'" class="flex items-center gap-3 text-sm text-red-700">
                <span class="flex h-8 w-8 items-center justify-center rounded-full bg-red-50">!</span>
                <span class="font-medium">No se pudo transcribir</span>
              </div>
              <p v-else class="text-sm italic text-slate-500">Audio recibido sin transcripción.</p>
            </template>
            <p v-else class="whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ message.body || 'Mensaje sin texto.' }}</p>
          </div>
        </article>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../services/api'

const messages = ref([])
const loading = ref(false)
const error = ref('')

const fetchMessages = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('/api/forestal-bot/whatsapp/owner/messages/', {
      params: { limit: 200 }
    })
    messages.value = response.data || []
  } catch (_error) {
    error.value = 'No pudimos cargar los mensajes. Intentá nuevamente.'
  } finally {
    loading.value = false
  }
}

const isAudio = (message) =>
  String(message.message_type || '').startsWith('audio') ||
  String(message.media_type || '').startsWith('audio')

const senderLabel = (message) => message.sender_name || message.sender_id || 'Remitente sin identificar'

const formatDate = (value) => {
  if (!value) return 'Fecha no disponible'
  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

onMounted(fetchMessages)
</script>
