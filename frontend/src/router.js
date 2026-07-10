import { createRouter, createWebHistory } from 'vue-router'
import { getStoredUser } from './api'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/', name: 'dashboard', component: () => import('./views/DashboardView.vue') },
  { path: '/noticias', name: 'noticias', component: () => import('./views/NewsView.vue') },
  { path: '/convocatorias', name: 'convocatorias', component: () => import('./views/CohortsView.vue') },
  { path: '/convocatorias/:id', name: 'cohort-detail', component: () => import('./views/CohortDetailView.vue') },
  { path: '/inscripcion', name: 'inscripcion', component: () => import('./views/EnrollmentView.vue') },
  { path: '/mi-proyecto', name: 'mi-proyecto', component: () => import('./views/MyProjectView.vue') },
  { path: '/entregables', name: 'entregables', component: () => import('./views/DeliverablesView.vue') },
  { path: '/admin', name: 'admin', component: () => import('./views/AdminView.vue'), meta: { roles: ['admin'] } },
  { path: '/perfil', name: 'perfil', component: () => import('./views/ProfileView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const user = getStoredUser()
  const token = localStorage.getItem('parmenia_token')

  if (to.meta.public) {
    if (token && user) return next('/')
    return next()
  }

  if (!token || !user) {
    return next('/login')
  }

  if (to.meta.roles && !to.meta.roles.includes(user.role)) {
    return next('/')
  }

  next()
})

export default router
