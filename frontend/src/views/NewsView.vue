<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiRequest, getStoredUser } from '../api'

const user = ref(getStoredUser())
const posts = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingPost = ref(null)
const formData = ref({ title: '', content: '', image_url: '', is_published: false })

const isAdmin = computed(() => user.value?.role === 'admin')
const isMentor = computed(() => user.value?.role === 'mentor')
const canCreate = computed(() => isAdmin.value || isMentor.value)

const publishedPosts = computed(() => {
  if (isAdmin.value) return posts.value
  return posts.value.filter(p => p.is_published)
})

const fetchPosts = async () => {
  loading.value = true
  try {
    posts.value = await apiRequest('/posts/?skip=0&limit=50') || []
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleSave = async () => {
  try {
    if (editingPost.value) {
      await apiRequest(`/posts/${editingPost.value.id}`, { method: 'PUT', body: formData.value })
    } else {
      await apiRequest('/posts/', { method: 'POST', body: formData.value })
    }
    showForm.value = false
    editingPost.value = null
    formData.value = { title: '', content: '', image_url: '', is_published: false }
    fetchPosts()
  } catch (e) { alert('Error: ' + e.message) }
}

const handleEdit = (post) => {
  editingPost.value = post
  formData.value = { title: post.title, content: post.content, image_url: post.image_url || '', is_published: post.is_published }
  showForm.value = true
}

const handleDelete = async (id) => {
  if (!confirm('¿Eliminar esta publicación?')) return
  try {
    await apiRequest(`/posts/${id}`, { method: 'DELETE' })
    fetchPosts()
  } catch (e) { alert('Error: ' + e.message) }
}

onMounted(fetchPosts)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="font-serif text-2xl font-bold text-parmenia-text">📰 Noticias y Anuncios</h1>
        <p class="text-sm text-parmenia-textMuted mt-1">Eventos, publicaciones y novedades de la incubadora Parmenia</p>
      </div>
      <button v-if="canCreate" @click="showForm = !showForm; editingPost = null" class="btn-primary">
        {{ showForm ? 'Cancelar' : '+ Nueva publicación' }}
      </button>
    </div>

    <!-- Form -->
    <div v-if="showForm && canCreate" class="card p-5 space-y-3">
      <h2 class="font-serif text-lg font-bold text-parmenia-text">{{ editingPost ? 'Editar' : 'Nueva' }} publicación</h2>
      <input v-model="formData.title" placeholder="Título" class="input" />
      <textarea v-model="formData.content" placeholder="Contenido..." class="input" rows="4"></textarea>
      <input v-model="formData.image_url" placeholder="URL de imagen (opcional)" class="input" />
      <label class="flex items-center gap-2 text-sm text-parmenia-textMuted">
        <input type="checkbox" v-model="formData.is_published" class="w-4 h-4" />
        Publicar inmediatamente
      </label>
      <button @click="handleSave" class="btn-primary w-full">{{ editingPost ? 'Guardar cambios' : 'Crear publicación' }}</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-parmenia-textMuted">
      <span class="text-3xl">⏳</span>
      <p class="mt-2 text-sm">Cargando noticias...</p>
    </div>

    <!-- Posts -->
    <div v-else-if="publishedPosts.length === 0" class="card p-8 text-center">
      <span class="text-4xl block mb-2">📭</span>
      <p class="text-sm text-parmenia-textMuted">No hay publicaciones disponibles</p>
    </div>

    <div v-else class="space-y-4">
      <article v-for="post in publishedPosts" :key="post.id" class="card overflow-hidden">
        <img v-if="post.image_url" :src="post.image_url" :alt="post.title" class="w-full h-48 object-cover" />
        <div class="p-5">
          <div class="flex items-start justify-between gap-3 mb-2">
            <h2 class="font-serif text-xl font-bold text-parmenia-text">{{ post.title }}</h2>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span v-if="!post.is_published" class="badge-warning">Borrador</span>
              <span v-else class="badge-success">Publicado</span>
            </div>
          </div>
          <p class="text-sm text-parmenia-textMuted whitespace-pre-wrap">{{ post.content }}</p>
          <div class="flex items-center justify-between mt-4 pt-3 border-t border-parmenia-border">
            <span class="text-xs text-parmenia-textDim">
              {{ post.published_at ? new Date(post.published_at).toLocaleDateString('es-PE', { day: '2-digit', month: 'long', year: 'numeric' }) : 'Sin publicar' }}
            </span>
            <div v-if="canCreate" class="flex gap-2">
              <button @click="handleEdit(post)" class="text-xs text-parmenia-primary font-semibold hover:underline">Editar</button>
              <button @click="handleDelete(post.id)" class="text-xs text-parmenia-danger font-semibold hover:underline">Eliminar</button>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
