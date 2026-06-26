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
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
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
        <button v-for="resource in resources" :key="resource.key" :class="{ active: activeKey === resource.key }" @click="activeKey = resource.key">
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
          <pre>{{ user }}</pre>
        </article>

        <article class="panel">
          <h2>Salud API</h2>
          <button @click="loadHealth">GET /health</button>
          <pre>{{ reports.health }}</pre>
        </article>

        <article class="panel">
          <h2>Reporte admin</h2>
          <button @click="loadDashboardReport">GET /reports/dashboard</button>
          <pre>{{ reports.dashboard }}</pre>
        </article>

        <article class="panel wide">
          <h2>Reporte por cohorte</h2>
          <div class="inline">
            <input v-model="reports.cohortId" placeholder="ID de cohorte" />
            <button @click="loadCohortReport">GET /reports/cohort/{id}/progress</button>
          </div>
          <pre>{{ reports.cohortProgress }}</pre>
        </article>
      </section>

      <section v-else-if="activeResource" class="resource">
        <div class="toolbar">
          <button v-if="activeResource.canList !== false" @click="listResource(activeResource)">Listar {{ activeResource.title }}</button>
          <input v-model="stateFor(activeResource).selectedId" placeholder="ID para obtener/eliminar" />
          <button @click="getResource(activeResource)">Obtener por ID</button>
          <button v-if="activeResource.canDelete" class="danger" @click="deleteResource(activeResource)">Eliminar por ID</button>
        </div>

        <div class="grid">
          <form v-if="activeResource.canCreate" class="panel" @submit.prevent="createResource(activeResource)">
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

          <form v-if="activeResource.canUpdate" class="panel" @submit.prevent="updateResource(activeResource)">
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

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Resumen</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in stateFor(activeResource).items" :key="item[activeResource.idField]">
                <td><code>{{ item[activeResource.idField] }}</code></td>
                <td>
                  <strong>{{ item.name || item.title || item.email || item.status || item.file_url || 'Registro' }}</strong>
                  <pre>{{ item }}</pre>
                </td>
                <td>
                  <button @click="stateFor(activeResource).selectedId = item[activeResource.idField]; getResource(activeResource)">Ver</button>
                  <button v-if="activeResource.canDelete" class="danger" @click="deleteResource(activeResource, item[activeResource.idField])">Eliminar</button>
                  <div v-for="action in activeResource.customActions || []" :key="action.key" class="action-box">
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
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <article class="panel">
          <h2>Resultado</h2>
          <pre>{{ stateFor(activeResource).actionResult }}</pre>
        </article>
      </section>
    </main>
  </div>
</template>
