/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        parmenia: {
          // Turquesa pgAdmin style — formal, serio, sin degradados vivos
          bg: '#F4F6F8',          // gris-azulado muy claro
          surface: '#FFFFFF',      // blanco puro para tarjetas
          card: '#FFFFFF',
          border: '#D1D9E0',       // gris-azulado sutil
          sidebar: '#2C3E50',      // azul oscuro marino
          sidebarHover: '#3A5068',
          sidebarActive: '#1ABC9C',
          primary: '#1ABC9C',      // turquesa pgAdmin
          primaryHover: '#16A085',
          primarySoft: '#E8F8F5',
          accent: '#348BC4',       // azul medio (links)
          success: '#27AE60',
          successSoft: '#E9F7EF',
          warning: '#E67E22',
          warningSoft: '#FDF2E9',
          danger: '#C0392B',
          dangerSoft: '#FDEDEC',
          text: '#2C3E50',         // azul oscuro para texto
          textMuted: '#7F8C8D',    // gris medio
          textDim: '#BDC3C7',      // gris claro
          textLight: '#ECF0F1',    // texto sobre fondo oscuro
          textLightMuted: '#95A5A6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
