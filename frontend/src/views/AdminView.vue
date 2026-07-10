<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiRequest, getStoredUser } from '../api'

const user = ref(getStoredUser())
const loading = ref(true)
const tab = ref('cohorts')
const cohorts = ref([])
const phases = ref([])
const enrollments = ref([])
const profiles = ref([])
const reports = ref(null)

const isAdmin = computed(() => user.value?.role === 'admin')

const tabs = [
  { key: 'cohorts', label: 'Convocatorias', icon: '📋' },
  { key: 'phases', label: 'Fases', icon: '📊' },
  { key: 'enrollments', label: 'Inscripciones', icon: '✍️' },
  { key: 'users', label: 'Usuarios', icon: '👥' },
  { key: 'reports', label: 'Reportes', icon: '📈' },
]

const fetchData = async () => {
  loading.value = true
  try {
    const [c, p, e, pr, r] = await Promise.all([
      apiRequest('/cohorts/').catch(() => []),
      apiRequest('/phases/').catch(() => []),
      apiRequest('/enrollments/').catch(() => []),
      apiRequest('/profiles/').catch(() => []),
      apiRequest('/reports/dashboard').catch(() => null),
    ])
    cohorts.value = Array.isArray(c) ? c : []
    phases.value = Array.isArray(p) ? p : []
    enrollments.value = Array.isArray(e) ? e : []
    profiles.value = Array.isArray(pr) ? pr : []
    reports.value = r
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const updateEnrollmentStatus = async (id, status) => {
  try {
    await apiRequest(`/enrollments/${id}/status`, { method: 'PUT', body: { status } })
    fetchData()
  } catch (e) { alert('Error: ' + e.message) }
}

onMounted(fetchData)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto space-y-6">
    <div>
      <h1 class="font-serif text-2xl font-bold text-parmenia-text">⚙️ Panel de Administración</h1>
      <p class="text-sm text-parmenia-textMuted mt-1">Gestión completa de la incubadora Parmenia</p>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 p-1 bg-parmenia-cream rounded-xl overflow-x-auto">
      <button v-for="t in tabs" :key="t.key" @click="tab = t.key"
        class="flex-1 min-w-max px-4 py-2 rounded-lg text-sm font-semibold transition whitespace-nowrap"
        :class="tab === t.key ? 'bg-parmenia-card text-parmenia-primary shadow-sm' : 'text-parmenia-textMuted'">
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">⏳</div>

    <template v-else>
      <!-- Cohorts -->
      <div v-if="tab === 'cohorts'" class="space-y-3">
        <div v-for="c in cohorts" :key="c.id" class="card p-4 flex items-center justify-between">
          <div>
            <p class="font-semibold text-sm text-parmenia-text">{{ c.name }}</p>
            <p class="text-xs text-parmenia-textDim">{{ c.start_date }} → {{ c.end_date || 'Sin fin' }}</p>
          </div>
          <span class="badge-neutral text-xs">{{ c.description?.slice(0, 30) || 'Sin desc' }}</span>
        </div>
        <div v-if="cohorts.length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin convocatorias</div>
      </div>

      <!-- Phases -->
      <div v-if="tab === 'phases'" class="space-y-3">
        <div v-for="p in phases" :key="p.id" class="card p-4 flex items-center justify-between">
          <div>
            <p class="font-semibold text-sm text-parmenia-text">{{ p.name }}</p>
            <p class="text-xs text-parmenia-textDim">Orden: {{ p.order }}</p>
          </div>
          <span class="badge-primary text-xs">Fase {{ p.order }}</span>
        </div>
        <div v-if="phases.length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin fases</div>
      </div>

      <!-- Enrollments -->
      <div v-if="tab === 'enrollments'" class="space-y-3">
        <div v-for="e in enrollments" :key="e.id" class="card p-4 flex items-center justify-between gap-3">
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm text-parmenia-text truncate">{{ e.user?.email || e.user_id }}</p>
            <p class="text-xs text-parmenia-textDim">{{ e.cohort?.name || `Cohort ${e.cohort_id}` }} · {{ new Date(e.enrollment_date).toLocaleDateString('es-PE') }}</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span :class="{ 'badge-success': e.status === 'aceptada', 'badge-danger': e.status === 'rechazada', 'badge-warning': e.status === 'pendiente' }">{{ e.status }}</span>
            <button v-if="e.status === 'pendiente'" @click="updateEnrollmentStatus(e.id, 'aceptada')" class="text-xs text-parmenia-success font-semibold hover:underline">✓</button>
            <button v-if="e.status === 'pendiente'" @click="updateEnrollmentStatus(e.id, 'rechazada')" class="text-xs text-parmenia-danger font-semibold hover:underline">✗</button>
          </div>
        </div>
        <div v-if="enrollments.length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin inscripciones</div>
      </div>

      <!-- Users -->
      <div v-if="tab === 'users'" class="space-y-3">
        <div v-for="p in profiles" :key="p.id" class="card p-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-parmenia-primarySoft flex items-center justify-center text-xs font-bold text-parmenia-primary">
              {{ (p.full_name || p.email || '?').charAt(0).toUpperCase() }}
            </div>
            <div>
              <p class="font-semibold text-sm text-parmenia-text">{{ p.full_name || 'Sin nombre' }}</p>
              <p class="text-xs text-parmenia-textDim">{{ p.email }}</p>
            </div>
          </div>
          <span :class="{ 'badge-primary': p.role === 'admin', 'badge-success': p.role === 'mentor', 'badge-neutral': p.role === 'emprendedor' }">{{ p.role }}</span>
        </div>
        <div v-if="profiles.length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin usuarios</div>
      </div>

      <!-- Reports -->
      <div v-if="tab === 'reports'" class="space-y-4">
        <div v-if="reports" class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.users_by_role?.total || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Total usuarios</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.users_by_role?.emprendedor || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Emprendedores</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.users_by_role?.mentor || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Mentores</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.projects_by_phase?.total || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Proyectos</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.deliverables_reviewed || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Entregables revisados</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-2xl font-bold text-parmenia-primary">{{ reports.active_cohorts || 0 }}</p>
            <p class="text-xs text-parmenia-textMuted">Convocatorias activas</p>
          </div>
        </div>
        <div v-else class="card p-6 text-center text-parmenia-textMuted text-sm">No hay datos de reportes</div>
      </div>
    </template>
  </div>
</template>
