/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ════════ 杂志-纸张-印章色板（对齐 frontend_ui_demo.html）════════
        ink: {
          DEFAULT: '#0F1115',
          2: '#1C1F26',
          3: '#2A2F3A',
          4: '#3A4150',
        },
        paper: {
          DEFAULT: '#F6F3EC',
          2: '#EFEADE',
          3: '#E6DFCB',
        },
        line: {
          DEFAULT: '#D9D2C0',
          soft: '#E6DFCB',
        },
        seal: {
          // 绯红印章 · 主强调色
          DEFAULT: '#FF5A1F',
          soft: '#FFE6DA',
          dark: '#B4360F',
        },
        cobalt: {
          // 冷钴蓝 · 次级强调 / 数据 / 链接
          DEFAULT: '#3D5AFE',
          soft: '#DCE2FF',
          dark: '#172FA8',
        },
        jade: {
          // 翡翠绿 · 通过 / OK
          DEFAULT: '#1DB955',
          soft: '#D3F4DF',
          dark: '#0F6A33',
        },
        signal: {
          // 信号红 · 告警 / 失败
          DEFAULT: '#E63946',
          soft: '#FBD7DA',
          dark: '#8B1522',
        },
        amber: {
          // 琥珀金 · 警示 / 部分通过
          DEFAULT: '#F4B740',
          soft: '#FBECC8',
          dark: '#7C5300',
        },
        // ═══════ 保留原 primary/accent/surface/success/danger，做“别名映射”
        // 让所有页面不需要改 class，只是颜色被换成本套杂志色 ═══════
        primary: {
          50: '#FFE6DA',
          100: '#FFD3BF',
          200: '#FFB08D',
          300: '#FF8E5C',
          400: '#FF763B',
          500: '#FF5A1F',   // 绯红印章色作为 primary
          600: '#E24A13',
          700: '#B4360F',
          800: '#8A2708',
          900: '#5C1700',
        },
        accent: {
          50: '#DCE2FF',
          100: '#B8C4F5',
          200: '#8AA0EF',
          300: '#5E7AE9',
          400: '#4C69FE',
          500: '#3D5AFE',   // 冷钴蓝作为 accent
          600: '#2A48E6',
          600: '#2A48E6',
        },
        surface: {
          50: '#FAF8F3',
          100: '#F6F3EC',   // paper
          200: '#EFEADE',   // paper-2
          300: '#D9D2C0',   // line
          400: '#948872',
          500: '#6B6256',
          600: '#4A443A',
          700: '#2A2F3A',   // ink-3
          800: '#1C1F26',   // ink-2
          900: '#0F1115',   // ink
        },
        success: {
          50: '#D3F4DF',
          400: '#46CF79',
          500: '#1DB955',   // jade
          600: '#0F6A33',
        },
        danger: {
          50: '#FBD7DA',
          400: '#F18A94',
          500: '#E63946',   // signal
          600: '#8B1522',
        },
      },
      fontFamily: {
        // ═══════ 杂志式字族 ═══════
        // display: 衬线小型大写大标题
        display: ['"Playfair Display SC"', '"Noto Serif SC"', 'Georgia', 'serif'],
        // sub/heading: 无衬线科技标题/导航/小标签
        sub: ['"Space Grotesk"', '"PingFang SC"', '"Noto Sans SC"', 'system-ui', 'sans-serif'],
        sans: ['"Space Grotesk"', '"PingFang SC"', '"Noto Sans SC"', 'system-ui', 'sans-serif'],
        // body: 人文衬线正文
        serif: ['"Fraunces"', '"Noto Serif SC"', 'Georgia', 'serif'],
        body: ['"Fraunces"', '"Noto Serif SC"', 'Georgia', 'serif'],
        // mono: 代码等宽
        mono: ['"JetBrains Mono"', '"Fira Code"', 'ui-monospace', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'sm-d': '6px',   // r-sm
        'md-d': '12px',  // r-md
        'lg-d': '22px',  // r-lg
        'xl-d': '34px',  // r-xl
        // 让原 tailwind 的 2xl/3xl/4xl 也对齐
        '2xl': '22px',
        '3xl': '28px',
        '4xl': '34px',
      },
      boxShadow: {
        // 纸张杂志风三级阴影
        'paper-1': '0 1px 2px rgba(15,17,21,.06), 0 1px 1px rgba(15,17,21,.04)',
        'paper-2': '0 10px 24px -10px rgba(15,17,21,.18), 0 2px 6px rgba(15,17,21,.06)',
        'paper-3': '0 30px 80px -24px rgba(15,17,21,.28), 0 6px 18px rgba(15,17,21,.08)',
        // 印章红发光
        'seal-glow': '0 0 40px -10px rgba(255,90,31,0.35)',
        'cobalt-glow': '0 0 40px -10px rgba(61,90,254,0.3)',
        // 原名映射
        soft: '0 10px 24px -10px rgba(15,17,21,.18), 0 2px 6px rgba(15,17,21,.06)',
        card: '0 1px 2px rgba(15,17,21,.06), 0 1px 1px rgba(15,17,21,.04)',
        elevated: '0 30px 80px -24px rgba(15,17,21,.28), 0 6px 18px rgba(15,17,21,.08)',
        glow: '0 0 40px -10px rgba(255,90,31,0.35)',
        'glow-amber': '0 0 40px -10px rgba(244,183,64,0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'fade-in-down': 'fadeInDown 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.4s ease-out',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        'scale-in-center': 'scaleInCenter 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'rotate-slow': 'rotateSlow 20s linear infinite',
        // 进场动画：先隐藏后位移向上 14px 显现
        'reveal': 'revealIn 0.6s ease-out both',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        scaleInCenter: {
          '0%': { opacity: '0', transform: 'scale(0.8)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        rotateSlow: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        revealIn: {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'none' },
        },
      },
      backgroundImage: {
        // 颗粒噪点（杂志纸张质感）
        'noise-paper': "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.06  0 0 0 0 0.07  0 0 0 0 0.1  0 0 0 0.8 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        // 24px 细网格
        'grid-paper':
          "linear-gradient(to right, rgba(217,210,192,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(217,210,192,0.6) 1px, transparent 1px)",
        // 杂志常用渐变
        'gradient-seal': 'linear-gradient(135deg, #FF8A5C 0%, #FF5A1F 55%, #B4360F 100%)',
        'gradient-seal-soft': 'linear-gradient(135deg, rgba(61,90,254,0.08) 0%, rgba(255,90,31,0.08) 100%)',
        'gradient-card': 'linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(255,255,255,0.78) 100%)',
      },
    },
  },
  plugins: [],
}
