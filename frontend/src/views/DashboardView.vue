<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, getStoredUser } from '../api'

const router = useRouter()
const user = ref(getStoredUser())
const loading = ref(true)
const stats = ref(null)
const recentPosts = ref([])
const myProject = ref(null)

const fetchDashboard = async () => {
  loading.value = true
  try {
    const [postsRes, projectsRes] = await Promise.all([
      apiRequest('/posts/?skip=0&limit=3'),
      apiRequest('/projects/?skip=0&limit=5').catch(() => []),
    ])
    recentPosts.value = postsRes || []
    const projects = Array.isArray(projectsRes) ? projectsRes : []
    myProject.value = projects.find(p => p.leader_id === user.value?.id || p.members?.some(m => m.user_id === user.value?.id)) || null
    if (user.value?.role === 'admin') {
      stats.value = await apiRequest('/reports/dashboard').catch(() => null)
    }
  } catch (e) {
    console.error('Dashboard error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto space-y-6">
    <!-- Welcome -->
    <div class="card p-6 bg-gradient-to-br from-parmenia-primary to-parmenia-accent text-white border-0">
      <p class="text-sm opacity-80 mb-1">¡Bienvenido de vuelta!</p>
      <h1 class="font-serif text-3xl font-bold mb-2">{{ user?.full_name || user?.email }}</h1>
      <p class="text-sm opacity-90 max-w-lg">
        Aquí puedes ver las últimas noticias de la incubadora, el estado de tu proyecto y próximos pasos.
      </p>
    </div>

    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">
      <span class="text-3xl">⏳</span>
      <p class="mt-2 text-sm">Cargando...</p>
    </div>

    <template v-else>
      <!-- Admin stats -->
      <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-parmenia-primary">{{ stats.users_by_role?.total || 0 }}</p>
          <p class="text-xs text-parmenia-textMuted mt-1">Usuarios</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-parmenia-primary">{{ stats.projects_by_phase?.total || 0 }}</p>
          <p class="text-xs text-parmenia-textMuted mt-1">Proyectos</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-parmenia-primary">{{ stats.active_cohorts || 0 }}</p>
          <p class="text-xs text-parmenia-textMuted mt-1">Convocatorias activas</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold text-parmenia-primary">{{ stats.published_posts || 0 }}</p>
          <p class="text-xs text-parmenia-textMuted mt-1">Publicaciones</p>
        </div>
      </div>

      <div class="grid lg:grid-cols-2 gap-6">
        <!-- Recent news -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-serif text-lg font-bold text-parmenia-text">📰 Últimas Noticias</h2>
            <button @click="router.push('/noticias')" class="text-xs text-parmenia-primary font-semibold hover:underline">Ver todas →</button>
          </div>
          <div v-if="recentPosts.length === 0" class="text-center py-8 text-parmenia-textDim text-sm">
            No hay publicaciones aún
          </div>
          <div v-else class="space-y-3">
            <div v-for="post in recentPosts" :key="post.id" class="border-b border-parmenia-border pb-3 last:border-0">
              <h3 class="font-semibold text-sm text-parmenia-text">{{ post.title }}</h3>
              <p class="text-xs text-parmenia-textMuted mt-1 line-clamp-2">{{ post.content }}</p>
              <p class="text-[10px] text-parmenia-textDim mt-1">
                {{ post.published_at ? new Date(post.published_at).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Borrador' }}
              </p>
            </div>
          </div>
        </div>

        <!-- My project -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-serif text-lg font-bold text-parmenia-text">🚀 Mi Proyecto</h2>
            <button v-if="myProject" @click="router.push('/mi-proyecto')" class="text-xs text-parmenia-primary font-semibold hover:underline">Ver detalle →</button>
          </div>
          <div v-if="!myProject" class="text-center py-8">
            <p class="text-sm text-parmenia-textDim mb-3">Aún no tienes un proyecto activo</p>
            <button @click="router.push('/inscripcion')" class="btn-primary text-xs">Inscribirse a convocatoria</button>
          </div>
          <div v-else class="space-y-2">
            <h3 class="font-semibold text-parmenia-text">{{ myProject.name }}</h3>
            <p class="text-xs text-parmenia-textMuted">{{ myProject.description || 'Sin descripción' }}</p>
            <div class="flex items-center gap-2 pt-2">
              <span v-if="myProject.current_phase" class="badge-primary">Fase: {{ myProject.current_phase.name || myProject.current_phase_id }}</span>
              <span class="badge-neutral">{{ myProject.cohort?.name || 'Sin convocatoria' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="card p-5">
        <h2 class="font-serif text-lg font-bold text-parmenia-text mb-4">⚡ Accesos Rápidos</h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button @click="router.push('/convocatorias')" class="card p-4 hover:border-parmenia-primary transition text-center">
            <span class="text-2xl block mb-1">📋</span>
            <span class="text-xs font-medium text-parmenia-text">Convocatorias</span>
          </button>
          <button @click="router.push('/inscripcion')" class="card p-4 hover:border-parmenia-primary transition text-center">
            <span class="text-2xl block mb-1">✍️</span>
            <span class="text-xs font-medium text-parmenia-text">Inscripción</span>
          </button>
          <button @click="router.push('/entregables')" class="card p-4 hover:border-parmenia-primary transition text-center">
            <span class="text-2xl block mb-1">📦</span>
            <span class="text-xs font-medium text-parmenia-text">Entregables</span>
          </button>
          <button @click="router.push('/noticias')" class="card p-4 hover:border-parmenia-primary transition text-center">
            <span class="text-2xl block mb-1">📰</span>
            <span class="text-xs font-medium text-parmenia-text">Noticias</span>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
