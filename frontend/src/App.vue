<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { apiRequest, authApi, clearSession, getStoredUser, setSession } from './api'
import { resources } from './resources'

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

const user = ref(getStoredUser())
const token = ref(localStorage.getItem('parmenia_token') || '')
const activeKey = ref('dashboard')
const loading = ref(false)
const notice = ref('')
const error = ref('')
const loginForm = reactive({ email: 'admin@parmenia.pe', password: 'admin123' })
const registerForm = reactive({
  email: '',
  password: '123456',
  full_name: '',
  faculty: '',
  skills: '',
  role: 'emprendedor',
})
const publicRegisterRoles = ['emprendedor', 'mentor']

const resourceState = reactive({})
const reports = reactive({
  health: null,
  dashboard: null,
  cohortId: '',
  cohortProgress: null,
})

const activeResource = computed(() => resources.find((item) => item.key === activeKey.value))
const isAuthenticated = computed(() => Boolean(token.value && user.value))
const isAdmin = computed(() => user.value?.role === 'admin')
const isMentor = computed(() => user.value?.role === 'mentor')
const visibleResources = computed(() => resources.filter((resource) => canAccessResource(resource, 'view')))

function canAccessResource(resource, action) {
  if (!user.value) return false
  if (isAdmin.value) return true

  const permissions = {
    emprendedor: {
      profiles: ['view', 'list', 'get', 'update'],
      phases: ['view', 'list', 'get'],
      cohorts: ['view', 'list', 'get'],
      enrollments: ['view', 'list', 'get', 'create'],
      projects: ['view', 'list', 'get', 'create', 'update'],
      posts: ['view', 'list', 'get'],
      deliverables: ['view', 'get', 'update', 'delete'],
      reviews: ['view', 'get'],
    },
    mentor: {
      profiles: ['view', 'list', 'get', 'update'],
      phases: ['view', 'list', 'get'],
      cohorts: ['view', 'list', 'get'],
      enrollments: ['view', 'list', 'get'],
      projects: ['view', 'list', 'get'],
      posts: ['view', 'list', 'get', 'create', 'update', 'delete'],
      deliverables: ['view', 'get'],
      reviews: ['view', 'get', 'create', 'update'],
    },
  }

  return permissions[user.value.role]?.[resource.key]?.includes(action) || false
}

function canRunAction(action) {
  if (!user.value) return false
  if (isAdmin.value) return true

  const permissions = {
    emprendedor: [
      'members-list',
      'members-add',
      'members-remove',
      'mentors-list',
      'deliverables-list',
      'deliverables-add',
      'reviews-list',
    ],
    mentor: ['members-list', 'mentors-list', 'deliverables-list', 'reviews-list', 'reviews-add'],
  }

  return permissions[user.value.role]?.includes(action.key) || false
}

function setMessage(message, type = 'notice') {
  notice.value = type === 'notice' ? message : ''
  error.value = type === 'error' ? message : ''
}

function normalizeList(value) {
  if (!value) return []
  if (Array.isArray(value)) return value
  return String(value)
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function cleanBody(raw, fields) {
  const body = {}
  fields.forEach((field) => {
    let value = raw[field.name]
    if (field.type === 'list') value = normalizeList(value)
    if (field.type === 'number' && value !== '' && value !== null && value !== undefined) value = Number(value)
    if (field.type === 'checkbox') value = Boolean(value)
    if (value !== '' && value !== null && value !== undefined) body[field.name] = value
  })
  return body
}

function initialForm(fields = []) {
  return fields.reduce((acc, field) => {
    if (field.type === 'checkbox') acc[field.name] = field.default ?? false
    else acc[field.name] = field.default ?? ''
    return acc
  }, {})
}

function stateFor(resource) {
  if (!resourceState[resource.key]) {
    resourceState[resource.key] = {
      items: [],
      selectedId: '',
      form: initialForm(resource.createFields),
      updateId: '',
      updateForm: initialForm(resource.updateFields),
      actionForms: {},
      actionResult: null,
    }
  }
  return resourceState[resource.key]
}

async function safeRun(fn, success) {
  loading.value = true
  setMessage('')
  try {
    const result = await fn()
    if (success) setMessage(success)
    return result
  } catch (err) {
    setMessage(err.message || 'Ocurrio un error', 'error')
    return null
  } finally {
    loading.value = false
  }
}

function applyAuth(auth) {
  setSession(auth)
  token.value = auth.access_token
  user.value = auth.user
  activeKey.value = 'dashboard'
}

async function login() {
  const auth = await safeRun(() => authApi.login(loginForm), 'Sesion iniciada')
  if (auth) applyAuth(auth)
}

async function register() {
  const body = {
    ...registerForm,
    skills: normalizeList(registerForm.skills),
  }
  const auth = await safeRun(() => authApi.register(body), 'Registro creado')
  if (auth) applyAuth(auth)
}

async function googleLogin(credential) {
  const auth = await safeRun(() => authApi.google(credential), 'Sesion iniciada con Google')
  if (auth) applyAuth(auth)
}

function logout() {
  clearSession()
  token.value = ''
  user.value = null
  activeKey.value = 'dashboard'
  setMessage('Sesion cerrada')
}

async function refreshMe() {
  const current = await safeRun(() => authApi.me())
  if (current) {
    user.value = current
    localStorage.setItem('parmenia_user', JSON.stringify(current))
  }
}

async function listResource(resource) {
  const state = stateFor(resource)
  const data = await safeRun(() => apiRequest(resource.basePath), `${resource.title}: datos cargados`)
  if (Array.isArray(data)) state.items = data
}

async function getResource(resource) {
  const state = stateFor(resource)
  if (!state.selectedId) return setMessage('Ingresa un ID', 'error')
  const item = await safeRun(() => apiRequest(`${resource.basePath}${state.selectedId}`))
  if (item) state.actionResult = item
}

async function createResource(resource) {
  const state = stateFor(resource)
  const body = cleanBody(state.form, resource.createFields || [])
  const item = await safeRun(() => apiRequest(resource.basePath, { method: 'POST', body }), `${resource.title}: creado`)
  if (item) {
    state.form = initialForm(resource.createFields)
    await listResource(resource)
  }
}

async function updateResource(resource) {
  const state = stateFor(resource)
  if (!state.updateId) return setMessage('Ingresa el ID a actualizar', 'error')
  const body = cleanBody(state.updateForm, resource.updateFields || [])
  const item = await safeRun(
    () => apiRequest(`${resource.basePath}${state.updateId}`, { method: 'PUT', body }),
    `${resource.title}: actualizado`,
  )
  if (item) await listResource(resource)
}

async function deleteResource(resource, id) {
  const targetId = id || stateFor(resource).selectedId
  if (!targetId) return setMessage('Ingresa o selecciona un ID', 'error')
  const deleted = await safeRun(
    () => apiRequest(`${resource.basePath}${targetId}`, { method: 'DELETE' }),
    `${resource.title}: eliminado`,
  )
  if (deleted !== null) await listResource(resource)
}

async function runAction(resource, action, item) {
  const state = stateFor(resource)
  const key = `${action.key}:${item?.[resource.idField] || 'global'}`
  const form = state.actionForms[key] || {}
  const body = action.fields ? cleanBody(form, action.fields) : undefined
  const data = await safeRun(() =>
    apiRequest(action.path(item, body || form), {
      method: action.method,
      body: body && Object.keys(body).length ? body : undefined,
    }),
  )
  if (data !== null) state.actionResult = data
}

function actionForm(resource, action, item) {
  const state = stateFor(resource)
  const key = `${action.key}:${item?.[resource.idField] || 'global'}`
  if (!state.actionForms[key]) state.actionForms[key] = initialForm(action.fields)
  return state.actionForms[key]
}

async function loadDashboardReport() {
  reports.dashboard = await safeRun(() => apiRequest('/reports/dashboard'))
}

async function loadHealth() {
  reports.health = await safeRun(() => apiRequest('/health'))
}

async function loadCohortReport() {
  if (!reports.cohortId) return setMessage('Ingresa el ID de cohorte', 'error')
  reports.cohortProgress = await safeRun(() => apiRequest(`/reports/cohort/${reports.cohortId}/progress`))
}

function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([key, nestedValue]) => `${formatLabel(key)}: ${formatValue(nestedValue)}`)
      .join(' | ')
  }
  return String(value)
}

function formatLabel(key) {
  const labels = {
    id: 'ID',
    email: 'Email',
    full_name: 'Nombre',
    faculty: 'Facultad',
    skills: 'Habilidades',
    role: 'Rol',
    created_at: 'Creado',
    name: 'Nombre',
    title: 'Titulo',
    content: 'Contenido',
    description: 'Descripcion',
    start_date: 'Inicio',
    end_date: 'Fin',
    order: 'Orden',
    status: 'Estado',
    user_id: 'Usuario',
    cohort_id: 'Convocatoria',
    enrollment_date: 'Fecha',
    leader_id: 'Lider',
    current_phase_id: 'Fase actual',
    phase_id: 'Fase',
    project_id: 'Proyecto',
    mentor_id: 'Mentor',
    uploaded_by: 'Subido por',
    file_url: 'Archivo',
    feedback: 'Feedback',
    reviewed_at: 'Revisado',
    is_published: 'Publicado',
    published_at: 'Publicado en',
    access_token: 'Token',
    token_type: 'Tipo',
    message: 'Mensaje',
  }

  return labels[key] || key.replaceAll('_', ' ')
}

function importantFields(resource, item) {
  const fieldsByResource = {
    profiles: ['full_name', 'email', 'role', 'faculty', 'skills'],
    phases: ['name', 'order'],
    cohorts: ['name', 'description', 'start_date', 'end_date'],
    enrollments: ['status', 'cohort_id', 'user_id', 'enrollment_date'],
    projects: ['name', 'description', 'cohort_id', 'leader_id', 'current_phase_id'],
    posts: ['title', 'content', 'is_published', 'published_at'],
    deliverables: ['file_url', 'project_id', 'phase_id', 'uploaded_by', 'created_at'],
    reviews: ['status', 'feedback', 'mentor_id', 'reviewed_at'],
  }

  const fields = fieldsByResource[resource?.key] || Object.keys(item || {})
  return fields
    .filter((field) => item?.[field] !== undefined && item?.[field] !== null && item?.[field] !== '')
    .map((field) => ({ label: formatLabel(field), value: formatValue(item[field]) }))
}

function summaryTitle(item) {
  return item?.full_name || item?.name || item?.title || item?.email || item?.status || item?.file_url || 'Registro'
}

function summarySubtitle(resource, item) {
  const role = item?.role ? `Rol: ${item.role}` : ''
  const status = item?.status ? `Estado: ${item.status}` : ''
  const id = item?.[resource?.idField] ? `ID: ${item[resource.idField]}` : ''
  return [role, status, id].filter(Boolean).join(' · ')
}

function renderGoogleButton() {
  if (!googleClientId || !window.google || isAuthenticated.value) return
  window.google.accounts.id.initialize({
    client_id: googleClientId,
    callback: (response) => googleLogin(response.credential),
  })
  window.google.accounts.id.renderButton(document.getElementById('googleButton'), {
    theme: 'outline',
    size: 'large',
    text: 'signin_with',
    shape: 'rectangular',
  })
}

onMounted(async () => {
  await nextTick()
  renderGoogleButton()
})
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="mark">P</span>
        <div>
          <strong>Parmenia</strong>
          <small>Pre-incubacion</small>
        </div>
      </div>

      <nav v-if="isAuthenticated">
        <button :class="{ active: activeKey === 'dashboard' }" @click="activeKey = 'dashboard'">Dashboard</button>
        <button v-for="resource in visibleResources" :key="resource.key" :class="{ active: activeKey === resource.key }" @click="activeKey = resource.key">
          {{ resource.title }}
        </button>
      </nav>
    </aside>

    <main>
      <header class="topbar">
        <div>
          <h1>{{ activeResource?.title || 'Dashboard' }}</h1>
          <p v-if="user">Sesion: {{ user.full_name || user.email }} · {{ user.role }}</p>
          <p v-else>Frontend Vue consumiendo la API FastAPI y OAuth2 con Google.</p>
        </div>
        <button v-if="isAuthenticated" class="ghost" @click="logout">Cerrar sesion</button>
      </header>

      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="loading">Procesando...</p>

      <section v-if="!isAuthenticated" class="auth-grid">
        <form class="panel" @submit.prevent="login">
          <h2>Login tradicional</h2>
          <label>Email<input v-model="loginForm.email" type="email" required /></label>
          <label>Password<input v-model="loginForm.password" type="password" required /></label>
          <button type="submit">Ingresar</button>
          <small>Prueba: admin@parmenia.pe / admin123</small>
        </form>

        <form class="panel" @submit.prevent="register">
          <h2>Registro</h2>
          <label>Email<input v-model="registerForm.email" type="email" required /></label>
          <label>Password<input v-model="registerForm.password" type="password" required /></label>
          <label>Nombre<input v-model="registerForm.full_name" /></label>
          <label>Facultad<input v-model="registerForm.faculty" /></label>
          <label>Habilidades<input v-model="registerForm.skills" placeholder="Python, Vue, UX" /></label>
          <label>Rol
            <select v-model="registerForm.role">
              <option v-for="role in publicRegisterRoles" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>
          <button type="submit">Crear cuenta</button>
        </form>

        <div class="panel">
          <h2>OAuth2 con Google</h2>
          <p>Usa Google Identity para validar el usuario y obtener un JWT local de la API.</p>
          <div id="googleButton" class="google-slot"></div>
          <p v-if="!googleClientId" class="error">Configura VITE_GOOGLE_CLIENT_ID en frontend/.env</p>
        </div>
      </section>

      <section v-else-if="activeKey === 'dashboard'" class="grid">
        <article class="panel">
          <h2>Mi perfil</h2>
          <button @click="refreshMe">Actualizar /auth/me</button>
          <dl class="detail-list">
            <template v-for="entry in importantFields({ key: 'profiles' }, user)" :key="entry.label">
              <dt>{{ entry.label }}</dt>
              <dd>{{ entry.value }}</dd>
            </template>
          </dl>
        </article>

        <article class="panel">
          <h2>Salud API</h2>
          <button @click="loadHealth">GET /health</button>
          <p v-if="reports.health" class="status-pill">API activa</p>
          <p v-else class="muted">Aun no se consulto el estado.</p>
        </article>

        <article v-if="isAdmin" class="panel">
          <h2>Reporte admin</h2>
          <button @click="loadDashboardReport">GET /reports/dashboard</button>
          <div v-if="reports.dashboard" class="metric-grid">
            <div class="metric">
              <span>Usuarios</span>
              <strong>{{ reports.dashboard.total_users }}</strong>
            </div>
            <div class="metric">
              <span>Inscripciones</span>
              <strong>{{ reports.dashboard.total_enrollments }}</strong>
            </div>
            <div class="metric">
              <span>Proyectos</span>
              <strong>{{ reports.dashboard.total_projects }}</strong>
            </div>
            <div class="metric">
              <span>Entregables pendientes</span>
              <strong>{{ reports.dashboard.pending_deliverables }}</strong>
            </div>
          </div>
          <p v-else class="muted">Carga el reporte para ver los indicadores.</p>
        </article>

        <article v-if="isAdmin || isMentor" class="panel wide">
          <h2>Reporte por cohorte</h2>
          <div class="inline">
            <input v-model="reports.cohortId" placeholder="ID de cohorte" />
            <button @click="loadCohortReport">GET /reports/cohort/{id}/progress</button>
          </div>
          <div v-if="reports.cohortProgress">
            <h3>{{ reports.cohortProgress.cohort_name }}</h3>
            <p class="muted">Total de proyectos: {{ reports.cohortProgress.total_projects }}</p>
            <div class="cards">
              <article v-for="project in reports.cohortProgress.projects" :key="project.project_id" class="record-card">
                <h3>{{ project.project_name }}</h3>
                <p>{{ project.current_phase }} · {{ project.progress_percentage }}%</p>
                <dl class="detail-list compact">
                  <dt>Lider</dt>
                  <dd>{{ project.leader_name || '-' }}</dd>
                  <dt>Miembros</dt>
                  <dd>{{ project.member_count }}</dd>
                  <dt>Entregables</dt>
                  <dd>{{ project.deliverable_count }}</dd>
                  <dt>Aprobados</dt>
                  <dd>{{ project.reviews_approved }}</dd>
                </dl>
              </article>
            </div>
          </div>
          <p v-else class="muted">Ingresa una cohorte para ver su progreso.</p>
        </article>
      </section>

      <section v-else-if="activeResource" class="resource">
        <div class="toolbar">
          <button v-if="activeResource.canList !== false && canAccessResource(activeResource, 'list')" @click="listResource(activeResource)">Listar {{ activeResource.title }}</button>
          <input v-model="stateFor(activeResource).selectedId" placeholder="ID para obtener/eliminar" />
          <button v-if="canAccessResource(activeResource, 'get')" @click="getResource(activeResource)">Obtener por ID</button>
          <button v-if="activeResource.canDelete && canAccessResource(activeResource, 'delete')" class="danger" @click="deleteResource(activeResource)">Eliminar por ID</button>
        </div>

        <div class="grid">
          <form v-if="activeResource.canCreate && canAccessResource(activeResource, 'create')" class="panel" @submit.prevent="createResource(activeResource)">
            <h2>Crear</h2>
            <template v-for="field in activeResource.createFields" :key="field.name">
              <label>
                {{ field.label }}
                <textarea v-if="field.type === 'textarea'" v-model="stateFor(activeResource).form[field.name]" :required="field.required"></textarea>
                <select v-else-if="field.type === 'select'" v-model="stateFor(activeResource).form[field.name]" :required="field.required">
                  <option value="">Seleccionar</option>
                  <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
                </select>
                <input v-else-if="field.type === 'checkbox'" v-model="stateFor(activeResource).form[field.name]" type="checkbox" />
                <input v-else v-model="stateFor(activeResource).form[field.name]" :type="field.type || 'text'" :required="field.required" />
              </label>
            </template>
            <button type="submit">Crear</button>
          </form>

          <form v-if="activeResource.canUpdate && canAccessResource(activeResource, 'update')" class="panel" @submit.prevent="updateResource(activeResource)">
            <h2>Actualizar</h2>
            <label>ID<input v-model="stateFor(activeResource).updateId" required /></label>
            <template v-for="field in activeResource.updateFields" :key="field.name">
              <label>
                {{ field.label }}
                <textarea v-if="field.type === 'textarea'" v-model="stateFor(activeResource).updateForm[field.name]"></textarea>
                <select v-else-if="field.type === 'select'" v-model="stateFor(activeResource).updateForm[field.name]">
                  <option value="">No cambiar</option>
                  <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
                </select>
                <input v-else-if="field.type === 'checkbox'" v-model="stateFor(activeResource).updateForm[field.name]" type="checkbox" />
                <input v-else v-model="stateFor(activeResource).updateForm[field.name]" :type="field.type || 'text'" />
              </label>
            </template>
            <button type="submit">Actualizar</button>
          </form>
        </div>

        <div class="cards">
          <article v-for="item in stateFor(activeResource).items" :key="item[activeResource.idField]" class="record-card">
            <div class="record-head">
              <div>
                <h3>{{ summaryTitle(item) }}</h3>
                <p>{{ summarySubtitle(activeResource, item) }}</p>
              </div>
            </div>

            <dl class="detail-list">
              <template v-for="entry in importantFields(activeResource, item)" :key="entry.label">
                <dt>{{ entry.label }}</dt>
                <dd>{{ entry.value }}</dd>
              </template>
            </dl>

            <div class="record-actions">
                  <button @click="stateFor(activeResource).selectedId = item[activeResource.idField]; getResource(activeResource)">Ver</button>
                  <button v-if="activeResource.canDelete && canAccessResource(activeResource, 'delete')" class="danger" @click="deleteResource(activeResource, item[activeResource.idField])">Eliminar</button>
                  <div v-for="action in (activeResource.customActions || []).filter(canRunAction)" :key="action.key" class="action-box">
                    <template v-if="action.fields">
                      <label v-for="field in action.fields" :key="field.name">
                        {{ field.label }}
                        <textarea v-if="field.type === 'textarea'" v-model="actionForm(activeResource, action, item)[field.name]"></textarea>
                        <select v-else-if="field.type === 'select'" v-model="actionForm(activeResource, action, item)[field.name]">
                          <option value="">Seleccionar</option>
                          <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
                        </select>
                        <input v-else v-model="actionForm(activeResource, action, item)[field.name]" :type="field.type || 'text'" />
                      </label>
                    </template>
                    <button @click="runAction(activeResource, action, item)">{{ action.label }}</button>
                  </div>
            </div>
          </article>
        </div>

        <article class="panel">
          <h2>Resultado</h2>
          <dl v-if="stateFor(activeResource).actionResult && !Array.isArray(stateFor(activeResource).actionResult)" class="detail-list">
            <template v-for="entry in importantFields(activeResource, stateFor(activeResource).actionResult)" :key="entry.label">
              <dt>{{ entry.label }}</dt>
              <dd>{{ entry.value }}</dd>
            </template>
          </dl>
          <div v-else-if="Array.isArray(stateFor(activeResource).actionResult)" class="cards">
            <article v-for="(item, index) in stateFor(activeResource).actionResult" :key="item.id || index" class="record-card">
              <h3>{{ summaryTitle(item) }}</h3>
              <dl class="detail-list">
                <template v-for="entry in importantFields(activeResource, item)" :key="entry.label">
                  <dt>{{ entry.label }}</dt>
                  <dd>{{ entry.value }}</dd>
                </template>
              </dl>
            </article>
          </div>
          <p v-else class="muted">Aqui aparecera el resultado de la accion seleccionada.</p>
        </article>
      </section>
    </main>
  </div>
</template>
