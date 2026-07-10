<script setup>
import { ref, reactive, onMounted } from 'vue'
import { apiRequest, getStoredUser, authApi } from '../api'

const user = ref(getStoredUser())
const loading = ref(false)
const msg = ref(null)
const form = reactive({ full_name: '', email: '', faculty: '', skills: '' })

const fetchProfile = async () => {
  try {
    const me = await apiRequest('/auth/me')
    user.value = me
    form.full_name = me.full_name || ''
    form.email = me.email || ''
    form.faculty = me.faculty || ''
    form.skills = Array.isArray(me.skills) ? me.skills.join(', ') : ''
  } catch (e) { console.error(e) }
}

const handleSave = async () => {
  loading.value = true
  msg.value = null
  try {
    const payload = {
      full_name: form.full_name,
      faculty: form.faculty,
      skills: form.skills ? form.skills.split(',').map(s => s.trim()) : [],
    }
    await apiRequest(`/profiles/${user.value.id}`, { method: 'PUT', body: payload })
    msg.value = { type: 'success', text: 'Perfil actualizado correctamente' }
    await fetchProfile()
  } catch (e) {
    msg.value = { type: 'error', text: e.message || 'Error al guardar' }
  } finally { loading.value = false }
}

onMounted(fetchProfile)
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto space-y-6">
    <div>
      <h1 class="font-serif text-2xl font-bold text-parmenia-text">👤 Mi Perfil</h1>
      <p class="text-sm text-parmenia-textMuted mt-1">Gestiona tu información personal</p>
    </div>

    <!-- Profile card -->
    <div class="card p-6 flex items-center gap-4">
      <div class="w-16 h-16 rounded-full bg-gradient-to-br from-parmenia-primary to-parmenia-accent flex items-center justify-center text-white font-serif font-bold text-2xl">
        {{ (user?.full_name || user?.email || '?').charAt(0).toUpperCase() }}
      </div>
      <div>
        <h2 class="font-serif text-lg font-bold text-parmenia-text">{{ user?.full_name || 'Sin nombre' }}</h2>
        <p class="text-sm text-parmenia-textMuted">{{ user?.email }}</p>
        <span class="badge-primary mt-1">{{ user?.role }}</span>
      </div>
    </div>

    <!-- Edit form -->
    <div class="card p-6 space-y-4">
      <h3 class="font-serif font-bold text-parmenia-text">Editar información</h3>

      <div v-if="msg" :class="msg.type === 'success' ? 'bg-parmenia-successSoft text-parmenia-success' : 'bg-parmenia-dangerSoft text-parmenia-danger'" class="rounded-lg px-3 py-2 text-sm">
        {{ msg.text }}
      </div>

      <div>
        <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Nombre completo</label>
        <input v-model="form.full_name" class="input" />
      </div>
      <div>
        <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Correo</label>
        <input v-model="form.email" type="email" disabled class="input opacity-60" />
      </div>
      <div>
        <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Facultad</label>
        <input v-model="form.faculty" class="input" />
      </div>
      <div>
        <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Habilidades (separadas por comas)</label>
        <input v-model="form.skills" class="input" />
      </div>

      <button @click="handleSave" :disabled="loading" class="btn-primary w-full">
        {{ loading ? '⏳ Guardando...' : 'Guardar cambios' }}
      </button>
    </div>
  </div>
</template>
