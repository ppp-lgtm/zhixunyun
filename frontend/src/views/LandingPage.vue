<template>
  <div class="landing font-sans overflow-x-hidden text-white">
    <!-- ═══════════════════════════════════════════
    全局统一渐变背景 — 从深空蓝自然过渡到纯黑
    ════════════════════════════════════════════ -->
    <div class="fixed inset-0 pointer-events-none -z-10"
      style="background: linear-gradient(180deg, #0A0E1A 0%, #0D1525 15%, #0F1729 30%, #0D1525 55%, #0A0E1A 80%, #060912 100%);">
    </div>
    <!-- 柔光晕（居中偏上） -->
    <div class="fixed inset-0 pointer-events-none -z-10">
      <div class="absolute top-[15%] left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-indigo-600/[0.06] rounded-full blur-[180px]"></div>
      <div class="absolute top-[50%] left-[20%] w-[500px] h-[400px] bg-blue-600/[0.04] rounded-full blur-[150px]"></div>
      <div class="absolute top-[70%] right-[10%] w-[400px] h-[350px] bg-violet-600/[0.04] rounded-full blur-[140px]"></div>
    </div>

    <!-- ═══════════════════════════════════════════
    NAVIGATION
    ════════════════════════════════════════════ -->
    <header
      class="fixed top-0 inset-x-0 z-50 transition-all duration-500"
      :class="isScrolled ? 'bg-[#0A0E1A]/85 backdrop-blur-2xl border-b border-white/[0.04]' : 'bg-transparent'"
    >
      <div class="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-16">
        <div class="flex items-center gap-3 cursor-pointer" @click="scrollToTop">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <img src="@/img/logo.png" alt="知训云" class="w-5 h-5 object-cover rounded-lg" />
          </div>
          <span class="font-bold text-base text-white tracking-tight">知训云<span class="text-gray-500 font-normal text-xs ml-2 hidden sm:inline">智能实训评价</span></span>
        </div>

        <nav class="hidden lg:flex items-center gap-1">
          <a v-for="item in navList" :key="item.href" :href="item.href"
            class="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-white/[0.04] transition-all duration-200 font-medium">
            {{ item.label }}
          </a>
        </nav>

        <div class="flex items-center gap-3">
          <button @click="goToLogin"
            class="hidden sm:inline-flex items-center gap-2 px-5 py-2 bg-white text-gray-900 rounded-xl text-sm font-bold hover:bg-gray-100 hover:shadow-lg hover:shadow-white/5 transition-all duration-300">
            立即开始
            <svg xmlns="http://www.w3.org/2000/svg" class="text-base w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
          <button class="lg:hidden text-white p-2" @click="mobileMenuOpen = !mobileMenuOpen">
            <svg v-if="!mobileMenuOpen" xmlns="http://www.w3.org/2000/svg" class="text-2xl w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="text-2xl w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <Transition name="slide-down">
        <div v-if="mobileMenuOpen" class="lg:hidden bg-[#0A0E1A]/98 backdrop-blur-2xl border-t border-white/[0.04]">
          <div class="flex flex-col px-6 py-4 gap-1">
            <a v-for="item in navList" :key="item.href" :href="item.href"
              class="py-3 text-gray-400 hover:text-white font-medium border-b border-white/[0.04] last:border-0"
              @click="mobileMenuOpen = false">{{ item.label }}</a>
            <button @click="goToLogin" class="mt-3 w-full py-3 bg-white text-gray-900 rounded-xl font-bold text-sm">立即开始</button>
          </div>
        </div>
      </Transition>
    </header>

    <!-- ═══════════════════════════════════════════
    HERO
    ════════════════════════════════════════════ -->
    <section class="relative pt-32 pb-20 lg:pt-44 lg:pb-28">
      <div class="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div class="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <!-- 左侧文字 -->
          <div class="text-center lg:text-left">
            <div class="inline-flex items-center gap-2 px-4 py-2 bg-white/[0.03] border border-white/[0.06] rounded-full text-sm text-gray-400 mb-8 animate-fade-in">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              AI 驱动 · 重塑实训评价范式
            </div>

            <h1 class="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.05] mb-8">
              <span class="block animate-fade-in-up text-gray-100">用智能</span>
              <span class="block mt-3 animate-fade-in-up text-gray-100" style="animation-delay:0.15s">
                重新定义
              </span>
              <span class="block mt-3 animate-fade-in-up" style="animation-delay:0.3s">
                <span class="bg-gradient-to-r from-indigo-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  实训评价
                </span>
              </span>
            </h1>

            <p class="text-lg lg:text-xl text-gray-500 max-w-xl mx-auto lg:mx-0 mb-10 leading-relaxed animate-fade-in-up" style="animation-delay:0.45s">
              面向软件实训教学的智能化评价平台。上传成果物即可自动评分，支持多维度分析、教师复核与数据统计。
            </p>

            <div class="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start animate-fade-in-up" style="animation-delay:0.6s">
              <button @click="goToLogin"
                class="group w-full sm:w-auto px-10 py-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl font-bold text-lg hover:from-indigo-500 hover:to-blue-500 hover:shadow-2xl hover:shadow-indigo-500/20 transition-all duration-500 flex items-center justify-center gap-3 hover:scale-[1.02]">
                立即开始使用
                <svg xmlns="http://www.w3.org/2000/svg" class="text-xl w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
              <button @click="scrollToFeatures"
                class="w-full sm:w-auto px-10 py-4 border border-white/[0.08] text-gray-400 rounded-2xl font-semibold text-lg hover:bg-white/[0.03] hover:text-gray-200 hover:border-white/[0.15] transition-all duration-300">
                了解更多
              </button>
            </div>

            <div class="flex items-center gap-8 mt-12 justify-center lg:justify-start text-sm text-gray-600 animate-fade-in-up" style="animation-delay:0.75s">
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="text-emerald-500/70 text-lg w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                企业级安全
              </div>
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="text-amber-500/70 text-lg w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                实时评分
              </div>
              <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="text-blue-500/70 text-lg w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                深度分析
              </div>
            </div>
          </div>

          <!-- 右侧可视化卡片 -->
          <div class="hidden lg:block relative animate-fade-in-up" style="animation-delay:0.4s">
            <div class="absolute -top-10 -left-10 w-20 h-20 bg-indigo-500/[0.04] rounded-3xl rotate-12 border border-white/[0.04] animate-float-slow"></div>
            <div class="absolute -bottom-6 -right-6 w-28 h-28 bg-blue-500/[0.04] rounded-3xl -rotate-12 border border-white/[0.04] animate-float-slow" style="animation-delay:-2s"></div>

            <div class="relative bg-white/[0.02] rounded-3xl border border-white/[0.06] p-8 backdrop-blur-sm">
              <div class="flex items-center gap-2 mb-8">
                <span class="w-3 h-3 rounded-full bg-white/20"></span>
                <span class="w-3 h-3 rounded-full bg-white/20"></span>
                <span class="w-3 h-3 rounded-full bg-white/20"></span>
              </div>

              <div class="space-y-4">
                <div v-for="(card, i) in demoCards" :key="i"
                  class="flex items-center gap-4 p-4 bg-white/[0.02] rounded-2xl border border-white/[0.04] hover:bg-white/[0.04] transition-colors">
                  <div class="w-11 h-11 rounded-xl flex items-center justify-center" :class="card.iconBg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="text-xl w-5 h-5" :class="card.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-300">{{ card.title }}</div>
                    <div class="text-xs text-gray-600 mt-0.5">{{ card.sub }}</div>
                  </div>
                  <span class="px-2.5 py-1 rounded-full text-xs font-bold border" :class="card.badgeClass">{{ card.score }}</span>
                </div>

                <!-- 迷你图表 -->
                <div class="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.04]">
                  <div class="text-xs text-gray-600 mb-3 font-medium">本周提交趋势</div>
                  <div class="flex items-end gap-1.5 h-16">
                    <div v-for="(h, i) in [35,55,40,70,50,80,65]" :key="i"
                      class="flex-1 rounded-t-md transition-all duration-500"
                      :style="{ height: h + '%', background: i === 5 ? 'linear-gradient(to top, rgba(99,102,241,0.6), rgba(99,102,241,0.15))' : 'linear-gradient(to top, rgba(255,255,255,0.08), rgba(255,255,255,0.02))' }">
                    </div>
                  </div>
                  <div class="flex items-center justify-between mt-2 text-[10px] text-gray-600">
                    <span v-for="d in ['一','二','三','四','五','六','日']" :key="d">{{ d }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce opacity-40">
        <svg xmlns="http://www.w3.org/2000/svg" class="text-2xl w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    过渡分隔线（非色块，仅一条微光细线）
    ════════════════════════════════════════════ -->
    <div class="max-w-7xl mx-auto px-6 lg:px-8">
      <div class="h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent"></div>
    </div>

    <!-- ═══════════════════════════════════════════
    FEATURES — Bento Grid
    ════════════════════════════════════════════ -->
    <section id="features" class="relative py-28 lg:py-36 scroll-section">
      <div class="max-w-7xl mx-auto px-6 lg:px-8">
        <div class="text-center mb-20 scroll-reveal">
          <p class="text-indigo-400/80 font-bold text-xs tracking-[0.2em] uppercase mb-5">核心能力</p>
          <h2 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 text-gray-100">全流程智能评价</h2>
          <p class="text-lg text-gray-500 max-w-2xl mx-auto">从成果上传到报告导出，覆盖实训评价的每一个环节</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- AI评分 — 跨两行，C位 -->
          <div class="lg:row-span-2 group relative bg-white/[0.015] rounded-3xl border border-white/[0.04] p-8 lg:p-10 hover:bg-white/[0.025] hover:border-indigo-500/[0.15] transition-all duration-700 scroll-reveal overflow-hidden">
            <div class="absolute top-0 right-0 w-40 h-40 bg-indigo-500/[0.03] rounded-full blur-3xl group-hover:bg-indigo-500/[0.06] transition-all duration-1000"></div>
            <div class="relative z-10">
              <div class="w-14 h-14 rounded-2xl bg-indigo-500/[0.08] flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform duration-700">
                <svg xmlns="http://www.w3.org/2000/svg" class="text-indigo-400 w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-100">AI 智能评分</h3>
              <p class="text-gray-500 leading-relaxed mb-8 text-sm">自动解析实训文档，从代码质量、功能完整性等多个维度即时生成精准评分与详细评语。</p>
              <div class="space-y-3">
                <div v-for="item in ['代码质量分析', '功能完整性检测', '文档规范性审查', '界面设计评估']" :key="item"
                  class="flex items-center gap-3 text-sm text-gray-400">
                  <div class="w-6 h-6 rounded-lg bg-indigo-500/[0.08] flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" class="text-indigo-400 text-xs w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  {{ item }}
                </div>
              </div>
            </div>
          </div>

          <!-- 其余特性卡片 -->
          <div v-for="(feat, idx) in featureCards" :key="feat.title"
            class="group relative bg-white/[0.015] rounded-3xl border border-white/[0.04] p-8 hover:bg-white/[0.025] hover:border-white/[0.1] transition-all duration-500 scroll-reveal overflow-hidden"
            :style="`animation-delay: ${idx * 0.08}s`">
            <div class="absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-all duration-700" :class="feat.glowColor"></div>
            <div class="relative z-10">
              <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl mb-5 group-hover:scale-110 transition-transform duration-500"
                :class="feat.iconBg">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" :class="feat.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 class="text-lg font-bold mb-2 text-gray-200">{{ feat.title }}</h3>
              <p class="text-gray-500 leading-relaxed text-sm">{{ feat.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    STATS — 融入背景，放射光晕居中
    ════════════════════════════════════════════ -->
    <section id="stats" class="relative py-24 lg:py-32 scroll-section">
      <!-- 中心放射光（不是色块，是指向中心的柔光） -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/[0.03] rounded-full blur-[120px] pointer-events-none"></div>

      <div class="relative max-w-7xl mx-auto px-6 lg:px-8">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-16">
          <div v-for="(item, idx) in statsList" :key="item.label"
            class="text-center scroll-reveal" :style="`animation-delay: ${idx * 0.12}s`">
            <div class="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight mb-3"
              :class="[idx === 0 ? 'text-indigo-400' : idx === 1 ? 'text-blue-400' : idx === 2 ? 'text-cyan-400' : 'text-violet-400']">
              {{ item.animatedValue }}<span v-if="item.suffix" class="text-3xl">{{ item.suffix }}</span>
            </div>
            <div class="text-base text-gray-500 font-medium">{{ item.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    过渡分隔线
    ════════════════════════════════════════════ -->
    <div class="max-w-7xl mx-auto px-6 lg:px-8">
      <div class="h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent"></div>
    </div>

    <!-- ═══════════════════════════════════════════
    ADVANTAGES — 核心优势（纯本地 SVG 图标）
    ════════════════════════════════════════════ -->
    <section id="advantages" class="relative py-28 lg:py-36 scroll-section">
      <div class="max-w-7xl mx-auto px-6 lg:px-8">
        <div class="text-center mb-20 scroll-reveal">
          <p class="text-blue-400/80 font-bold text-xs tracking-[0.2em] uppercase mb-5">为什么选择我们</p>
          <h2 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 text-gray-100">核心优势</h2>
          <p class="text-lg text-gray-500 max-w-2xl mx-auto">聚焦软件实训教学场景，兼顾评分效率、评价精准度与系统易用性</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="(item, idx) in advantageList" :key="item.title"
            class="group relative bg-white/[0.015] rounded-3xl border border-white/[0.04] p-8 lg:p-10 hover:bg-white/[0.025] transition-all duration-500 scroll-reveal"
            :style="`animation-delay: ${idx * 0.08}s`">
            
            <!-- 纯本地 SVG 图标（不依赖任何外部网络） -->
            <div class="w-10 h-10 mb-5 text-indigo-400">
              <!-- ⚡ 闪电图标：实时处理 -->
              <svg v-if="item.icon === 'lightning'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <!-- ☁️ 云图标：可扩展架构 -->
              <svg v-else-if="item.icon === 'cloud'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
              </svg>
              <!-- 🔒 锁图标：企业级安全 -->
              <svg v-else-if="item.icon === 'shield'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <!-- 🎯 靶心图标：自定义模型 -->
              <svg v-else-if="item.icon === 'target'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke-width="1.5" />
                <circle cx="12" cy="12" r="6" stroke-width="1.5" />
                <circle cx="12" cy="12" r="2" fill="currentColor" />
              </svg>
              <!-- 📊 柱状图图标：深度数据分析 -->
              <svg v-else-if="item.icon === 'chart'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <!-- 🔗 链接图标：无缝集成 -->
              <svg v-else-if="item.icon === 'link'" class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <!-- 默认占位图标（六边形/星星） -->
              <svg v-else class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </div>
            
            <h3 class="text-lg font-bold mb-2 text-gray-200 group-hover:text-white transition-colors">{{ item.title }}</h3>
            <p class="text-gray-500 leading-relaxed text-sm">{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    TESTIMONIALS
    ════════════════════════════════════════════ -->
    <section id="testimonials" class="relative py-28 lg:py-36 scroll-section">
      <div class="max-w-7xl mx-auto px-6 lg:px-8">
        <div class="text-center mb-20 scroll-reveal">
          <p class="text-emerald-400/80 font-bold text-xs tracking-[0.2em] uppercase mb-5">用户评价</p>
          <h2 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 text-gray-100">他们这样说</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-for="(item, idx) in testimonialList" :key="item.name"
            class="group relative bg-white/[0.015] rounded-3xl border border-white/[0.04] p-8 lg:p-10 hover:bg-white/[0.025] transition-all duration-500 scroll-reveal"
            :style="`animation-delay: ${idx * 0.12}s`">
            <div class="text-xl mb-5 text-amber-500/60 font-bold tracking-widest">5.0</div>
            <p class="text-gray-400 leading-relaxed mb-8 italic text-sm">"{{ item.content }}"</p>
            <div class="flex items-center gap-4 pt-6 border-t border-white/[0.04]">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500/20 to-blue-600/20 flex items-center justify-center text-sm font-bold text-gray-300 border border-white/[0.06]">
                {{ item.name.charAt(0) }}
              </div>
              <div>
                <div class="font-bold text-gray-300 text-sm">{{ item.name }}</div>
                <div class="text-xs text-gray-600">{{ item.position }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    SCENARIOS
    ════════════════════════════════════════════ -->
    <section id="scenes" class="relative py-28 lg:py-36 scroll-section">
      <div class="max-w-7xl mx-auto px-6 lg:px-8">
        <div class="text-center mb-20 scroll-reveal">
          <p class="text-amber-400/80 font-bold text-xs tracking-[0.2em] uppercase mb-5">适用场景</p>
          <h2 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 text-gray-100">全场景覆盖</h2>
          <p class="text-lg text-gray-500 max-w-2xl mx-auto">适配不同类型的实训教学与评价需求</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div v-for="(item, idx) in sceneList" :key="item.title"
            class="group relative bg-white/[0.015] rounded-3xl border border-white/[0.04] overflow-hidden hover:bg-white/[0.025] transition-all duration-500 scroll-reveal"
            :style="`animation-delay: ${idx * 0.08}s`">
            <div class="h-1" :class="item.barColor"></div>
            <div class="p-8">
              <h3 class="text-lg font-bold mb-2 text-gray-200">{{ item.title }}</h3>
              <p class="text-gray-500 text-sm mb-6">{{ item.desc }}</p>
              <ul class="space-y-3">
                <li v-for="feat in item.features" :key="feat" class="flex items-center gap-3 text-sm text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="flex-shrink-0 text-xs w-3 h-3" :class="item.checkColor" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  {{ feat }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    CTA — 唯一使用色彩强调的区域
    ════════════════════════════════════════════ -->
    <section class="relative py-28 lg:py-36 scroll-section">
      <div class="max-w-5xl mx-auto px-6 lg:px-8">
        <div class="relative rounded-3xl overflow-hidden scroll-reveal border border-indigo-500/[0.08]"
          style="background: linear-gradient(135deg, rgba(67,56,202,0.15) 0%, rgba(37,99,235,0.12) 50%, rgba(67,56,202,0.15) 100%);">
          <div class="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] bg-[length:20px_20px]"></div>
          <div class="relative z-10 p-12 lg:p-20 text-center">
            <h2 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-6 text-white">
              准备好开始了吗？
            </h2>
            <p class="text-lg text-gray-400 mb-12 max-w-xl mx-auto">
              注册即用，体验 AI 驱动的软件实训评价平台
            </p>
            <button @click="goToLogin"
              class="group inline-flex items-center gap-3 px-12 py-5 bg-white text-indigo-700 rounded-2xl font-bold text-xl hover:bg-gray-100 hover:shadow-2xl hover:shadow-black/10 transition-all duration-300 hover:scale-[1.02]">
              立即开始使用
              <svg xmlns="http://www.w3.org/2000/svg" class="text-2xl w-6 h-6 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════
    FOOTER
    ════════════════════════════════════════════ -->
    <footer class="py-16 border-t border-white/[0.04]">
      <div class="max-w-7xl mx-auto px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center gap-8 mb-10">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/30 to-blue-600/30 flex items-center justify-center border border-white/[0.06]">
              <img src="@/img/logo.png" alt="知训云" class="w-5 h-5 object-cover rounded" />
            </div>
            <span class="font-bold text-gray-300 text-sm">知训云 · 智能实训评价系统</span>
          </div>
          <div class="flex gap-8">
            <a v-for="link in ['关注我们', '赞助我们', '联系我们']" :key="link"
              class="text-gray-600 hover:text-gray-400 text-sm font-medium transition-colors cursor-pointer">{{ link }}</a>
          </div>
        </div>
        <div class="pt-8 border-t border-white/[0.04] text-center text-gray-700 text-xs">
          © 2026 知训云 智能实训评价系统 版权所有 · 用 AI 赋能实训教学
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isScrolled = ref(false)
const mobileMenuOpen = ref(false)

const navList = [
  { label: '核心能力', href: '#features' },
  { label: '核心优势', href: '#advantages' },
  { label: '用户评价', href: '#testimonials' },
  { label: '适用场景', href: '#scenes' }
]

const statsList = ref([
  { value: 2652, suffix: '+', label: '实训报告评价', animatedValue: 0 },
  { value: 27, suffix: '+', label: '使用班级', animatedValue: 0 },
  { value: 95, suffix: '%', label: '教师认可度', animatedValue: 0 },
  { value: 66, suffix: 'x', label: '效率提升', animatedValue: 0 }
])

const demoCards = [
  { icon: 'mdi:file-document-outline', title: '登录页面开发', sub: '代码质量 · 功能完整性', score: '92分', iconBg: 'bg-indigo-500/[0.08]', iconColor: 'text-indigo-400', badgeClass: 'bg-emerald-500/[0.08] text-emerald-400 border-emerald-500/[0.15]' },
  { icon: 'mdi:chart-box-outline', title: '数据统计报表', sub: '文档规范 · 界面设计', score: '88分', iconBg: 'bg-blue-500/[0.08]', iconColor: 'text-blue-400', badgeClass: 'bg-emerald-500/[0.08] text-emerald-400 border-emerald-500/[0.15]' },
  { icon: 'mdi:account-group-outline', title: '班级成绩总览', sub: '功能完整 · 交互体验', score: '85分', iconBg: 'bg-violet-500/[0.08]', iconColor: 'text-violet-400', badgeClass: 'bg-amber-500/[0.08] text-amber-400 border-amber-500/[0.15]' }
]

const featureCards = [
  { title: '教师人工复核', desc: '在AI初评基础上人工调整分数与评语，保留最终评分权。', icon: 'mdi:account-tie-outline', iconBg: 'bg-blue-500/[0.06]', iconColor: 'text-blue-400', glowColor: 'bg-blue-500/[0.04]' },
  { title: '班级全流程管理', desc: '创建班级、发布任务、收集成果物，全流程线上化。', icon: 'mdi:account-group-outline', iconBg: 'bg-violet-500/[0.06]', iconColor: 'text-violet-400', glowColor: 'bg-violet-500/[0.04]' },
  { title: '多维度数据统计', desc: '班级成绩对比、个人趋势分析、薄弱维度识别。', icon: 'mdi:chart-bar', iconBg: 'bg-cyan-500/[0.06]', iconColor: 'text-cyan-400', glowColor: 'bg-cyan-500/[0.04]' },
  { title: '自定义评价标准', desc: '自由设置评分维度与权重，适配不同实训需求。', icon: 'mdi:tune-variant', iconBg: 'bg-amber-500/[0.06]', iconColor: 'text-amber-400', glowColor: 'bg-amber-500/[0.04]' },
  { title: '报告一键导出', desc: '一键导出 Excel 与 PDF 报告，方便存档复盘。', icon: 'mdi:file-pdf-box', iconBg: 'bg-rose-500/[0.06]', iconColor: 'text-rose-400', glowColor: 'bg-rose-500/[0.04]' }
]

// 核心优势列表 — icon 字段使用纯本地 SVG 标识
const advantageList = [
  { icon: 'lightning', title: '实时处理', desc: '学生提交后数十秒内生成评分结果，即时反馈提升实训效率。' },
  { icon: 'cloud', title: '可扩展架构', desc: '云原生架构设计，支持班级、学生、提交量的无缝扩展。' },
  { icon: 'shield', title: '企业级安全', desc: '严格的角色权限管控与数据加密，保障教学数据安全。' },
  { icon: 'target', title: '自定义模型', desc: '支持自定义评价维度与权重，精准匹配不同课程教学标准。' },
  { icon: 'chart', title: '深度数据分析', desc: '多维度数据分析，识别薄弱环节，为教学改进提供依据。' },
  { icon: 'link', title: '无缝集成', desc: '提供完善的API接口，可对接院校现有教务系统和学习平台。' }
]

const testimonialList = [
  { content: '智能实训评价系统彻底改变了我们的实训教学模式，AI评分把我从重复的代码批改中解放出来，有更多时间专注于学生的个性化指导。', name: '李教授', position: '计算机学院 实训教研室主任' },
  { content: '以前实训作业批改要花一周时间，现在学生提交后即时就能出结果，还能精准定位代码问题和能力短板，学生的学习积极性显著提升。', name: '王老师', position: '软件技术专业 主讲教师' },
  { content: '提交作业后马上就能看到AI的评价和修改建议，不用等老师批改完才知道问题在哪，学习效率高了很多，还能看到班级排名。', name: '张同学', position: '2024级软件技术专业 学生' }
]

const sceneList = [
  { title: '职业院校', desc: '适配职业技能型实训教学', features: ['技能实操评价', '过程化考核', '班级批量管理', '就业能力分析'], barColor: 'bg-gradient-to-r from-amber-500/60 to-orange-500/60', checkColor: 'text-amber-400/60' },
  { title: '本科院校', desc: '满足科研与工程实训需求', features: ['多维度深度评价', '自定义评分标准', '科研能力分析', '教学数据复盘'], barColor: 'bg-gradient-to-r from-indigo-500/60 to-blue-500/60', checkColor: 'text-indigo-400/60' },
  { title: '培训机构', desc: '适配短周期高强度实训', features: ['快速班级创建', '实时评分反馈', '学员能力跟踪', '就业成果展示'], barColor: 'bg-gradient-to-r from-emerald-500/60 to-green-500/60', checkColor: 'text-emerald-400/60' },
  { title: '企业实训', desc: '满足新员工岗前评价需求', features: ['企业级标准定制', '岗位能力匹配', '批量员工考核', '成长路径分析'], barColor: 'bg-gradient-to-r from-violet-500/60 to-purple-500/60', checkColor: 'text-violet-400/60' }
]

const handleScroll = () => { isScrolled.value = window.scrollY > 30 }

const animateNumber = (target: number, refObj: { animatedValue: number }, duration = 2000) => {
  const startTime = performance.now()
  const step = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    refObj.animatedValue = Math.floor((1 - Math.pow(1 - progress, 4)) * target)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

let observer: IntersectionObserver | null = null

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed')
        if (entry.target.closest('#stats')) {
          statsList.value.forEach(item => animateNumber(item.value, item))
        }
        observer?.unobserve(entry.target)
      }
    })
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
  document.querySelectorAll('.scroll-section').forEach(el => observer?.observe(el))
  document.querySelectorAll('.scroll-reveal').forEach(el => observer?.observe(el))
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  observer?.disconnect()
})

const goToLogin = () => router.push('/login')
const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })
const scrollToFeatures = () => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
</script>

<style scoped>
/* ═══════ Scroll Reveal ═══════ */
.scroll-reveal {
  opacity: 0;
  transform: translateY(36px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.scroll-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}

/* ═══════ Keyframes ═══════ */
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@keyframes floatSlow { 0%, 100% { transform: translateY(0) rotate(var(--tw-rotate, 0deg)); } 50% { transform: translateY(-14px) rotate(var(--tw-rotate, 0deg)); } }

.animate-fade-in { animation: fadeIn 0.8s ease forwards; }
.animate-fade-in-up { opacity: 0; animation: fadeInUp 0.8s ease forwards; }
.animate-float-slow { animation: floatSlow 6s ease-in-out infinite; }

/* ═══════ Mobile Menu ═══════ */
.slide-down-enter-active,
.slide-down-leave-active { transition: all 0.3s ease; }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; max-height: 0; }
.slide-down-enter-to,
.slide-down-leave-from { opacity: 1; max-height: 400px; }

html { scroll-behavior: smooth; }
</style>