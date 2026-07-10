<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiRequest, getStoredUser } from '../api'

const user = ref(getStoredUser())
const projects = ref([])
const deliverables = ref([])
const phases = ref([])
const loading = ref(true)
const showUpload = ref(false)
const uploadForm = ref({ phase_id: '', file_url: '' })

// Reviews for each deliverable
const reviewsByDeliverable = ref({})
const showReviewForm = ref({})
const reviewForm = ref({})

const myProject = computed(() => {
  return projects.value.find(p =>
    p.leader_id === user.value?.id ||
    p.members?.some(m => m.user_id === user.value?.id) ||
    p.mentors?.some(m => m.mentor_id === user.value?.id)
  ) || projects.value[0]
})

const isMentor = computed(() => user.value?.role === 'mentor' && myProject.value?.mentors?.some(m => m.mentor_id === user.value?.id))

const fetchData = async () => {
  loading.value = true
  try {
    projects.value = await apiRequest('/projects/?skip=0&limit=20') || []
    phases.value = await apiRequest('/phases/').catch(() => [])
    if (myProject.value) {
      deliverables.value = await apiRequest(`/projects/${myProject.value.id}/deliverables`).catch(() => [])
      if (!Array.isArray(deliverables.value)) deliverables.value = []
      // Fetch reviews for each deliverable
      for (const d of deliverables.value) {
        try {
          const revs = await apiRequest(`/deliverables/${d.id}/reviews`)
          reviewsByDeliverable.value[d.id] = Array.isArray(revs) ? revs : []
        } catch { reviewsByDeliverable.value[d.id] = [] }
      }
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleUpload = async () => {
  try {
    await apiRequest(`/projects/${myProject.value.id}/deliverables`, {
      method: 'POST',
      body: { phase_id: parseInt(uploadForm.value.phase_id), file_url: uploadForm.value.file_url },
    })
    showUpload.value = false
    uploadForm.value = { phase_id: '', file_url: '' }
    fetchData()
  } catch (e) { alert('Error: ' + e.message) }
}

const handleReview = async (deliverableId) => {
  try {
    await apiRequest(`/deliverables/${deliverableId}/reviews`, {
      method: 'POST',
      body: reviewForm.value[deliverableId] || { status: 'pendiente', feedback: '' },
    })
    showReviewForm.value[deliverableId] = false
    fetchData()
  } catch (e) { alert('Error: ' + e.message) }
}

const phaseName = (id) => phases.value.find(p => p.id === id)?.name || `Fase ${id}`

onMounted(fetchData)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="font-serif text-2xl font-bold text-parmenia-text">📦 Entregables y Revisiones</h1>
        <p class="text-sm text-parmenia-textMuted mt-1">Gestión de entregables por fase del proyecto</p>
      </div>
      <button v-if="myProject" @click="showUpload = !showUpload" class="btn-primary text-xs">
        {{ showUpload ? 'Cancelar' : '+ Subir entregable' }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">⏳</div>

    <div v-else-if="!myProject" class="card p-8 text-center">
      <p class="text-sm text-parmenia-textMuted">No tienes un proyecto activo</p>
    </div>

    <template v-else>
      <!-- Upload form -->
      <div v-if="showUpload" class="card p-5 space-y-3">
        <h3 class="font-serif font-bold text-parmenia-text">Subir nuevo entregable</h3>
        <div>
          <label class="block text-xs font-medium text-parmenia-textMuted mb-1">Fase</label>
          <select v-model="uploadForm.phase_id" class="input">
            <option value="">Seleccionar fase...</option>
            <option v-for="p in phases" :key="p.id" :value="p.id">{{ p.name }} (orden {{ p.order }})</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-parmenia-textMuted mb-1">URL del archivo</label>
          <input v-model="uploadForm.file_url" placeholder="https://drive.google.com/..." class="input" />
        </div>
        <button @click="handleUpload" class="btn-primary w-full">Subir</button>
      </div>

      <!-- Deliverables list -->
      <div v-if="deliverables.length === 0" class="card p-8 text-center">
        <span class="text-4xl block mb-2">📭</span>
        <p class="text-sm text-parmenia-textMuted">No hay entregables subidos</p>
      </div>

      <div v-else class="space-y-4">
        <div v-for="d in deliverables" :key="d.id" class="card p-5">
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="font-serif font-bold text-parmenia-text">{{ phaseName(d.phase_id) }}</h3>
              <a :href="d.file_url" target="_blank" class="text-xs text-parmenia-primary hover:underline break-all">{{ d.file_url }}</a>
              <p class="text-[10px] text-parmenia-textDim mt-1">Subido: {{ new Date(d.created_at).toLocaleDateString('es-PE') }}</p>
            </div>
          </div>

          <!-- Reviews -->
          <div class="border-t border-parmenia-border pt-3 mt-3">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-semibold text-parmenia-textMuted uppercase tracking-wider">Revisiones</h4>
              <button v-if="isMentor" @click="showReviewForm[d.id] = !showReviewForm[d.id]" class="text-xs text-parmenia-primary font-semibold">+ Revisar</button>
            </div>

            <!-- Review form (mentor only) -->
            <div v-if="showReviewForm[d.id] && isMentor" class="bg-parmenia-cream rounded-xl p-3 space-y-2 mb-2">
              <select v-model="(reviewForm[d.id] ||= {}).status" class="input">
                <option value="aprobado">Aprobado</option>
                <option value="rechazado">Rechazado</option>
                <option value="pendiente">Pendiente</option>
              </select>
              <textarea v-model="(reviewForm[d.id] ||= {}).feedback" placeholder="Feedback..." class="input" rows="2"></textarea>
              <button @click="handleReview(d.id)" class="btn-primary text-xs w-full">Enviar revisión</button>
            </div>

            <div v-if="!reviewsByDeliverable[d.id] || reviewsByDeliverable[d.id].length === 0" class="text-xs text-parmenia-textDim">Sin revisiones</div>
            <div v-else class="space-y-2">
              <div v-for="r in reviewsByDeliverable[d.id]" :key="r.id" class="flex items-start gap-2 p-2 bg-parmenia-cream rounded-lg">
                <span :class="{
                  'badge-success': r.status === 'aprobado',
                  'badge-danger': r.status === 'rechazado',
                  'badge-warning': r.status === 'pendiente',
                }" class="flex-shrink-0">{{ r.status }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-xs text-parmenia-text">{{ r.feedback || 'Sin comentarios' }}</p>
                  <p class="text-[10px] text-parmenia-textDim mt-0.5">{{ new Date(r.reviewed_at).toLocaleDateString('es-PE') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
