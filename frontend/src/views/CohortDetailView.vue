<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiRequest, getStoredUser } from '../api'

const route = useRoute()
const router = useRouter()
const user = ref(getStoredUser())
const cohort = ref(null)
const projects = ref([])
const loading = ref(true)

const fetchCohort = async () => {
  loading.value = true
  try {
    cohort.value = await apiRequest(`/cohorts/${route.params.id}`)
    projects.value = await apiRequest(`/projects/?cohort_id=${route.params.id}`).catch(() => [])
    if (!Array.isArray(projects.value)) projects.value = []
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(fetchCohort)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-6">
    <button @click="router.push('/convocatorias')" class="text-sm text-parmenia-primary font-semibold hover:underline">← Volver a convocatorias</button>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">⏳</div>

    <template v-else-if="cohort">
      <div class="card p-6">
        <h1 class="font-serif text-2xl font-bold text-parmenia-text mb-2">{{ cohort.name }}</h1>
        <p class="text-sm text-parmenia-textMuted mb-4">{{ cohort.description || 'Sin descripción' }}</p>
        <div class="flex gap-4 text-xs text-parmenia-textDim">
          <span v-if="cohort.start_date">📅 Inicio: {{ new Date(cohort.start_date).toLocaleDateString('es-PE') }}</span>
          <span v-if="cohort.end_date">⏰ Fin: {{ new Date(cohort.end_date).toLocaleDateString('es-PE') }}</span>
        </div>
      </div>

      <div>
        <h2 class="font-serif text-lg font-bold text-parmenia-text mb-3">🚀 Proyectos ({{ projects.length }})</h2>
        <div v-if="projects.length === 0" class="card p-8 text-center text-parmenia-textMuted text-sm">
          No hay proyectos registrados en esta convocatoria
        </div>
        <div v-else class="grid sm:grid-cols-2 gap-4">
          <div v-for="p in projects" :key="p.id" class="card p-4">
            <h3 class="font-serif font-bold text-parmenia-text mb-1">{{ p.name }}</h3>
            <p class="text-xs text-parmenia-textMuted line-clamp-2 mb-2">{{ p.description || 'Sin descripción' }}</p>
            <div class="flex items-center gap-2">
              <span v-if="p.current_phase" class="badge-primary">{{ p.current_phase.name }}</span>
              <span class="badge-neutral">Líder: {{ p.leader?.full_name || 'N/A' }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
