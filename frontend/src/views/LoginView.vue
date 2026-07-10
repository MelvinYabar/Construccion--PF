<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, setSession } from '../api'

const router = useRouter()
const mode = ref('login')
const loading = ref(false)
const error = ref('')

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

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

const handleGoogleCallback = async (response) => {
  loading.value = true
  error.value = ''
  try {
    const res = await authApi.googleLogin(response.credential)
    setSession(res.access_token, res.user)
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Error con Google'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (googleClientId && window.google) {
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: handleGoogleCallback,
    })
    window.google.accounts.id.renderButton(
      document.getElementById('google-btn'),
      { theme: 'outline', size: 'large', width: '100%' }
    )
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

        <!-- Google OAuth -->
        <div id="google-btn" class="flex justify-center"></div>
      </div>

      <p class="text-center text-xs text-parmenia-textDim mt-6">
        Parmenia v1.0 · Universidad La Salle
      </p>
    </div>
  </div>
</template>
