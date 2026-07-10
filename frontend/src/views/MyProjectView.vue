<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, getStoredUser } from '../api'

const router = useRouter()
const user = ref(getStoredUser())
const projects = ref([])
const loading = ref(true)
const showEdit = ref(false)
const editForm = ref({ name: '', description: '' })
const members = ref([])
const mentors = ref([])
const phases = ref([])
const showAddMember = ref(false)
const newMemberId = ref('')

const myProject = computed(() => {
  return projects.value.find(p =>
    p.leader_id === user.value?.id ||
    p.members?.some(m => m.user_id === user.value?.id)
  ) || projects.value[0]
})

const isLeader = computed(() => myProject.value?.leader_id === user.value?.id)

const fetchProject = async () => {
  loading.value = true
  try {
    projects.value = await apiRequest('/projects/?skip=0&limit=20') || []
    if (myProject.value) {
      editForm.value = { name: myProject.value.name, description: myProject.value.description || '' }
      const [m, men, ph] = await Promise.all([
        apiRequest(`/projects/${myProject.value.id}/members`).catch(() => []),
        apiRequest(`/projects/${myProject.value.id}/mentors`).catch(() => []),
        apiRequest('/phases/').catch(() => []),
      ])
      members.value = Array.isArray(m) ? m : []
      mentors.value = Array.isArray(men) ? men : []
      phases.value = Array.isArray(ph) ? ph : []
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleSave = async () => {
  try {
    await apiRequest(`/projects/${myProject.value.id}`, { method: 'PUT', body: editForm.value })
    showEdit.value = false
    fetchProject()
  } catch (e) { alert('Error: ' + e.message) }
}

const handleAddMember = async () => {
  if (!newMemberId.value) return
  try {
    await apiRequest(`/projects/${myProject.value.id}/members`, { method: 'POST', body: { user_id: newMemberId.value } })
    newMemberId.value = ''
    showAddMember.value = false
    members.value = await apiRequest(`/projects/${myProject.value.id}/members`)
  } catch (e) { alert('Error: ' + e.message) }
}

const handleRemoveMember = async (userId) => {
  if (!confirm('¿Remover este integrante?')) return
  try {
    await apiRequest(`/projects/${myProject.value.id}/members/${userId}`, { method: 'DELETE' })
    members.value = await apiRequest(`/projects/${myProject.value.id}/members`)
  } catch (e) { alert('Error: ' + e.message) }
}

const currentPhase = computed(() => {
  if (!myProject.value?.current_phase) return null
  return phases.value.find(p => p.id === myProject.value.current_phase_id) || myProject.value.current_phase
})

onMounted(fetchProject)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-6">
    <div>
      <h1 class="font-serif text-2xl font-bold text-parmenia-text">🚀 Mi Proyecto</h1>
      <p class="text-sm text-parmenia-textMuted mt-1">Información y gestión de tu proyecto en la incubadora</p>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">⏳</div>

    <div v-else-if="!myProject" class="card p-8 text-center">
      <span class="text-4xl block mb-2">📭</span>
      <p class="text-sm text-parmenia-textMuted mb-4">No tienes un proyecto activo</p>
      <button @click="router.push('/inscripcion')" class="btn-primary">Inscribirse a convocatoria</button>
    </div>

    <template v-else>
      <!-- Project info -->
      <div class="card p-6">
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <h2 class="font-serif text-xl font-bold text-parmenia-text mb-1">{{ myProject.name }}</h2>
            <p class="text-sm text-parmenia-textMuted">{{ myProject.description || 'Sin descripción' }}</p>
          </div>
          <button v-if="isLeader" @click="showEdit = !showEdit" class="btn-secondary text-xs">✏️ Editar</button>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <span v-if="currentPhase" class="badge-primary">📍 Fase: {{ currentPhase.name }}</span>
          <span class="badge-neutral">👥 {{ members.length }} integrantes</span>
          <span class="badge-neutral">🎓 {{ mentors.length }} mentores</span>
        </div>
      </div>

      <!-- Edit form -->
      <div v-if="showEdit && isLeader" class="card p-5 space-y-3">
        <h3 class="font-serif font-bold text-parmenia-text">Editar proyecto</h3>
        <input v-model="editForm.name" placeholder="Nombre" class="input" />
        <textarea v-model="editForm.description" placeholder="Descripción" class="input" rows="3"></textarea>
        <button @click="handleSave" class="btn-primary w-full">Guardar cambios</button>
      </div>

      <!-- Members -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-serif text-lg font-bold text-parmenia-text">👥 Integrantes</h3>
          <button v-if="isLeader" @click="showAddMember = !showAddMember" class="btn-secondary text-xs">+ Agregar</button>
        </div>
        <div v-if="showAddMember" class="flex gap-2 mb-3">
          <input v-model="newMemberId" placeholder="ID del usuario" class="input flex-1" />
          <button @click="handleAddMember" class="btn-primary text-xs">Agregar</button>
        </div>
        <div v-if="members.length === 0" class="text-sm text-parmenia-textDim text-center py-4">Sin integrantes</div>
        <div v-else class="space-y-2">
          <div v-for="m in members" :key="m.user_id" class="flex items-center justify-between p-2 bg-parmenia-cream rounded-lg">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-parmenia-primarySoft flex items-center justify-center text-xs font-bold text-parmenia-primary">
                {{ (m.user?.full_name || m.user?.email || '?').charAt(0).toUpperCase() }}
              </div>
              <div>
                <p class="text-sm font-medium text-parmenia-text">{{ m.user?.full_name || 'Usuario' }}</p>
                <p class="text-xs text-parmenia-textDim">{{ m.user?.email }}</p>
              </div>
            </div>
            <span v-if="m.user_id === myProject.leader_id" class="badge-primary text-xs">Líder</span>
            <button v-else-if="isLeader" @click="handleRemoveMember(m.user_id)" class="text-xs text-parmenia-danger hover:underline">Remover</button>
          </div>
        </div>
      </div>

      <!-- Mentors -->
      <div class="card p-5">
        <h3 class="font-serif text-lg font-bold text-parmenia-text mb-4">🎓 Mentores Asignados</h3>
        <div v-if="mentors.length === 0" class="text-sm text-parmenia-textDim text-center py-4">Sin mentores asignados</div>
        <div v-else class="space-y-2">
          <div v-for="men in mentors" :key="men.mentor_id" class="flex items-center gap-3 p-2 bg-parmenia-cream rounded-lg">
            <div class="w-8 h-8 rounded-full bg-parmenia-accentSoft flex items-center justify-center text-xs font-bold text-parmenia-accent">
              {{ (men.mentor?.full_name || 'M').charAt(0).toUpperCase() }}
            </div>
            <div>
              <p class="text-sm font-medium text-parmenia-text">{{ men.mentor?.full_name || 'Mentor' }}</p>
              <p class="text-xs text-parmenia-textDim">{{ men.mentor?.email }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
