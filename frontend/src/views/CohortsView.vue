<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, getStoredUser } from '../api'

const router = useRouter()
const user = ref(getStoredUser())
const cohorts = ref([])
const loading = ref(true)
const showForm = ref(false)
const formData = ref({ name: '', description: '', start_date: '', end_date: '' })

const isAdmin = computed(() => user.value?.role === 'admin')

const today = new Date().toISOString().split('T')[0]
const activeCohorts = computed(() => cohorts.value.filter(c => !c.end_date || c.end_date >= today))
const pastCohorts = computed(() => cohorts.value.filter(c => c.end_date && c.end_date < today))

const fetchCohorts = async () => {
  loading.value = true
  try {
    cohorts.value = await apiRequest('/cohorts/') || []
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleCreate = async () => {
  try {
    await apiRequest('/cohorts/', { method: 'POST', body: formData.value })
    showForm.value = false
    formData.value = { name: '', description: '', start_date: '', end_date: '' }
    fetchCohorts()
  } catch (e) { alert('Error: ' + e.message) }
}

onMounted(fetchCohorts)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="font-serif text-2xl font-bold text-parmenia-text">📋 Convocatorias</h1>
        <p class="text-sm text-parmenia-textMuted mt-1">Procesos de pre-incubación e incubación de Parmenia</p>
      </div>
      <button v-if="isAdmin" @click="showForm = !showForm" class="btn-primary">
        {{ showForm ? 'Cancelar' : '+ Nueva convocatoria' }}
      </button>
    </div>

    <!-- Create form -->
    <div v-if="showForm && isAdmin" class="card p-5 space-y-3">
      <h2 class="font-serif text-lg font-bold">Crear convocatoria</h2>
      <input v-model="formData.name" placeholder="Nombre de la convocatoria" class="input" />
      <textarea v-model="formData.description" placeholder="Descripción" class="input" rows="3"></textarea>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-parmenia-textMuted mb-1">Fecha inicio</label>
          <input v-model="formData.start_date" type="date" class="input" />
        </div>
        <div>
          <label class="block text-xs font-medium text-parmenia-textMuted mb-1">Fecha fin</label>
          <input v-model="formData.end_date" type="date" class="input" />
        </div>
      </div>
      <button @click="handleCreate" class="btn-primary w-full">Crear</button>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">
      <span class="text-3xl">⏳</span><p class="mt-2 text-sm">Cargando convocatorias...</p>
    </div>

    <template v-else>
      <!-- Active -->
      <div v-if="activeCohorts.length > 0">
        <h2 class="font-serif text-lg font-bold text-parmenia-text mb-3">🟢 Convocatorias Activas</h2>
        <div class="grid sm:grid-cols-2 gap-4">
          <div v-for="c in activeCohorts" :key="c.id" class="card p-5 hover:border-parmenia-primary transition cursor-pointer" @click="router.push(`/convocatorias/${c.id}`)">
            <div class="flex items-start justify-between mb-2">
              <h3 class="font-serif font-bold text-parmenia-text">{{ c.name }}</h3>
              <span class="badge-success">Activa</span>
            </div>
            <p class="text-xs text-parmenia-textMuted mb-3 line-clamp-2">{{ c.description || 'Sin descripción' }}</p>
            <div class="flex items-center gap-3 text-xs text-parmenia-textDim">
              <span v-if="c.start_date">📅 {{ new Date(c.start_date).toLocaleDateString('es-PE') }}</span>
              <span v-if="c.end_date">⏰ {{ new Date(c.end_date).toLocaleDateString('es-PE') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Past -->
      <div v-if="pastCohorts.length > 0">
        <h2 class="font-serif text-lg font-bold text-parmenia-textMuted mb-3">📦 Convocatorias Anteriores</h2>
        <div class="space-y-2">
          <div v-for="c in pastCohorts" :key="c.id" class="card p-4 flex items-center justify-between hover:border-parmenia-border transition cursor-pointer" @click="router.push(`/convocatorias/${c.id}`)">
            <div>
              <h3 class="font-semibold text-sm text-parmenia-text">{{ c.name }}</h3>
              <p class="text-xs text-parmenia-textDim">{{ c.start_date ? new Date(c.start_date).toLocaleDateString('es-PE') : '' }} - {{ c.end_date ? new Date(c.end_date).toLocaleDateString('es-PE') : '' }}</p>
            </div>
            <span class="badge-neutral">Finalizada</span>
          </div>
        </div>
      </div>

      <div v-if="cohorts.length === 0" class="card p-8 text-center">
        <span class="text-4xl block mb-2">📭</span>
        <p class="text-sm text-parmenia-textMuted">No hay convocatorias registradas</p>
      </div>
    </template>
  </div>
</template>
