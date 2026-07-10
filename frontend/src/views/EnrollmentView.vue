<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, getStoredUser } from '../api'

const router = useRouter()
const user = ref(getStoredUser())
const cohorts = ref([])
const enrollments = ref([])
const loading = ref(true)
const enrolling = ref(false)

const activeCohorts = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return cohorts.value.filter(c => !c.end_date || c.end_date >= today)
})

const myEnrollments = computed(() => enrollments.value.filter(e => e.user_id === user.value?.id))

const fetchData = async () => {
  loading.value = true
  try {
    const [c, e] = await Promise.all([
      apiRequest('/cohorts/'),
      apiRequest('/enrollments/'),
    ])
    cohorts.value = c || []
    enrollments.value = Array.isArray(e) ? e : []
  } catch (err) { console.error(err) } finally { loading.value = false }
}

const handleEnroll = async (cohortId) => {
  enrolling.value = true
  try {
    await apiRequest('/enrollments/', { method: 'POST', body: { cohort_id: cohortId } })
    await fetchData()
  } catch (e) { alert('Error: ' + e.message) } finally { enrolling.value = false }
}

const isEnrolled = (cohortId) => myEnrollments.value.some(e => e.cohort_id === cohortId)

onMounted(fetchData)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-6">
    <div>
      <h1 class="font-serif text-2xl font-bold text-parmenia-text">✍️ Inscripción a Convocatorias</h1>
      <p class="text-sm text-parmenia-textMuted mt-1">Inscríbete en un proceso de pre-incubación o incubación</p>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">⏳</div>

    <template v-else>
      <!-- My enrollments -->
      <div v-if="myEnrollments.length > 0" class="card p-5">
        <h2 class="font-serif text-lg font-bold text-parmenia-text mb-3">📋 Mis Inscripciones</h2>
        <div class="space-y-2">
          <div v-for="enr in myEnrollments" :key="enr.id" class="flex items-center justify-between p-3 bg-parmenia-cream rounded-xl">
            <div>
              <p class="text-sm font-medium text-parmenia-text">{{ enr.cohort?.name || `Convocatoria ${enr.cohort_id}` }}</p>
              <p class="text-xs text-parmenia-textDim">{{ new Date(enr.enrollment_date).toLocaleDateString('es-PE') }}</p>
            </div>
            <span :class="{
              'badge-success': enr.status === 'aceptada',
              'badge-danger': enr.status === 'rechazada',
              'badge-warning': enr.status === 'pendiente',
            }">{{ enr.status }}</span>
          </div>
        </div>
      </div>

      <!-- Available cohorts -->
      <div>
        <h2 class="font-serif text-lg font-bold text-parmenia-text mb-3">🟢 Convocatorias Disponibles</h2>
        <div v-if="activeCohorts.length === 0" class="card p-8 text-center text-parmenia-textMuted text-sm">
          No hay convocatorias abiertas en este momento
        </div>
        <div v-else class="space-y-3">
          <div v-for="c in activeCohorts" :key="c.id" class="card p-5 flex items-start justify-between gap-4">
            <div class="flex-1">
              <h3 class="font-serif font-bold text-parmenia-text mb-1">{{ c.name }}</h3>
              <p class="text-xs text-parmenia-textMuted mb-2">{{ c.description || 'Sin descripción' }}</p>
              <div class="flex gap-3 text-xs text-parmenia-textDim">
                <span v-if="c.start_date">📅 {{ new Date(c.start_date).toLocaleDateString('es-PE') }}</span>
                <span v-if="c.end_date">⏰ {{ new Date(c.end_date).toLocaleDateString('es-PE') }}</span>
              </div>
            </div>
            <div class="flex-shrink-0">
              <button v-if="isEnrolled(c.id)" disabled class="btn-secondary text-xs opacity-60">✓ Inscrito</button>
              <button v-else @click="handleEnroll(c.id)" :disabled="enrolling" class="btn-primary text-xs">Inscribirse</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
