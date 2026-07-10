<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest, authApi, clearSession, getStoredUser, setSession, notificationsApi, commentsApi, uploadApi, mentorshipsApi, projectsApi } from './api'

/* ─── Auth state ─── */
const user = ref(getStoredUser())
const token = ref(localStorage.getItem('parmenia_token') || '')
const activeKey = ref('dashboard')
const loading = ref(false)
const notice = ref('')
const error = ref('')

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ email: '', password: '', full_name: '', faculty: '', skills: '', role: 'emprendedor' })
const showRegister = ref(false)

const isAuthenticated = computed(() => Boolean(token.value && user.value))
const isAdmin = computed(() => user.value?.role === 'admin')
const isMentor = computed(() => user.value?.role === 'mentor')
const sessionName = computed(() => user.value?.full_name || user.value?.email || 'Usuario')
const roleLabel = computed(() => ({ admin: 'Administrador', mentor: 'Mentor', emprendedor: 'Emprendedor' }[user.value?.role] || 'Usuario'))

/* ─── Notifications ─── */
const unreadCount = ref(0)
const showNotifPanel = ref(false)
const notifList = ref([])
const notifLoading = ref(false)

const fetchUnreadCount = async () => {
  if (!isAuthenticated.value) return
  try { const res = await notificationsApi.unreadCount(); unreadCount.value = res.unread || 0 } catch {}
}
const fetchNotifications = async () => {
  notifLoading.value = true
  try { notifList.value = await notificationsApi.list(false) } catch {} finally { notifLoading.value = false }
}
const toggleNotifPanel = async () => {
  showNotifPanel.value = !showNotifPanel.value
  if (showNotifPanel.value && notifList.value.length === 0) await fetchNotifications()
}
const markNotifRead = async (id) => { await notificationsApi.markRead(id); await fetchNotifications(); await fetchUnreadCount() }
const markAllNotifRead = async () => { await notificationsApi.markAllRead(); await fetchNotifications(); await fetchUnreadCount() }

/* ─── Navigation ─── */
const navItems = computed(() => {
  const items = [
    { key: 'dashboard', label: 'Dashboard', icon: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z' },
    { key: 'noticias', label: 'Noticias', icon: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z' },
    { key: 'convocatorias', label: 'Convocatorias', icon: 'M3 5h18v2H3V5zm0 4h18v2H3V9zm0 4h12v2H3v-2zm0 4h12v2H3v-2zm14-2.5l4 2.5-4 2.5v-5z' },
    { key: 'inscripcion', label: 'Inscripción', icon: 'M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm-2 14l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z' },
    { key: 'mi-proyecto', label: 'Mi Proyecto', icon: 'M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L19.82 8 12 11.82 4.18 8 12 4.18zM4 9.82l7 3.5v7.86l-7-3.5V9.82zm9 11.36v-7.86l7-3.5v7.86l-7 3.5z' },
    { key: 'entregables', label: 'Entregables', icon: 'M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2z' },
  ]
  if (isMentor.value) items.push({ key: 'mentor', label: 'Mis Mentorías', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z' })
  if (isAdmin.value) items.push({ key: 'admin', label: 'Administración', icon: 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z' })
  return items
})

/* ─── Data stores ─── */
const data = reactive({
  posts: [], cohorts: [], enrollments: [], projects: [], phases: [],
  members: [], mentors: [], deliverables: [], reviews: {}, comments: {},
  myEnrollments: [], myProject: null, dashboardStats: null, myStats: null,
  selectedCohort: null, showCohortDetail: false,
  projectDetail: null, showProjectDetail: false,
  mentorProjects: [], mentorships: [],
  mentorDeliverables: [],
})

/* ─── Forms ─── */
const forms = reactive({
  post: { title: '', content: '', image_url: '', is_published: false },
  showPostForm: false, editingPost: null,
  cohort: { name: '', description: '', start_date: '', end_date: '' },
  showCohortForm: false,
  project: { name: '', description: '' },
  showProjectEdit: false,
  deliverable: { phase_id: '', file_url: '' },
  showDeliverableForm: false, uploadingFile: false,
  newMemberSearch: '', showAddMember: false, searchResults: [], searchingMembers: false,
  review: {}, showReviewForm: {},
  comment: {}, showCommentForm: {},
  profile: { full_name: '', faculty: '', skills: '' }, profileLoaded: false,
  mentorship: { title: 'Mentoría Parmenia', description: '', start_datetime: '', end_datetime: '', attendee_emails: '', create_meet: true },
  showMentorshipForm: false, mentorshipResult: null, schedulingMentorship: false,
  adminPhaseChange: { project_id: '', phase_id: '' },
})

/* ─── Auth handlers ─── */
const handleLogin = async () => {
  loading.value = true; error.value = ''
  try { const res = await authApi.login(loginForm.email, loginForm.password); setSession(res.access_token, res.user); user.value = res.user; token.value = res.access_token; await loadAll(); await fetchUnreadCount() }
  catch (e) { error.value = e.message } finally { loading.value = false }
}
const handleRegister = async () => {
  loading.value = true; error.value = ''
  try { const payload = { ...registerForm, skills: registerForm.skills ? registerForm.skills.split(',').map(s => s.trim()) : [] }; const res = await authApi.register(payload); setSession(res.access_token, res.user); user.value = res.user; token.value = res.access_token; await loadAll(); await fetchUnreadCount() }
  catch (e) { error.value = e.message } finally { loading.value = false }
}
const handleGoogle = async (response) => {
  loading.value = true; error.value = ''
  try { const res = await authApi.googleLogin(response.credential); setSession(res.access_token, res.user); user.value = res.user; token.value = res.access_token; await loadAll(); await fetchUnreadCount() }
  catch (e) { error.value = e.message } finally { loading.value = false }
}
const handleLogout = () => { clearSession(); user.value = null; token.value = '' }

/* ─── Data loaders ─── */
const loadAll = async () => {
  loading.value = true
  try {
    await Promise.all([loadPosts(), loadCohorts(), loadEnrollments(), loadProjects(), loadPhases()])
    if (isAdmin.value) loadDashboard()
    findMyProject()
    data.myStats = await projectsApi.myStats().catch(() => null)
  } catch (e) { console.error(e) } finally { loading.value = false }
}
const loadPosts = async () => { data.posts = await apiRequest('/posts/?skip=0&limit=50') || [] }
const loadCohorts = async () => { data.cohorts = await apiRequest('/cohorts/') || [] }
const loadEnrollments = async () => { data.enrollments = await apiRequest('/enrollments/') || []; data.myEnrollments = data.enrollments.filter(e => e.user_id === user.value?.id) }
const loadProjects = async () => { data.projects = await apiRequest('/projects/?skip=0&limit=50') || [] }
const loadPhases = async () => { data.phases = await apiRequest('/phases/') || [] }
const loadDashboard = async () => { data.dashboardStats = await apiRequest('/reports/dashboard').catch(() => null) }
const findMyProject = () => { data.myProject = data.projects.find(p => p.leader_id === user.value?.id) || null }

const loadMembers = async (pid) => { data.members = await apiRequest(`/projects/${pid}/members`) || [] }
const loadMentors = async (pid) => { data.mentors = await apiRequest(`/projects/${pid}/mentors`) || [] }
const loadDeliverables = async (pid) => {
  data.deliverables = await apiRequest(`/projects/${pid}/deliverables`) || []
  data.reviews = {}; data.comments = {}
  for (const d of data.deliverables) {
    try { data.reviews[d.id] = await apiRequest(`/deliverables/${d.id}/reviews`) || [] } catch { data.reviews[d.id] = [] }
    try { data.comments[d.id] = await commentsApi.list(d.id) } catch { data.comments[d.id] = [] }
  }
}

/* ─── Mentor data ─── */
const loadMentorData = async () => {
  // Cargar mentorías persistidas
  data.mentorships = await mentorshipsApi.list().catch(() => [])
  // Cargar proyectos donde el mentor está asignado
  const allProjects = await apiRequest('/projects/?skip=0&limit=50') || []
  const myMentorProjects = []
  for (const p of allProjects) {
    try {
      const mentors = await apiRequest(`/projects/${p.id}/mentors`) || []
      if (mentors.some(m => m.mentor_id === user.value?.id)) {
        // Cargar entregables del proyecto
        const dels = await apiRequest(`/projects/${p.id}/deliverables`) || []
        p._deliverables = dels
        p._pendingReviews = dels.filter(d => {
          const reviews = data.reviews[d.id] || []
          return !reviews.some(r => r.status === 'aprobado')
        })
        myMentorProjects.push(p)
      }
    } catch {}
  }
  data.mentorProjects = myMentorProjects
}

/* ─── Nav handler ─── */
const handleNavClick = async (key) => {
  activeKey.value = key; data.showCohortDetail = false; data.showProjectDetail = false; notice.value = ''; showNotifPanel.value = false
  if (key === 'mi-proyecto' && data.myProject) { await loadMembers(data.myProject.id); await loadMentors(data.myProject.id) }
  if (key === 'entregables' && data.myProject) { await loadDeliverables(data.myProject.id) }
  if (key === 'perfil') { forms.profile = { full_name: user.value?.full_name || '', faculty: user.value?.faculty || '', skills: Array.isArray(user.value?.skills) ? user.value?.skills.join(', ') : '' }; forms.profileLoaded = true }
  if (key === 'mentor') { await loadMentorData() }
}

/* ─── Post handlers ─── */
const savePost = async () => {
  try { if (forms.editingPost) await apiRequest(`/posts/${forms.editingPost.id}`, { method: 'PUT', body: forms.post }); else await apiRequest('/posts/', { method: 'POST', body: forms.post }); forms.showPostForm = false; forms.editingPost = null; forms.post = { title: '', content: '', image_url: '', is_published: false }; await loadPosts() }
  catch (e) { error.value = e.message }
}
const editPost = (p) => { forms.editingPost = p; forms.post = { title: p.title, content: p.content, image_url: p.image_url || '', is_published: p.is_published }; forms.showPostForm = true }
const deletePost = async (id) => { if (!confirm('¿Eliminar?')) return; await apiRequest(`/posts/${id}`, { method: 'DELETE' }); loadPosts() }

/* ─── Cohort handlers ─── */
const saveCohort = async () => { await apiRequest('/cohorts/', { method: 'POST', body: forms.cohort }); forms.showCohortForm = false; forms.cohort = { name: '', description: '', start_date: '', end_date: '' }; loadCohorts() }
const viewCohort = (c) => { data.selectedCohort = c; data.showCohortDetail = true }
const viewProjectDetail = async (p) => { data.projectDetail = await projectsApi.publicDetail(p.id); data.showProjectDetail = true }

/* ─── Enrollment handlers ─── */
const enroll = async (cid) => { try { await apiRequest('/enrollments/', { method: 'POST', body: { cohort_id: cid } }); await loadEnrollments() } catch (e) { error.value = e.message } }
const isEnrolled = (cid) => data.myEnrollments.some(e => e.cohort_id === cid)
const updateEnrollmentStatus = async (id, status) => { await apiRequest(`/enrollments/${id}/status`, { method: 'PUT', body: { status } }); loadEnrollments() }

/* ─── Project handlers ─── */
const saveProject = async () => { await apiRequest(`/projects/${data.myProject.id}`, { method: 'PUT', body: forms.project }); forms.showProjectEdit = false; loadProjects(); findMyProject() }

const searchMembers = async () => {
  if (!forms.newMemberSearch.trim() || forms.newMemberSearch.trim().length < 2) { forms.searchResults = []; return }
  forms.searchingMembers = true
  try {
    // Usar el parámetro search del endpoint
    const results = await apiRequest(`/profiles/?search=${encodeURIComponent(forms.newMemberSearch)}&limit=10`)
    forms.searchResults = (Array.isArray(results) ? results : []).filter(p => p.id !== user.value?.id)
  } catch { forms.searchResults = [] }
  finally { forms.searchingMembers = false }
}

const addMember = async (userId) => {
  try { await apiRequest(`/projects/${data.myProject.id}/members`, { method: 'POST', body: { user_id: userId } }); forms.newMemberSearch = ''; forms.searchResults = []; forms.showAddMember = false; await loadMembers(data.myProject.id) }
  catch (e) { error.value = e.message }
}
const removeMember = async (uid) => { if (!confirm('¿Remover?')) return; await apiRequest(`/projects/${data.myProject.id}/members/${uid}`, { method: 'DELETE' }); loadMembers(data.myProject.id) }

/* ─── Deliverable handlers ─── */
const handleFileUpload = async (event) => { const file = event.target.files[0]; if (!file) return; forms.uploadingFile = true; try { const res = await uploadApi.upload(file); forms.deliverable.file_url = res.url } catch (e) { error.value = 'Error al subir archivo: ' + e.message } finally { forms.uploadingFile = false } }
const uploadDeliverable = async () => { await apiRequest(`/projects/${data.myProject.id}/deliverables`, { method: 'POST', body: { phase_id: parseInt(forms.deliverable.phase_id), file_url: forms.deliverable.file_url } }); forms.showDeliverableForm = false; forms.deliverable = { phase_id: '', file_url: '' }; await loadDeliverables(data.myProject.id); await fetchUnreadCount() }
const submitReview = async (did) => { await apiRequest(`/deliverables/${did}/reviews`, { method: 'POST', body: forms.review[did] || { status: 'pendiente', feedback: '' } }); forms.showReviewForm[did] = false; await loadDeliverables(data.myProject.id); await fetchUnreadCount() }

/* ─── Mentor review from mentor panel ─── */
const submitMentorReview = async (deliverableId, projectId) => {
  await apiRequest(`/deliverables/${deliverableId}/reviews`, { method: 'POST', body: forms.review[deliverableId] || { status: 'pendiente', feedback: '' } })
  forms.showReviewForm[deliverableId] = false
  await loadMentorData()
  await fetchUnreadCount()
}

/* ─── Comment handlers ─── */
const submitComment = async (did) => {
  if (!forms.comment[did]?.trim()) return
  try { await commentsApi.create(did, forms.comment[did]); forms.comment[did] = ''; data.comments[did] = await commentsApi.list(did); await fetchUnreadCount() }
  catch (e) { error.value = e.message }
}

/* ─── Admin: change phase ─── */
const adminChangePhase = async () => { try { await projectsApi.changePhase(forms.adminPhaseChange.project_id, parseInt(forms.adminPhaseChange.phase_id)); notice.value = 'Fase actualizada'; forms.adminPhaseChange = { project_id: '', phase_id: '' }; await loadProjects() } catch (e) { error.value = e.message } }

/* ─── Google Calendar mentorship ─── */
const scheduleMentorship = async () => {
  if (!window.google) { error.value = 'Google no está cargado'; return }
  forms.schedulingMentorship = true
  const tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    scope: 'https://www.googleapis.com/auth/calendar.events',
    callback: async (tokenResponse) => {
      if (tokenResponse.error) { error.value = 'Error de autorización'; forms.schedulingMentorship = false; return }
      try {
        const res = await mentorshipsApi.create({
          google_access_token: tokenResponse.access_token,
          project_id: data.myProject?.id || null,
          title: forms.mentorship.title,
          description: forms.mentorship.description,
          start_datetime: forms.mentorship.start_datetime,
          end_datetime: forms.mentorship.end_datetime,
          attendee_emails: forms.mentorship.attendee_emails ? forms.mentorship.attendee_emails.split(',').map(e => e.trim()) : [],
          create_meet: forms.mentorship.create_meet,
        })
        forms.mentorshipResult = res
        forms.showMentorshipForm = false
        // Recargar lista de mentorías
        data.mentorships = await mentorshipsApi.list().catch(() => [])
        await fetchUnreadCount()
      } catch (e) { error.value = e.message }
      finally { forms.schedulingMentorship = false }
    },
  })
  tokenClient.requestAccessToken()
}

/* ─── Profile handler ─── */
const saveProfile = async () => { await apiRequest(`/profiles/${user.value.id}`, { method: 'PUT', body: { full_name: forms.profile.full_name, faculty: forms.profile.faculty, skills: forms.profile.skills ? forms.profile.skills.split(',').map(s => s.trim()) : [] } }); const me = await apiRequest('/auth/me'); user.value = me; setSession(token.value, me); notice.value = 'Perfil actualizado' }

/* ─── Helpers ─── */
const today = new Date().toISOString().split('T')[0]
const activeCohorts = computed(() => data.cohorts.filter(c => !c.end_date || c.end_date >= today))
const pastCohorts = computed(() => data.cohorts.filter(c => c.end_date && c.end_date < today))
const publishedPosts = computed(() => isAdmin.value ? data.posts : data.posts.filter(p => p.is_published))
const phaseName = (id) => data.phases.find(p => p.id === id)?.name || `Fase ${id}`
const canCreatePost = computed(() => isAdmin.value || isMentor.value)
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
const fmtDateTime = (d) => d ? new Date(d).toLocaleString('es-PE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
onMounted(() => {
  if (isAuthenticated.value) { loadAll(); fetchUnreadCount() }
  if (googleClientId && window.google) { window.google.accounts.id.initialize({ client_id: googleClientId, callback: handleGoogle }) }
  if (isAuthenticated.value) setInterval(fetchUnreadCount, 60000)
})
const renderGoogle = () => { if (googleClientId && window.google && !isAuthenticated.value) window.google.accounts.id.renderButton(document.getElementById('google-btn'), { theme: 'outline', size: 'large', width: '100%' }) }
</script>

<template>
  <!-- ═══ NO AUTENTICADO ═══ -->
  <div v-if="!isAuthenticated" class="min-h-screen bg-parmenia-bg flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="w-14 h-14 mx-auto rounded-lg bg-parmenia-primary flex items-center justify-center text-white font-bold text-xl mb-4">P</div>
        <h1 class="text-2xl font-bold text-parmenia-text">Parmenia</h1>
        <p class="text-sm text-parmenia-textMuted mt-1">Incubadora de Empresas · Universidad La Salle</p>
      </div>
      <div class="card p-6 space-y-4">
        <div class="flex gap-1 p-1 bg-parmenia-bg rounded-lg">
          <button @click="showRegister = false" class="flex-1 py-1.5 rounded-md text-sm font-semibold transition" :class="!showRegister ? 'bg-white text-parmenia-primary shadow-sm' : 'text-parmenia-textMuted'">Iniciar sesión</button>
          <button @click="showRegister = true" class="flex-1 py-1.5 rounded-md text-sm font-semibold transition" :class="showRegister ? 'bg-white text-parmenia-primary shadow-sm' : 'text-parmenia-textMuted'">Registrarse</button>
        </div>
        <div v-if="error" class="bg-parmenia-dangerSoft border border-parmenia-danger/20 rounded-md px-3 py-2 text-sm text-parmenia-danger">{{ error }}</div>
        <form v-if="!showRegister" @submit.prevent="handleLogin" class="space-y-3">
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Correo</label><input v-model="loginForm.email" type="email" required placeholder="tu@ulasalle.edu.pe" class="input" /></div>
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Contraseña</label><input v-model="loginForm.password" type="password" required placeholder="••••••••" class="input" /></div>
          <button type="submit" :disabled="loading" class="btn-primary w-full"><span v-if="loading">⏳</span> Ingresar</button>
        </form>
        <form v-else @submit.prevent="handleRegister" class="space-y-3">
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Nombre completo</label><input v-model="registerForm.full_name" type="text" required class="input" /></div>
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Correo</label><input v-model="registerForm.email" type="email" required class="input" /></div>
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Contraseña</label><input v-model="registerForm.password" type="password" required minlength="6" class="input" /></div>
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Facultad</label><input v-model="registerForm.faculty" type="text" class="input" /></div>
          <div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Habilidades (comas)</label><input v-model="registerForm.skills" type="text" class="input" /></div>
          <button type="submit" :disabled="loading" class="btn-primary w-full"><span v-if="loading">⏳</span> Crear cuenta</button>
        </form>
        <div class="flex items-center gap-3 py-1"><div class="flex-1 h-px bg-parmenia-border"></div><span class="text-xs text-parmenia-textDim">o</span><div class="flex-1 h-px bg-parmenia-border"></div></div>
        <div id="google-btn" class="flex justify-center" :data-render="renderGoogle()"></div>
      </div>
      <p class="text-center text-xs text-parmenia-textDim mt-6">Parmenia v1.0 · Universidad La Salle</p>
    </div>
  </div>

  <!-- ═══ AUTENTICADO ═══ -->
  <div v-else class="flex h-screen overflow-hidden bg-parmenia-bg">
    <aside class="w-56 bg-parmenia-sidebar flex flex-col flex-shrink-0">
      <div class="px-5 py-4 border-b border-parmenia-sidebarHover"><div class="flex items-center gap-2.5"><div class="w-8 h-8 rounded-md bg-parmenia-primary flex items-center justify-center text-white font-bold text-sm">P</div><div><h1 class="text-sm font-bold text-parmenia-textLight tracking-wide">PARMENIA</h1><p class="text-[10px] text-parmenia-textLightMuted">Incubadora La Salle</p></div></div></div>
      <div class="px-5 py-2"><span class="inline-block text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-parmenia-primary/20 text-parmenia-primary">{{ roleLabel }}</span></div>
      <nav class="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        <button v-for="item in navItems" :key="item.key" @click="handleNavClick(item.key)" class="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors text-left" :class="activeKey === item.key ? 'bg-parmenia-primary text-white' : 'text-parmenia-textLightMuted hover:bg-parmenia-sidebarHover hover:text-parmenia-textLight'"><svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path :d="item.icon" /></svg>{{ item.label }}</button>
      </nav>
      <div class="px-3 py-2 border-t border-parmenia-sidebarHover relative">
        <button @click="toggleNotifPanel" class="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-parmenia-textLightMuted hover:bg-parmenia-sidebarHover hover:text-parmenia-textLight transition-colors"><div class="relative"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg><span v-if="unreadCount > 0" class="absolute -top-1 -right-1 bg-parmenia-danger text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">{{ unreadCount > 9 ? '9+' : unreadCount }}</span></div><span class="flex-1 text-left text-xs">Notificaciones</span></button>
        <div v-if="showNotifPanel" class="absolute bottom-full left-0 right-0 mb-1 mx-3 bg-white rounded-lg shadow-xl border border-parmenia-border max-h-80 overflow-y-auto z-50">
          <div class="flex items-center justify-between p-2 border-b border-parmenia-border"><span class="text-xs font-bold text-parmenia-text">Notificaciones</span><button @click="markAllNotifRead" class="text-[10px] text-parmenia-primary font-semibold hover:underline">Marcar todas</button></div>
          <div v-if="notifLoading" class="p-4 text-center text-xs text-parmenia-textDim">Cargando...</div>
          <div v-else-if="notifList.length === 0" class="p-4 text-center text-xs text-parmenia-textDim">Sin notificaciones</div>
          <div v-else class="divide-y divide-parmenia-border"><button v-for="n in notifList.slice(0, 15)" :key="n.id" @click="markNotifRead(n.id)" class="w-full flex items-start gap-2 p-2.5 text-left hover:bg-parmenia-bg transition-colors" :class="!n.is_read ? 'bg-parmenia-primarySoft/30' : ''"><div class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" :class="n.is_read ? 'bg-parmenia-textDim' : 'bg-parmenia-primary'"></div><div class="flex-1 min-w-0"><p class="text-xs font-medium text-parmenia-text truncate">{{ n.title }}</p><p class="text-[11px] text-parmenia-textMuted line-clamp-2">{{ n.message }}</p><p class="text-[10px] text-parmenia-textDim mt-0.5">{{ fmtDateTime(n.created_at) }}</p></div></button></div>
        </div>
      </div>
      <div class="p-3 border-t border-parmenia-sidebarHover space-y-0.5">
        <button @click="handleNavClick('perfil')" class="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-parmenia-textLightMuted hover:bg-parmenia-sidebarHover hover:text-parmenia-textLight transition-colors"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg><span class="flex-1 text-left truncate text-xs">{{ sessionName }}</span></button>
        <button @click="handleLogout" class="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-parmenia-textLightMuted hover:bg-parmenia-danger/20 hover:text-parmenia-danger transition-colors"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg><span class="text-xs">Cerrar sesión</span></button>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-w-0">
      <div v-if="loading" class="flex items-center justify-center py-20"><div class="w-8 h-8 border-2 border-parmenia-primary border-t-transparent rounded-full animate-spin"></div></div>
      <div v-else class="max-w-5xl mx-auto p-6 space-y-5">

        <!-- ═══ DASHBOARD ═══ -->
        <template v-if="activeKey === 'dashboard'">
          <div class="card p-5 border-l-4 border-l-parmenia-primary"><p class="text-xs text-parmenia-textMuted mb-1">Bienvenido</p><h1 class="text-xl font-bold text-parmenia-text mb-1">{{ sessionName }}</h1><p class="text-sm text-parmenia-textMuted">{{ roleLabel === 'Mentor' ? 'Revisa los entregables pendientes de tus proyectos asignados' : roleLabel === 'Administrador' ? 'Gestiona la incubadora Parmenia' : 'Noticias, estado de tu proyecto y próximos pasos.' }}</p></div>
          <div v-if="isAdmin && data.dashboardStats" class="grid grid-cols-2 sm:grid-cols-4 gap-3"><div class="card p-4"><p class="text-2xl font-bold text-parmenia-primary">{{ data.dashboardStats.users_by_role?.total || 0 }}</p><p class="text-xs text-parmenia-textMuted mt-0.5">Usuarios</p></div><div class="card p-4"><p class="text-2xl font-bold text-parmenia-primary">{{ data.dashboardStats.projects_by_phase?.total || 0 }}</p><p class="text-xs text-parmenia-textMuted mt-0.5">Proyectos</p></div><div class="card p-4"><p class="text-2xl font-bold text-parmenia-primary">{{ data.dashboardStats.active_cohorts || 0 }}</p><p class="text-xs text-parmenia-textMuted mt-0.5">Convocatorias</p></div><div class="card p-4"><p class="text-2xl font-bold text-parmenia-primary">{{ data.dashboardStats.published_posts || 0 }}</p><p class="text-xs text-parmenia-textMuted mt-0.5">Publicaciones</p></div></div>
          <div v-if="!isAdmin && !isMentor && data.myStats" class="grid grid-cols-2 sm:grid-cols-4 gap-3"><div class="card p-4"><p class="text-lg font-bold text-parmenia-primary">{{ data.myStats.progress_percentage }}%</p><p class="text-xs text-parmenia-textMuted">Progreso</p></div><div class="card p-4"><p class="text-lg font-bold text-parmenia-primary">{{ data.myStats.current_phase || '—' }}</p><p class="text-xs text-parmenia-textMuted">Fase actual</p></div><div class="card p-4"><p class="text-lg font-bold text-parmenia-primary">{{ data.myStats.deliverables_uploaded }}</p><p class="text-xs text-parmenia-textMuted">Entregables</p></div><div class="card p-4"><p class="text-lg font-bold text-parmenia-primary">{{ data.myStats.deliverables_approved }}</p><p class="text-xs text-parmenia-textMuted">Aprobados</p></div></div>
          <div v-if="!isAdmin && !isMentor && data.myStats && data.myStats.total_phases > 0" class="card p-4"><div class="flex items-center justify-between mb-2"><span class="text-xs font-semibold text-parmenia-textMuted">Progreso del proyecto</span><span class="text-xs font-bold text-parmenia-primary">{{ data.myStats.progress_percentage }}%</span></div><div class="w-full h-2 bg-parmenia-bg rounded-full overflow-hidden"><div class="h-full bg-parmenia-primary rounded-full transition-all duration-500" :style="{ width: data.myStats.progress_percentage + '%' }"></div></div><p class="text-[10px] text-parmenia-textDim mt-1">Fase {{ data.myStats.current_phase_order }} de {{ data.myStats.total_phases }}</p></div>
          <div v-if="isMentor" class="card p-4"><h2 class="text-sm font-bold text-parmenia-text mb-2">Proyectos Asignados</h2><p v-if="data.mentorProjects.length === 0" class="text-sm text-parmenia-textDim">No tienes proyectos asignados. Pide al administrador que te asigne.</p><div v-else class="space-y-2"><div v-for="p in data.mentorProjects" :key="p.id" class="flex items-center justify-between p-2 bg-parmenia-bg rounded-md"><div><p class="text-sm font-medium text-parmenia-text">{{ p.name }}</p><p class="text-xs text-parmenia-textDim">{{ p._pendingReviews?.length || 0 }} entregable(s) por revisar</p></div><button @click="handleNavClick('mentor')" class="btn-primary text-xs">Ver</button></div></div></div>
          <div class="grid lg:grid-cols-2 gap-4">
            <div class="card p-4"><div class="flex items-center justify-between mb-3"><h2 class="text-sm font-bold text-parmenia-text">Últimas Noticias</h2><button @click="handleNavClick('noticias')" class="text-xs text-parmenia-primary font-semibold hover:underline">Ver todas</button></div><div v-if="publishedPosts.length === 0" class="text-center py-4 text-parmenia-textDim text-sm">Sin publicaciones</div><div v-else class="space-y-2"><div v-for="p in publishedPosts.slice(0, 3)" :key="p.id" class="border-b border-parmenia-border pb-2 last:border-0"><p class="text-sm font-medium text-parmenia-text">{{ p.title }}</p><p class="text-xs text-parmenia-textMuted line-clamp-1 mt-0.5">{{ p.content }}</p></div></div></div>
            <div class="card p-4"><h2 class="text-sm font-bold text-parmenia-text mb-3">{{ isMentor ? 'Próximas Mentorías' : 'Mi Proyecto' }}</h2><div v-if="isMentor"><div v-if="data.mentorships.length === 0" class="text-center py-4 text-parmenia-textDim text-sm">Sin mentorías</div><div v-else class="space-y-2"><div v-for="m in data.mentorships.slice(0, 3)" :key="m.id" class="border-b border-parmenia-border pb-2 last:border-0"><p class="text-sm font-medium text-parmenia-text">{{ m.title }}</p><p class="text-xs text-parmenia-textDim">{{ fmtDateTime(m.start_datetime) }}</p></div></div></div><div v-else-if="!data.myProject" class="text-center py-4"><p class="text-sm text-parmenia-textDim mb-2">Sin proyecto activo</p><button @click="handleNavClick('inscripcion')" class="btn-primary text-xs">Inscribirse</button></div><div v-else><p class="text-sm font-medium text-parmenia-text">{{ data.myProject.name }}</p><p class="text-xs text-parmenia-textMuted mt-0.5">{{ data.myProject.description || 'Sin descripción' }}</p></div></div>
          </div>
        </template>

        <!-- ═══ NOTICIAS ═══ -->
        <template v-if="activeKey === 'noticias'">
          <div class="flex items-center justify-between"><h1 class="text-lg font-bold text-parmenia-text">Noticias</h1><button v-if="canCreatePost" @click="forms.showPostForm = !forms.showPostForm" class="btn-primary text-xs">{{ forms.showPostForm ? 'Cancelar' : '+ Nueva' }}</button></div>
          <div v-if="forms.showPostForm && canCreatePost" class="card p-4 space-y-3"><input v-model="forms.post.title" placeholder="Título" class="input" /><textarea v-model="forms.post.content" placeholder="Contenido..." class="input" rows="4"></textarea><input v-model="forms.post.image_url" placeholder="URL imagen (opcional)" class="input" /><label class="flex items-center gap-2 text-sm text-parmenia-textMuted"><input type="checkbox" v-model="forms.post.is_published" class="w-4 h-4" /> Publicar</label><button @click="savePost" class="btn-primary w-full">{{ forms.editingPost ? 'Guardar' : 'Crear' }}</button></div>
          <div v-if="publishedPosts.length === 0" class="card p-8 text-center text-parmenia-textMuted text-sm">Sin publicaciones</div>
          <div v-else class="space-y-3"><div v-for="p in publishedPosts" :key="p.id" class="card p-4"><div class="flex items-start justify-between gap-2 mb-2"><h2 class="text-base font-bold text-parmenia-text">{{ p.title }}</h2><span :class="p.is_published ? 'badge-success' : 'badge-warning'" class="flex-shrink-0 text-[10px]">{{ p.is_published ? 'Publicado' : 'Borrador' }}</span></div><p class="text-sm text-parmenia-textMuted whitespace-pre-wrap">{{ p.content }}</p><div class="flex items-center justify-between mt-3 pt-2 border-t border-parmenia-border"><span class="text-xs text-parmenia-textDim">{{ fmtDate(p.published_at) || 'Sin publicar' }}</span><div v-if="canCreatePost" class="flex gap-2"><button @click="editPost(p)" class="text-xs text-parmenia-primary font-semibold hover:underline">Editar</button><button @click="deletePost(p.id)" class="text-xs text-parmenia-danger font-semibold hover:underline">Eliminar</button></div></div></div></div>
        </template>

        <!-- ═══ CONVOCATORIAS ═══ -->
        <template v-if="activeKey === 'convocatorias' && !data.showCohortDetail && !data.showProjectDetail">
          <div class="flex items-center justify-between"><h1 class="text-lg font-bold text-parmenia-text">Convocatorias</h1><button v-if="isAdmin" @click="forms.showCohortForm = !forms.showCohortForm" class="btn-primary text-xs">+ Nueva</button></div>
          <div v-if="forms.showCohortForm && isAdmin" class="card p-4 space-y-3"><input v-model="forms.cohort.name" placeholder="Nombre" class="input" /><textarea v-model="forms.cohort.description" placeholder="Descripción" class="input" rows="2"></textarea><div class="grid grid-cols-2 gap-3"><input v-model="forms.cohort.start_date" type="date" class="input" /><input v-model="forms.cohort.end_date" type="date" class="input" /></div><button @click="saveCohort" class="btn-primary w-full">Crear</button></div>
          <div v-if="activeCohorts.length > 0"><p class="text-xs font-semibold text-parmenia-textMuted uppercase tracking-wide mb-2">Activas</p><div class="grid sm:grid-cols-2 gap-3"><div v-for="c in activeCohorts" :key="c.id" class="card p-4 hover:border-parmenia-primary cursor-pointer transition-colors" @click="viewCohort(c)"><div class="flex items-start justify-between mb-1"><h3 class="font-bold text-sm text-parmenia-text">{{ c.name }}</h3><span class="badge-success text-[10px]">Activa</span></div><p class="text-xs text-parmenia-textMuted line-clamp-2">{{ c.description || 'Sin descripción' }}</p></div></div></div>
          <div v-if="pastCohorts.length > 0" class="mt-4"><p class="text-xs font-semibold text-parmenia-textMuted uppercase tracking-wide mb-2">Anteriores</p><div class="space-y-1.5"><div v-for="c in pastCohorts" :key="c.id" class="card p-3 flex items-center justify-between cursor-pointer hover:border-parmenia-border" @click="viewCohort(c)"><div><h3 class="font-semibold text-sm text-parmenia-text">{{ c.name }}</h3><p class="text-xs text-parmenia-textDim">{{ fmtDate(c.start_date) }} - {{ fmtDate(c.end_date) }}</p></div><span class="badge-neutral text-[10px]">Finalizada</span></div></div></div>
        </template>

        <!-- ═══ CONVOCATORIA DETALLE ═══ -->
        <template v-if="activeKey === 'convocatorias' && data.showCohortDetail && !data.showProjectDetail">
          <button @click="data.showCohortDetail = false" class="text-sm text-parmenia-primary font-semibold hover:underline">← Volver</button>
          <div class="card p-5"><h1 class="text-lg font-bold text-parmenia-text mb-1">{{ data.selectedCohort?.name }}</h1><p class="text-sm text-parmenia-textMuted mb-2">{{ data.selectedCohort?.description }}</p><p class="text-xs text-parmenia-textDim">{{ fmtDate(data.selectedCohort?.start_date) }} → {{ fmtDate(data.selectedCohort?.end_date) || 'Sin fin' }}</p></div>
          <p class="text-sm font-bold text-parmenia-text">Proyectos ({{ data.projects.filter(p => p.cohort_id === data.selectedCohort?.id).length }})</p>
          <div v-if="data.projects.filter(p => p.cohort_id === data.selectedCohort?.id).length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin proyectos</div>
          <div v-else class="grid sm:grid-cols-2 gap-3"><div v-for="p in data.projects.filter(pr => pr.cohort_id === data.selectedCohort?.id)" :key="p.id" class="card p-4 hover:border-parmenia-primary cursor-pointer transition-colors" @click="viewProjectDetail(p)"><h3 class="font-bold text-sm text-parmenia-text">{{ p.name }}</h3><p class="text-xs text-parmenia-textMuted line-clamp-2 mt-1">{{ p.description || 'Sin descripción' }}</p></div></div>
        </template>

        <!-- ═══ PROYECTO DETALLE PÚBLICO ═══ -->
        <template v-if="activeKey === 'convocatorias' && data.showProjectDetail">
          <button @click="data.showProjectDetail = false; data.showCohortDetail = true" class="text-sm text-parmenia-primary font-semibold hover:underline">← Volver</button>
          <div v-if="data.projectDetail" class="card p-5"><h1 class="text-lg font-bold text-parmenia-text mb-2">{{ data.projectDetail.name }}</h1><p class="text-sm text-parmenia-textMuted mb-3">{{ data.projectDetail.description || 'Sin descripción' }}</p><div class="flex flex-wrap gap-2 mb-3"><span class="badge-primary text-[10px]">{{ data.projectDetail.current_phase_name || 'Sin fase' }}</span><span class="badge-neutral text-[10px]">{{ data.projectDetail.cohort_name || '' }}</span><span class="badge-neutral text-[10px]">{{ data.projectDetail.member_count }} integrantes</span><span class="badge-neutral text-[10px]">{{ data.projectDetail.mentor_count }} mentores</span></div><div class="mb-2"><div class="flex items-center justify-between mb-1"><span class="text-xs font-semibold text-parmenia-textMuted">Progreso</span><span class="text-xs font-bold text-parmenia-primary">{{ data.projectDetail.progress_percentage }}%</span></div><div class="w-full h-2 bg-parmenia-bg rounded-full"><div class="h-full bg-parmenia-primary rounded-full" :style="{ width: data.projectDetail.progress_percentage + '%' }"></div></div></div><p class="text-xs text-parmenia-textDim mt-2">Líder: {{ data.projectDetail.leader_name || 'N/A' }}</p></div>
        </template>

        <!-- ═══ INSCRIPCIÓN ═══ -->
        <template v-if="activeKey === 'inscripcion'">
          <h1 class="text-lg font-bold text-parmenia-text">Inscripción</h1>
          <div v-if="data.myEnrollments.length > 0" class="card p-4"><p class="text-sm font-bold text-parmenia-text mb-2">Mis Inscripciones</p><div class="space-y-1.5"><div v-for="e in data.myEnrollments" :key="e.id" class="flex items-center justify-between p-2.5 bg-parmenia-bg rounded-md"><div><p class="text-sm font-medium text-parmenia-text">{{ data.cohorts.find(c => c.id === e.cohort_id)?.name || 'N/A' }}</p><p class="text-xs text-parmenia-textDim">{{ fmtDate(e.enrollment_date) }}</p></div><span :class="e.status === 'aceptada' ? 'badge-success' : e.status === 'rechazada' ? 'badge-danger' : 'badge-warning'" class="text-[10px]">{{ e.status }}</span></div></div></div>
          <p class="text-sm font-bold text-parmenia-text">Disponibles</p>
          <div v-if="activeCohorts.length === 0" class="card p-6 text-center text-parmenia-textMuted text-sm">Sin convocatorias abiertas</div>
          <div v-else class="space-y-2"><div v-for="c in activeCohorts" :key="c.id" class="card p-4 flex items-start justify-between gap-3"><div class="flex-1"><h3 class="font-bold text-sm text-parmenia-text">{{ c.name }}</h3><p class="text-xs text-parmenia-textMuted mt-0.5">{{ c.description || 'Sin descripción' }}</p></div><button v-if="isEnrolled(c.id)" disabled class="btn-secondary text-xs opacity-60">✓ Inscrito</button><button v-else @click="enroll(c.id)" class="btn-primary text-xs">Inscribirse</button></div></div>
        </template>

        <!-- ═══ MI PROYECTO ═══ -->
        <template v-if="activeKey === 'mi-proyecto'">
          <h1 class="text-lg font-bold text-parmenia-text">Mi Proyecto</h1>
          <div v-if="!data.myProject" class="card p-8 text-center"><p class="text-sm text-parmenia-textMuted mb-3">Sin proyecto activo</p><button @click="handleNavClick('inscripcion')" class="btn-primary text-xs">Inscribirse</button></div>
          <template v-else>
            <div class="card p-4"><div class="flex items-start justify-between mb-2"><div class="flex-1"><h2 class="text-base font-bold text-parmenia-text">{{ data.myProject.name }}</h2><p class="text-sm text-parmenia-textMuted">{{ data.myProject.description || 'Sin descripción' }}</p></div><button v-if="data.myProject.leader_id === user.id" @click="forms.showProjectEdit = !forms.showProjectEdit; forms.project = { name: data.myProject.name, description: data.myProject.description || '' }" class="btn-secondary text-xs">Editar</button></div><div class="flex gap-2 mt-2"><span v-if="data.myProject.current_phase_id" class="badge-primary text-[10px]">{{ phaseName(data.myProject.current_phase_id) }}</span><span class="badge-neutral text-[10px]">{{ data.members.length }} integrantes</span><span class="badge-neutral text-[10px]">{{ data.mentors.length }} mentores</span></div></div>
            <div v-if="forms.showProjectEdit" class="card p-4 space-y-3"><input v-model="forms.project.name" class="input" /><textarea v-model="forms.project.description" class="input" rows="2"></textarea><button @click="saveProject" class="btn-primary w-full">Guardar</button></div>
            <!-- Integrantes con búsqueda mejorada -->
            <div class="card p-4">
              <div class="flex items-center justify-between mb-2"><p class="text-sm font-bold text-parmenia-text">Integrantes</p><button v-if="data.myProject.leader_id === user.id" @click="forms.showAddMember = !forms.showAddMember; forms.newMemberSearch=''; forms.searchResults=[]" class="btn-secondary text-xs">+ Agregar</button></div>
              <div v-if="forms.showAddMember" class="space-y-2 mb-2">
                <input v-model="forms.newMemberSearch" @input="searchMembers" placeholder="Buscar por nombre o correo..." class="input" />
                <p v-if="forms.searchingMembers" class="text-xs text-parmenia-textDim">Buscando...</p>
                <div v-if="forms.searchResults.length > 0" class="space-y-1 max-h-48 overflow-y-auto">
                  <button v-for="r in forms.searchResults" :key="r.id" @click="addMember(r.id)" class="w-full flex items-center gap-2 p-2 bg-parmenia-bg rounded-md hover:bg-parmenia-primarySoft transition-colors text-left">
                    <div class="w-6 h-6 rounded-full bg-parmenia-primarySoft flex items-center justify-center text-[10px] font-bold text-parmenia-primary">{{ (r.full_name || r.email || '?').charAt(0).toUpperCase() }}</div>
                    <div class="flex-1 min-w-0"><p class="text-xs font-medium text-parmenia-text truncate">{{ r.full_name || 'Sin nombre' }}</p><p class="text-[10px] text-parmenia-textDim truncate">{{ r.email }}</p></div>
                    <span class="text-[10px] text-parmenia-primary font-semibold">+ Agregar</span>
                  </button>
                </div>
                <p v-else-if="forms.newMemberSearch.length > 2 && !forms.searchingMembers" class="text-xs text-parmenia-textDim text-center py-2">Sin resultados</p>
              </div>
              <div v-if="data.members.length === 0" class="text-sm text-parmenia-textDim text-center py-2">Sin integrantes</div>
              <div v-else class="space-y-1.5">
                <div v-for="m in data.members" :key="m.user_id" class="flex items-center justify-between p-2 bg-parmenia-bg rounded-md">
                  <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-full bg-parmenia-primarySoft flex items-center justify-center text-[10px] font-bold text-parmenia-primary">{{ (m.full_name || m.email || '?').charAt(0).toUpperCase() }}</div>
                    <div><p class="text-sm text-parmenia-text">{{ m.full_name || 'Sin nombre' }}</p><p class="text-[10px] text-parmenia-textDim">{{ m.email }}</p></div>
                  </div>
                  <span v-if="m.user_id === data.myProject.leader_id" class="badge-primary text-[10px]">Líder</span>
                  <button v-else-if="data.myProject.leader_id === user.id" @click="removeMember(m.user_id)" class="text-xs text-parmenia-danger hover:underline">Remover</button>
                </div>
              </div>
            </div>
            <!-- Mentores -->
            <div class="card p-4"><p class="text-sm font-bold text-parmenia-text mb-2">Mentores Asignados</p><div v-if="data.mentors.length === 0" class="text-sm text-parmenia-textDim text-center py-2">Sin mentores asignados</div><div v-else class="space-y-1.5"><div v-for="men in data.mentors" :key="men.mentor_id" class="flex items-center gap-2 p-2 bg-parmenia-bg rounded-md"><div class="w-6 h-6 rounded-full bg-parmenia-warningSoft flex items-center justify-center text-[10px] font-bold text-parmenia-warning">{{ (men.full_name || men.email || 'M').charAt(0).toUpperCase() }}</div><div><p class="text-sm text-parmenia-text">{{ men.full_name || 'Mentor' }}</p><p class="text-[10px] text-parmenia-textDim">{{ men.email }}</p></div></div></div></div>
          </template>
        </template>

        <!-- ═══ ENTREGABLES ═══ -->
        <template v-if="activeKey === 'entregables'">
          <div class="flex items-center justify-between"><h1 class="text-lg font-bold text-parmenia-text">Entregables</h1><button v-if="data.myProject" @click="forms.showDeliverableForm = !forms.showDeliverableForm" class="btn-primary text-xs">+ Subir</button></div>
          <div v-if="!data.myProject" class="card p-8 text-center text-parmenia-textMuted text-sm">Sin proyecto activo</div>
          <div v-else-if="data.deliverables.length === 0" class="card p-8 text-center text-parmenia-textMuted text-sm">Sin entregables</div>
          <div v-if="forms.showDeliverableForm && data.myProject" class="card p-4 space-y-3"><select v-model="forms.deliverable.phase_id" class="input"><option value="">Seleccionar fase...</option><option v-for="p in data.phases" :key="p.id" :value="p.id">{{ p.name }}</option></select><div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Archivo</label><input type="file" @change="handleFileUpload" :disabled="forms.uploadingFile" class="input" /><p v-if="forms.uploadingFile" class="text-xs text-parmenia-primary mt-1">Subiendo...</p><p v-if="forms.deliverable.file_url && !forms.uploadingFile" class="text-xs text-parmenia-success mt-1">✓ Archivo subido</p></div><button @click="uploadDeliverable" :disabled="!forms.deliverable.file_url || !forms.deliverable.phase_id" class="btn-primary w-full">Subir entregable</button></div>
          <div v-if="data.myProject && data.deliverables.length > 0" class="space-y-3">
            <div v-for="d in data.deliverables" :key="d.id" class="card p-4">
              <div class="flex items-start justify-between mb-2"><div><h3 class="text-sm font-bold text-parmenia-text">{{ phaseName(d.phase_id) }}</h3><a :href="d.file_url" target="_blank" class="text-xs text-parmenia-accent hover:underline break-all">{{ d.file_url }}</a><p class="text-[10px] text-parmenia-textDim mt-0.5">{{ fmtDate(d.created_at) }}</p></div></div>
              <div class="border-t border-parmenia-border pt-2 mt-2"><div class="flex items-center justify-between mb-1"><p class="text-xs font-semibold text-parmenia-textMuted uppercase">Revisiones</p><button v-if="isMentor || isAdmin" @click="forms.showReviewForm[d.id] = !forms.showReviewForm[d.id]" class="text-xs text-parmenia-primary font-semibold">+ Revisar</button></div><div v-if="forms.showReviewForm[d.id] && (isMentor || isAdmin)" class="bg-parmenia-bg rounded-md p-3 space-y-2 mb-2"><select v-model="(forms.review[d.id] ||= {}).status" class="input"><option value="aprobado">Aprobado</option><option value="rechazado">Rechazado</option></select><textarea v-model="(forms.review[d.id] ||= {}).feedback" placeholder="Feedback..." class="input" rows="2"></textarea><button @click="submitReview(d.id)" class="btn-primary text-xs w-full">Enviar</button></div><div v-if="!data.reviews[d.id] || data.reviews[d.id].length === 0" class="text-xs text-parmenia-textDim">Sin revisiones</div><div v-else class="space-y-1.5"><div v-for="r in data.reviews[d.id]" :key="r.id" class="flex items-start gap-2 p-2 bg-parmenia-bg rounded-md"><span :class="r.status === 'aprobado' ? 'badge-success' : 'badge-danger'" class="flex-shrink-0 text-[10px]">{{ r.status }}</span><div class="flex-1"><p class="text-xs text-parmenia-text">{{ r.feedback || 'Sin comentarios' }}</p></div></div></div></div>
              <div class="border-t border-parmenia-border pt-2 mt-2"><p class="text-xs font-semibold text-parmenia-textMuted uppercase mb-2">Comentarios</p><div v-if="data.comments[d.id] && data.comments[d.id].length > 0" class="space-y-1.5 mb-2 max-h-40 overflow-y-auto"><div v-for="c in data.comments[d.id]" :key="c.id" class="flex items-start gap-2 p-2 bg-parmenia-bg rounded-md"><div class="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold flex-shrink-0" :class="c.author_role === 'mentor' ? 'bg-parmenia-warningSoft text-parmenia-warning' : 'bg-parmenia-primarySoft text-parmenia-primary'">{{ (c.author_name || '?').charAt(0).toUpperCase() }}</div><div class="flex-1 min-w-0"><p class="text-xs text-parmenia-text">{{ c.content }}</p><p class="text-[10px] text-parmenia-textDim">{{ c.author_name }} · {{ fmtDateTime(c.created_at) }}</p></div></div></div><div class="flex gap-2"><input :value="forms.comment[d.id] || ''" @input="forms.comment[d.id] = $event.target.value" placeholder="Escribir comentario..." class="input flex-1 text-xs" @keydown.enter="submitComment(d.id)" /><button @click="submitComment(d.id)" class="btn-primary text-xs px-3">Enviar</button></div></div>
            </div>
          </div>
        </template>

        <!-- ═══ MENTOR (rediseñado) ═══ -->
        <template v-if="activeKey === 'mentor' && isMentor">
          <h1 class="text-lg font-bold text-parmenia-text">Panel de Mentor</h1>

          <!-- Proyectos asignados -->
          <div class="card p-4">
            <p class="text-sm font-bold text-parmenia-text mb-3">Proyectos Asignados ({{ data.mentorProjects.length }})</p>
            <div v-if="data.mentorProjects.length === 0" class="text-sm text-parmenia-textDim text-center py-4">No tienes proyectos asignados. Pide al administrador que te asigne.</div>
            <div v-else class="space-y-3">
              <div v-for="p in data.mentorProjects" :key="p.id" class="bg-parmenia-bg rounded-md p-3">
                <div class="flex items-start justify-between mb-2">
                  <div><h3 class="text-sm font-bold text-parmenia-text">{{ p.name }}</h3><p class="text-xs text-parmenia-textMuted">{{ p.description || 'Sin descripción' }}</p></div>
                  <span v-if="p.current_phase_id" class="badge-primary text-[10px]">{{ phaseName(p.current_phase_id) }}</span>
                </div>
                <p class="text-xs font-semibold text-parmenia-textMuted uppercase mb-1">Entregables por revisar ({{ p._pendingReviews?.length || 0 }})</p>
                <div v-if="!p._pendingReviews || p._pendingReviews.length === 0" class="text-xs text-parmenia-textDim">Sin entregables pendientes</div>
                <div v-else class="space-y-2">
                  <div v-for="d in p._pendingReviews" :key="d.id" class="bg-white rounded-md p-2 border border-parmenia-border">
                    <div class="flex items-start justify-between mb-1"><div><p class="text-xs font-medium text-parmenia-text">{{ phaseName(d.phase_id) }}</p><a :href="d.file_url" target="_blank" class="text-[10px] text-parmenia-accent hover:underline break-all">{{ d.file_url?.substring(0, 40) }}...</a></div><button @click="forms.showReviewForm[d.id] = !forms.showReviewForm[d.id]" class="text-xs text-parmenia-primary font-semibold">+ Revisar</button></div>
                    <div v-if="forms.showReviewForm[d.id]" class="mt-2 space-y-2"><select v-model="(forms.review[d.id] ||= {}).status" class="input"><option value="aprobado">Aprobado</option><option value="rechazado">Rechazado</option></select><textarea v-model="(forms.review[d.id] ||= {}).feedback" placeholder="Feedback..." class="input" rows="2"></textarea><button @click="submitMentorReview(d.id, p.id)" class="btn-primary text-xs w-full">Enviar revisión</button></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Mentorías agendadas -->
          <div class="card p-4">
            <p class="text-sm font-bold text-parmenia-text mb-3">Mentorías Agendadas ({{ data.mentorships.length }})</p>
            <div v-if="data.mentorships.length === 0" class="text-sm text-parmenia-textDim text-center py-2">Sin mentorías agendadas</div>
            <div v-else class="space-y-2">
              <div v-for="m in data.mentorships" :key="m.id" class="flex items-center justify-between p-2.5 bg-parmenia-bg rounded-md">
                <div><p class="text-sm font-medium text-parmenia-text">{{ m.title }}</p><p class="text-xs text-parmenia-textDim">{{ fmtDateTime(m.start_datetime) }}</p></div>
                <div class="flex gap-2"><a v-if="m.google_meet_link" :href="m.google_meet_link" target="_blank" class="btn-secondary text-xs">Meet</a><a v-if="m.google_html_link" :href="m.google_html_link" target="_blank" class="btn-secondary text-xs">Calendar</a></div>
              </div>
            </div>
          </div>

          <!-- Agendar mentoría -->
          <div class="card p-4 space-y-3">
            <div class="flex items-center justify-between"><p class="text-sm font-bold text-parmenia-text">Agendar Nueva Mentoría</p><button @click="forms.showMentorshipForm = !forms.showMentorshipForm" class="btn-primary text-xs">{{ forms.showMentorshipForm ? 'Cancelar' : '+ Agendar' }}</button></div>
            <div v-if="forms.showMentorshipForm" class="space-y-3">
              <input v-model="forms.mentorship.title" placeholder="Título" class="input" />
              <textarea v-model="forms.mentorship.description" placeholder="Descripción" class="input" rows="2"></textarea>
              <div class="grid grid-cols-2 gap-3"><input v-model="forms.mentorship.start_datetime" type="datetime-local" class="input" /><input v-model="forms.mentorship.end_datetime" type="datetime-local" class="input" /></div>
              <input v-model="forms.mentorship.attendee_emails" placeholder="Emails de invitados (separados por comas)" class="input" />
              <label class="flex items-center gap-2 text-sm text-parmenia-textMuted"><input type="checkbox" v-model="forms.mentorship.create_meet" class="w-4 h-4" /> Crear Google Meet</label>
              <button @click="scheduleMentorship" :disabled="forms.schedulingMentorship" class="btn-primary w-full">{{ forms.schedulingMentorship ? '⏳ Autorizando...' : 'Autorizar y Agendar' }}</button>
            </div>
            <div v-if="forms.mentorshipResult" class="bg-parmenia-successSoft rounded-md p-3"><p class="text-sm font-bold text-parmenia-success">✓ Mentoría agendada correctamente</p><div class="mt-2 space-y-1"><a v-if="forms.mentorshipResult.google_html_link" :href="forms.mentorshipResult.google_html_link" target="_blank" class="text-xs text-parmenia-accent hover:underline block">Ver en Google Calendar</a><a v-if="forms.mentorshipResult.google_meet_link" :href="forms.mentorshipResult.google_meet_link" target="_blank" class="text-xs text-parmenia-accent hover:underline block">Unirse a Google Meet</a></div></div>
          </div>
        </template>

        <!-- ═══ ADMIN ═══ -->
        <template v-if="activeKey === 'admin' && isAdmin">
          <h1 class="text-lg font-bold text-parmenia-text">Administración</h1>
          <div class="card p-4"><p class="text-sm font-bold text-parmenia-text mb-2">Inscripciones Pendientes</p><div v-if="data.enrollments.filter(e => e.status === 'pendiente').length === 0" class="text-sm text-parmenia-textDim">Sin pendientes</div><div v-else class="space-y-1.5"><div v-for="e in data.enrollments.filter(en => en.status === 'pendiente')" :key="e.id" class="flex items-center justify-between p-2.5 bg-parmenia-bg rounded-md"><div><p class="text-sm font-medium text-parmenia-text">{{ data.cohorts.find(c => c.id === e.cohort_id)?.name || 'N/A' }}</p><p class="text-xs text-parmenia-textDim">{{ fmtDate(e.enrollment_date) }}</p></div><div class="flex gap-3"><button @click="updateEnrollmentStatus(e.id, 'aceptada')" class="text-xs text-parmenia-success font-bold hover:underline">✓ Aceptar</button><button @click="updateEnrollmentStatus(e.id, 'rechazada')" class="text-xs text-parmenia-danger font-bold hover:underline">✗ Rechazar</button></div></div></div></div>
          <div class="card p-4 space-y-3"><p class="text-sm font-bold text-parmenia-text">Cambiar Fase de Proyecto</p><select v-model="forms.adminPhaseChange.project_id" class="input"><option value="">Seleccionar proyecto...</option><option v-for="p in data.projects" :key="p.id" :value="p.id">{{ p.name }}</option></select><select v-if="forms.adminPhaseChange.project_id" v-model="forms.adminPhaseChange.phase_id" class="input"><option value="">Seleccionar fase...</option><option v-for="ph in data.phases" :key="ph.id" :value="ph.id">{{ ph.name }}</option></select><button @click="adminChangePhase" :disabled="!forms.adminPhaseChange.project_id || !forms.adminPhaseChange.phase_id" class="btn-primary w-full text-xs">Cambiar fase</button></div>
          <div v-if="data.dashboardStats" class="grid grid-cols-2 sm:grid-cols-3 gap-3"><div class="card p-4"><p class="text-xl font-bold text-parmenia-primary">{{ data.dashboardStats.users_by_role?.total || 0 }}</p><p class="text-xs text-parmenia-textMuted">Usuarios</p></div><div class="card p-4"><p class="text-xl font-bold text-parmenia-primary">{{ data.dashboardStats.projects_by_phase?.total || 0 }}</p><p class="text-xs text-parmenia-textMuted">Proyectos</p></div><div class="card p-4"><p class="text-xl font-bold text-parmenia-primary">{{ data.dashboardStats.deliverables_reviewed || 0 }}</p><p class="text-xs text-parmenia-textMuted">Revisados</p></div></div>
        </template>

        <!-- ═══ PERFIL ═══ -->
        <template v-if="activeKey === 'perfil'">
          <h1 class="text-lg font-bold text-parmenia-text">Mi Perfil</h1>
          <div class="card p-4 flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-parmenia-primary flex items-center justify-center text-white font-bold text-lg">{{ (user?.full_name || user?.email || '?').charAt(0).toUpperCase() }}</div><div><p class="font-bold text-parmenia-text">{{ user?.full_name || 'Sin nombre' }}</p><p class="text-sm text-parmenia-textMuted">{{ user?.email }}</p><span class="badge-primary mt-0.5 text-[10px]">{{ roleLabel }}</span></div></div>
          <div v-if="forms.profileLoaded" class="card p-4 space-y-3"><div v-if="notice" class="bg-parmenia-successSoft text-parmenia-success rounded-md px-3 py-2 text-sm">{{ notice }}</div><div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Nombre</label><input v-model="forms.profile.full_name" class="input" /></div><div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Facultad</label><input v-model="forms.profile.faculty" class="input" /></div><div><label class="block text-xs font-medium text-parmenia-textMuted mb-1">Habilidades (comas)</label><input v-model="forms.profile.skills" class="input" /></div><button @click="saveProfile" class="btn-primary w-full">Guardar</button></div>
        </template>

      </div>
    </main>
  </div>
</template>
