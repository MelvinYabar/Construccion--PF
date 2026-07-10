<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, setSession } from '../api'

const router = useRouter()
const mode = ref('login')
const loading = ref(false)
const error = ref('')

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({
  email: '', password: '', full_name: '', faculty: '', skills: '', role: 'emprendedor',
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await authApi.login(loginForm.email, loginForm.password)
    setSession(res.access_token, res.user)
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Credenciales incorrectas'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  try {
    const payload = {
      ...registerForm,
      skills: registerForm.skills ? registerForm.skills.split(',').map(s => s.trim()) : [],
    }
    const res = await authApi.register(payload)
    setSession(res.access_token, res.user)
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Error al registrar'
  } finally {
    loading.value = false
  }
}

// Login con Google usando el flujo OAuth 2.0 Authorization Code del backend.
// El backend redirige a Google, recibe el code, lo intercambia por tokens y vuelve
// aquí con ?token=<jwt_local> que se procesa en App.vue (onMounted).
const loginWithGoogle = () => {
  window.location.href = authApi.googleLoginUrl()
}

onMounted(() => {
  // Si volvemos del callback OAuth con ?token=... en la URL, lo procesamos aquí.
  const params = new URLSearchParams(window.location.search)
  const tokenFromUrl = params.get('token')
  if (tokenFromUrl) {
    loading.value = true
    // Limpiar la URL inmediatamente (no queremos que el token quede en historial)
    window.history.replaceState({}, document.title, window.location.pathname)
    // Guardar el token y obtener el usuario
    localStorage.setItem('parmenia_token', tokenFromUrl)
    authApi.me()
      .then(user => {
        setSession(tokenFromUrl, user)
        router.push('/')
      })
      .catch(() => {
        localStorage.removeItem('parmenia_token')
        error.value = 'No se pudo completar el login con Google'
      })
      .finally(() => { loading.value = false })
  }
})
</script>

<template>
  <div class="min-h-screen bg-parmenia-cream flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-parmenia-primary to-parmenia-accent flex items-center justify-center text-white font-serif font-bold text-2xl shadow-lg mb-4">
          P
        </div>
        <h1 class="font-serif text-3xl font-bold text-parmenia-text">Parmenia</h1>
        <p class="text-sm text-parmenia-textMuted mt-1">Incubadora de Empresas · Universidad La Salle</p>
      </div>

      <!-- Card -->
      <div class="card p-6 space-y-4">
        <!-- Tabs -->
        <div class="flex gap-2 p-1 bg-parmenia-cream rounded-xl">
          <button
            @click="mode = 'login'"
            class="flex-1 py-2 rounded-lg text-sm font-semibold transition"
            :class="mode === 'login' ? 'bg-parmenia-card text-parmenia-primary shadow-sm' : 'text-parmenia-textMuted'"
          >Iniciar sesión</button>
          <button
            @click="mode = 'register'"
            class="flex-1 py-2 rounded-lg text-sm font-semibold transition"
            :class="mode === 'register' ? 'bg-parmenia-card text-parmenia-primary shadow-sm' : 'text-parmenia-textMuted'"
          >Registrarse</button>
        </div>

        <div v-if="error" class="bg-parmenia-dangerSoft border border-parmenia-danger/20 rounded-lg px-3 py-2 text-sm text-parmenia-danger">
          {{ error }}
        </div>

        <!-- Login form -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Correo electrónico</label>
            <input v-model="loginForm.email" type="email" required placeholder="tu@ulasalle.edu.pe" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Contraseña</label>
            <input v-model="loginForm.password" type="password" required placeholder="••••••••" class="input" />
          </div>
          <button type="submit" :disabled="loading" class="btn-primary w-full">
            <span v-if="loading">⏳</span>
            Ingresar
          </button>
        </form>

        <!-- Register form -->
        <form v-else @submit.prevent="handleRegister" class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Nombre completo</label>
            <input v-model="registerForm.full_name" type="text" required placeholder="Juan Pérez" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Correo electrónico</label>
            <input v-model="registerForm.email" type="email" required placeholder="tu@ulasalle.edu.pe" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Contraseña</label>
            <input v-model="registerForm.password" type="password" required minlength="6" placeholder="Mínimo 6 caracteres" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Facultad</label>
            <input v-model="registerForm.faculty" type="text" placeholder="Ingeniería de Software" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Habilidades (separadas por comas)</label>
            <input v-model="registerForm.skills" type="text" placeholder="Python, Diseño, Marketing" class="input" />
          </div>
          <div>
            <label class="block text-xs font-medium text-parmenia-textMuted mb-1.5">Soy</label>
            <select v-model="registerForm.role" class="input">
              <option value="emprendedor">Emprendedor (tengo un proyecto)</option>
              <option value="mentor">Mentor (quiero guiar proyectos)</option>
            </select>
          </div>
          <button type="submit" :disabled="loading" class="btn-primary w-full">
            <span v-if="loading">⏳</span>
            Crear cuenta
          </button>
        </form>

        <!-- Divider -->
        <div class="flex items-center gap-3 py-1">
          <div class="flex-1 h-px bg-parmenia-border"></div>
          <span class="text-xs text-parmenia-textDim">o</span>
          <div class="flex-1 h-px bg-parmenia-border"></div>
        </div>

        <!-- Google OAuth — Authorization Code flow (redirige al backend) -->
        <button
          type="button"
          @click="loginWithGoogle"
          :disabled="loading"
          class="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-parmenia-border rounded-lg bg-white hover:bg-parmenia-cream transition text-sm font-medium text-parmenia-text"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuar con Google
        </button>
      </div>

      <p class="text-center text-xs text-parmenia-textDim mt-6">
        Parmenia v1.0 · Universidad La Salle
      </p>
    </div>
  </div>
</template>
