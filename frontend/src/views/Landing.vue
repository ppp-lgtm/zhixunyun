<template>
  <!-- Landing.vue · G1-3 UX-3: 品牌化营销首页（未登录访问 / 时展示） -->
  <div class="relative min-h-screen overflow-x-hidden">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 -z-10 pointer-events-none">
      <div class="absolute -top-32 -left-32 w-[560px] h-[560px] rounded-full bg-cobalt/15 blur-[120px]"></div>
      <div class="absolute top-40 -right-40 w-[620px] h-[620px] rounded-full bg-seal/15 blur-[140px]"></div>
      <div class="absolute bottom-0 left-1/3 w-[520px] h-[520px] rounded-full bg-violet-600/15 blur-[140px]"></div>
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_110%,rgba(255,90,31,0.06),transparent_55%)]"></div>
    </div>

    <!-- NAVBAR · 已按用户要求移除（2026-07-31）
         登录/立即体验按钮保留在 HERO 区正下方 CTA 处，用户可随时进入系统。
    -->

    <!-- HERO -->
    <section class="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 pt-12 pb-20 sm:pt-20 sm:pb-28">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div class="lg:col-span-7 order-2 lg:order-1 relative">
          <div class="chip-mag !bg-seal/10 !text-seal-dark !border-seal/30 !text-[11.5px] !px-3.5 !py-1.5 mb-6 inline-flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-seal animate-pulse"></span>
            2026 全国高校教学软件大赛 · 自主研发
          </div>
          <h1 class="font-display text-ink tracking-tight leading-[1.08] font-black">
            <span class="block text-[44px] sm:text-[56px] lg:text-[64px]">
              让软件实训的<span class="bg-gradient-to-r from-seal via-cobalt to-violet-600 bg-clip-text text-transparent">每一行代码</span>
            </span>
            <span class="block text-[40px] sm:text-[50px] lg:text-[58px] mt-2">都有智能的反馈。</span>
          </h1>
          <p class="mt-7 text-[15px] sm:text-[16px] text-ink-2 leading-[1.9] font-body max-w-[56ch]">
            基于大模型 + 静态代码分析的<strong class="text-ink">软件实训教学结果智能检查评价平台</strong>，覆盖 <span class="font-mono text-seal-dark">代码/Docx/PDF/截图/Zip</span> 全类型提交，自动评分、抄袭检测、班级报表、企业人岗匹配一体化。
          </p>
          <div class="mt-9 flex flex-wrap gap-3">
            <button @click="$router.push('/login')"
                    class="btn-mag btn-mag-primary !px-6 !py-3.5 text-[14.5px] shadow-[0_16px_40px_-14px_rgba(255,90,31,0.7)]">
              <Icon icon="mdi:rocket-launch-outline" class="mr-1.5" inline width="16" /> 现在就开始评价
            </button>
            <a href="#features"
               class="btn-mag btn-mag-ghost !px-6 !py-3.5 text-[14.5px]">
              <Icon icon="mdi:play-circle-outline" class="mr-1.5" inline width="16" /> 观看 2 分钟介绍
            </a>
          </div>

          <!-- 信任徽标 -->
          <div class="mt-12 flex items-center gap-8 text-[12px] text-ink-4 uppercase tracking-[0.14em] font-sub font-bold">
            <span class="flex items-center gap-2">
              <Icon icon="mdi:check-decagram" class="text-jade-dark text-base" inline width="14" />
              支持国产 CPU / OS
            </span>
            <span class="flex items-center gap-2">
              <Icon icon="mdi:lock-check" class="text-cobalt text-base" inline width="14" />
              数据本地存储
            </span>
            <span class="hidden sm:flex items-center gap-2">
              <Icon icon="mdi:api" class="text-violet-700 text-base" inline width="14" />
              Ollama / 云端 LLM 双模式
            </span>
          </div>

          <!-- 数字证明 -->
          <div class="mt-10 grid grid-cols-3 gap-3 sm:gap-6 max-w-xl">
            <div v-for="s in HERO_STATS" :key="s.label"
                 class="rounded-2xl border border-line/80 bg-paper/60 backdrop-blur-sm px-4 sm:px-5 py-3.5 sm:py-4">
              <div class="font-display font-black text-ink text-[22px] sm:text-[26px] tracking-tight leading-none">
                {{ s.value }}
              </div>
              <div class="mt-1.5 text-[11px] sm:text-[12px] text-ink-3 font-semibold tracking-wide">{{ s.label }}</div>
            </div>
          </div>
        </div>

        <!-- 右侧产品预览 Mock -->
        <div class="lg:col-span-5 order-1 lg:order-2">
          <div class="relative">
            <!-- 装饰光环 -->
            <div class="absolute -inset-6 bg-gradient-to-br from-cobalt/20 via-seal/10 to-violet-600/20 blur-3xl rounded-[48px]"></div>
            <!-- 模拟窗口 -->
            <div class="relative rounded-[28px] border border-line/80 bg-paper shadow-[0_32px_80px_-24px_rgba(15,23,42,0.35)] overflow-hidden animate-[float_6s_ease-in-out_infinite]">
              <!-- 窗口顶部 -->
              <div class="h-11 px-4 flex items-center justify-between border-b border-line/70 bg-paper-2/40">
                <div class="flex items-center gap-1.5">
                  <span class="w-3 h-3 rounded-full bg-[#FF5F57]"></span>
                  <span class="w-3 h-3 rounded-full bg-[#FEBC2E]"></span>
                  <span class="w-3 h-3 rounded-full bg-[#28C840]"></span>
                </div>
                <div class="text-[10.5px] font-mono text-ink-4 tracking-wide">zhixunyun.local / evaluation</div>
                <span class="chip-mag !bg-jade/10 !text-jade-dark !border-jade/30 !py-0.5 !px-2 !text-[10px] uppercase tracking-[0.14em]">LIVE</span>
              </div>

              <!-- 模拟 AI 评价内容 -->
              <div class="p-5 sm:p-6 bg-gradient-to-br from-paper to-paper-2/40">
                <!-- 评分条 -->
                <div class="flex items-center justify-between mb-5">
                  <div>
                    <div class="text-[11px] text-ink-4 uppercase tracking-[0.16em] font-sub font-bold">总评分</div>
                    <div class="font-display font-black text-4xl mt-1 bg-gradient-to-r from-cobalt to-seal bg-clip-text text-transparent leading-none">86.5</div>
                  </div>
                  <div class="flex gap-2">
                    <span class="chip-mag !bg-cobalt/10 !text-cobalt !border-cobalt/20 !text-[11px]">代码质量 A</span>
                    <span class="chip-mag !bg-seal/10 !text-seal-dark !border-seal/30 !text-[11px]">抄袭 < 5%</span>
                  </div>
                </div>

                <!-- 维度条 -->
                <div class="space-y-2.5 mb-6">
                  <div v-for="(d, i) in DIM_BARS" :key="i">
                    <div class="flex items-center justify-between text-[11.5px] font-semibold mb-1">
                      <span class="text-ink-2">{{ d.name }}</span>
                      <span class="font-mono text-ink">{{ d.score }}</span>
                    </div>
                    <div class="h-1.5 rounded-full bg-line overflow-hidden">
                      <div class="h-full rounded-full"
                           :class="d.barClass"
                           :style="{ width: d.score + '%' }"></div>
                    </div>
                  </div>
                </div>

                <!-- 日志区 -->
                <div class="rounded-2xl border border-line/80 bg-ink/[0.02] overflow-hidden">
                  <div class="px-3.5 py-2 border-b border-line/70 flex items-center justify-between text-[10.5px] uppercase tracking-[0.16em] font-sub font-bold text-ink-4">
                    <span class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-seal animate-pulse"></span> SSE 流式推送</span>
                    step 3 / 5
                  </div>
                  <div class="p-3.5 font-mono text-[11px] text-ink-2 leading-relaxed space-y-1">
                    <div><span class="text-jade-dark">[1/5]</span> parse: 解析出 <span class="text-cobalt font-bold">12</span> 个源码文件，4 张步骤截图</div>
                    <div><span class="text-jade-dark">[2/5]</span> analyze: LOC=1,284，函数=67，圈复杂度高=2</div>
                    <div><span class="text-seal-dark">[3/5]</span> ai_score: 正在生成多维度点评建议…</div>
                    <div class="opacity-50">[4/5] save → submission #3281 / evaluation #4012</div>
                    <div class="opacity-30">[5/5] done → 即将跳转结果页</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 装饰小卡片 1 -->
            <div class="hidden sm:block absolute -bottom-6 -left-8 w-56 rounded-2xl bg-paper border border-line shadow-[0_18px_40px_-16px_rgba(15,23,42,0.25)] p-4 animate-[float_7s_ease-in-out_infinite]" style="animation-delay: -1s">
              <div class="flex items-center gap-2.5 mb-2">
                <div class="w-8 h-8 rounded-xl bg-jade/15 text-jade-dark flex items-center justify-center">
                  <Icon icon="mdi:printer-pos-cog-outline" class="text-lg" />
                </div>
                <div>
                  <div class="font-display font-bold text-[13px] text-ink leading-none">三层报表导出</div>
                  <div class="text-[10px] text-ink-4 mt-0.5">PDF · XLSX · 9 份/次</div>
                </div>
              </div>
              <div class="flex items-center gap-1 mt-2.5">
                <span class="chip-mag !text-[9.5px] !py-0.5 !px-1.5 !bg-cobalt/10 !text-cobalt !border-cobalt/20">班级</span>
                <span class="chip-mag !text-[9.5px] !py-0.5 !px-1.5 !bg-seal/10 !text-seal-dark !border-seal/30">校级</span>
                <span class="chip-mag !text-[9.5px] !py-0.5 !px-1.5 !bg-violet-600/10 !text-violet-700 !border-violet-600/20">专业</span>
              </div>
            </div>

            <!-- 装饰小卡片 2 -->
            <div class="hidden sm:block absolute -top-5 -right-6 w-60 rounded-2xl bg-paper border border-line shadow-[0_18px_40px_-16px_rgba(15,23,42,0.25)] p-4 animate-[float_8s_ease-in-out_infinite]" style="animation-delay: -2.5s">
              <div class="flex items-center gap-2.5 mb-3">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-cobalt to-violet-600 text-white flex items-center justify-center">
                  <Icon icon="mdi:radar" class="text-lg" />
                </div>
                <div>
                  <div class="font-display font-bold text-[13px] text-ink leading-none">人岗智能匹配</div>
                  <div class="text-[10px] text-ink-4 mt-0.5">92% 企业/学生精准匹配</div>
                </div>
              </div>
              <div class="h-14 relative flex items-end gap-1">
                <div v-for="h in [40, 62, 78, 92, 85, 70, 55]" :key="h"
                     class="flex-1 rounded-t-md bg-gradient-to-t from-cobalt/60 to-seal/80"
                     :style="{ height: h + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURES · 7 大核心能力 -->
    <section id="features" class="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-20">
      <div class="text-center mb-14 max-w-2xl mx-auto">
        <h2 class="font-display font-black text-3xl sm:text-4xl text-ink tracking-tight">一个平台覆盖软件实训教学的<strong class="bg-gradient-to-r from-seal to-cobalt bg-clip-text text-transparent">全链路闭环</strong></h2>
        <p class="mt-4 text-[14.5px] text-ink-2 leading-[1.9]">从任务发布 → 多格式提交 → AI+教师+企业三方评价 → 报表导出 → 就业人岗匹配，完整打通软件实训教学每一步。</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <article v-for="(f, i) in FEATURES" :key="i"
                 class="card-mag p-6 hover:-translate-y-0.5 transition-all duration-300 group">
          <div class="w-14 h-14 rounded-2xl mb-5 flex items-center justify-center text-2xl transition-all duration-300 group-hover:scale-110 group-hover:-rotate-3"
               :class="f.color">
            <Icon :icon="f.icon" />
          </div>
          <h3 class="font-display font-bold text-[18px] text-ink mb-2">{{ f.title }}</h3>
          <p class="text-[13px] text-ink-3 leading-[1.9] mb-4">{{ f.desc }}</p>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="(t, j) in f.tags" :key="j"
                  class="text-[10.5px] px-2 py-1 rounded-lg font-mono bg-paper-2/80 text-ink-3 border border-line/60">{{ t }}</span>
          </div>
        </article>
      </div>
    </section>

    <!-- 龙芯麒麟生态 Logo 墙 -->
    <section class="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 pb-24">
      <div class="card-mag p-0 overflow-hidden relative">
        <div class="absolute inset-0 bg-gradient-to-br from-cobalt/5 via-transparent to-violet-600/5"></div>
        <div class="relative px-8 py-10 sm:px-12 sm:py-12 text-center">
          <div class="section-label mb-3">COMPATIBILITY · 信创生态</div>
          <h3 class="font-display font-black text-2xl sm:text-3xl text-ink tracking-tight">
            100% 兼容<strong class="bg-gradient-to-r from-cobalt to-seal bg-clip-text text-transparent">国产 CPU & 国产操作系统</strong>
          </h3>
          <p class="mt-3 text-[13.5px] text-ink-3 max-w-2xl mx-auto">通过 LoongArch + 银河麒麟部署验证（阶段 I1 强制要求），零分包离线可跑，适配政企客户合规要求。</p>

          <!-- Logo 网格（纯 CSS / Iconify 模拟，不依赖外部图片） -->
          <div class="mt-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
            <div v-for="(l, i) in LOGOS" :key="i"
                 class="rounded-2xl border border-line/80 bg-paper hover:bg-paper-2/60 hover:border-seal/40 transition-all p-4 sm:p-5 flex flex-col items-center justify-center aspect-[4/3]">
              <div class="w-11 h-11 rounded-2xl flex items-center justify-center text-xl mb-2" :class="l.bg">
                <Icon :icon="l.icon" :class="l.fg" />
              </div>
              <div class="font-display font-bold text-[13px] text-ink leading-tight text-center">{{ l.name }}</div>
              <div class="text-[10.5px] text-ink-4 mt-0.5 text-center">{{ l.sub }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 pb-20">
      <div class="rounded-[32px] relative overflow-hidden bg-gradient-to-br from-seal via-[#FF3D00] to-cobalt text-white p-10 sm:p-14 shadow-[0_30px_80px_-24px_rgba(255,90,31,0.6)]">
        <div class="absolute -top-20 -right-16 w-80 h-80 rounded-full bg-white/10 blur-3xl"></div>
        <div class="absolute -bottom-24 -left-8 w-80 h-80 rounded-full bg-cobalt/20 blur-3xl"></div>
        <div class="relative grid grid-cols-1 lg:grid-cols-5 gap-8 items-center">
          <div class="lg:col-span-3">
            <div class="text-[11px] uppercase tracking-[0.22em] font-sub font-bold text-white/80 mb-3">
              准备好开始了吗？
            </div>
            <h2 class="font-display font-black text-[36px] sm:text-[44px] leading-[1.1] tracking-tight mb-4">
              立即开通智讯云，<br class="hidden sm:block" />让每个实训学生都拥有<strong class="underline decoration-white/40 decoration-4 underline-offset-4">AI 导师 + 企业 HR</strong>。
            </h2>
            <p class="text-white/80 text-[14.5px] max-w-xl leading-[1.9]">
              1 分钟完成配置；无公网大模型 Key 时启用内置静态分析引擎，照样出结果。
            </p>
          </div>
          <div class="lg:col-span-2 flex flex-col sm:flex-row lg:flex-col gap-3 lg:items-end">
            <button @click="$router.push('/login')"
                    class="px-7 py-3.5 rounded-2xl bg-white text-seal-dark font-display font-bold text-[15px] shadow-[0_16px_40px_-14px_rgba(0,0,0,0.4)] hover:scale-[1.02] transition-all">
              <Icon icon="mdi:login-variant" class="mr-1.5" inline width="16" /> 登录并进入系统
            </button>
            <a href="#features"
               class="px-7 py-3.5 rounded-2xl border border-white/30 text-white hover:bg-white/10 font-semibold text-[14px] text-center">
              我想先看功能介绍
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="relative border-t border-line/80 bg-paper-2/40">
      <div class="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-10 flex flex-col sm:flex-row items-center justify-between gap-4 text-[12.5px] text-ink-3">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-seal via-cobalt to-violet-600 flex items-center justify-center text-white">
            <Icon icon="mdi:hexagon-slice-6" class="text-base" />
          </div>
          <div>
            <span class="font-display font-bold text-ink">智讯云 ZhiXunYun</span>
            <span class="mx-2 text-ink-4/60">·</span>
            <span>© 2026 参赛作品 · 实训教学评价系统 v2.0.0</span>
          </div>
        </div>
        <div class="flex items-center gap-5 font-mono text-[11.5px] text-ink-4 uppercase tracking-wider">
          <span>FastAPI</span><span>·</span>
          <span>Vue 3</span><span>·</span>
          <span>SQLite</span><span>·</span>
          <span>Ollama Ready</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { Icon } from '@iconify/vue'

const NAV_ITEMS = [
  { label: 'AI 评价', title: '核心能力：代码/文档/截图 5 步评分' },
  { label: '人岗匹配', title: 'C3 算法：历史加权平均 + 必选门槛' },
  { label: '班级报表', title: '三层报表：PDF/XLSX 一键导出' },
  { label: '企业中心', title: '岗位 CRUD + 匹配榜 + 评价工作台' },
  { label: '国产部署', title: 'LoongArch + 麒麟 离线可运行' },
]

const HERO_STATS = [
  { value: '12 类', label: '提交文件格式' },
  { value: '<3s', label: '代码静态分析' },
  { value: '8 份', label: '三层报表/次' },
]

const DIM_BARS = [
  { name: '代码质量', score: 88, barClass: 'bg-gradient-to-r from-cobalt to-jade' },
  { name: '功能完整性', score: 92, barClass: 'bg-gradient-to-r from-seal to-amber' },
  { name: '文档规范性', score: 76, barClass: 'bg-gradient-to-r from-violet-600 to-cobalt' },
  { name: '异常处理', score: 81, barClass: 'bg-gradient-to-r from-jade to-emerald-500' },
  { name: '界面设计', score: 72, barClass: 'bg-gradient-to-r from-seal to-violet-600' },
]

const FEATURES = [
  {
    title: 'AI 多维度智能评分',
    desc: '基于大模型 Prompt + 静态代码分析双引擎，5 步 SSE 流式反馈，支持无 Key 模式离线运行。',
    icon: 'mdi:robot-happy-outline',
    color: 'bg-cobalt/15 text-cobalt',
    tags: ['Prompt', 'AST分析', '5步反馈'],
  },
  {
    title: '教师评分工作台',
    desc: '同一提交自动对比 AI / 教师 / 企业三方评分差异，异常维度高亮预警，防止"人情分/误判"。',
    icon: 'mdi:scale-balance',
    color: 'bg-seal/15 text-seal-dark',
    tags: ['三方对比', '差异高亮', '一键复审'],
  },
  {
    title: '三层报表自动生成',
    desc: '个人 / 班级 / 校级三层 PDF + XLSX 报表一键出，班内排名 / 进步曲线 / 维度分布全有。',
    icon: 'mdi:printer-pos-star-outline',
    color: 'bg-jade/15 text-jade-dark',
    tags: ['PDF', 'XLSX', '9种模板'],
  },
  {
    title: '企业人岗智能匹配',
    desc: '岗位配置技能门槛 + 必选/可选维度，历史加权算法算出 Top 候选学生，支持班级定向匹配。',
    icon: 'mdi:radar',
    color: 'bg-violet-600/15 text-violet-700',
    tags: ['C3算法', 'TopN', '定向班级'],
  },
  {
    title: '抄袭代码检测',
    desc: '多文件结构相似度 + Token N-gram + 归一化权重，雷同对自动高亮，班内互抄一眼可见。',
    icon: 'mdi:content-duplicate',
    color: 'bg-amber/15 text-amber-dark',
    tags: ['AST指纹', '85%阈值', 'Top Pair'],
  },
  {
    title: '分步实训 + 步骤截图',
    desc: 'E1 阶段增强：按任务步骤分 1~8 号文件提交，自动识别"01_登录.png"并进度匹配。',
    icon: 'mdi:clipboard-list-outline',
    color: 'bg-rose-500/15 text-rose-600',
    tags: ['OCR识别', '步骤提取', '图片证据'],
  },
]

const LOGOS = [
  { name: '龙芯', icon: 'mdi:cpu-64-bit', sub: 'LoongArch',
    bg: 'bg-cobalt/15', fg: 'text-cobalt' },
  { name: '银河麒麟', icon: 'mdi:kde', sub: 'Kylin OS V10',
    bg: 'bg-jade/15', fg: 'text-jade-dark' },
  { name: '统信 UOS', icon: 'mdi:linux', sub: 'UnionTech OS',
    bg: 'bg-seal/15', fg: 'text-seal-dark' },
  { name: 'openEuler', icon: 'mdi:developer-board', sub: '欧拉 22.03 LTS',
    bg: 'bg-violet-600/15', fg: 'text-violet-700' },
  { name: 'Ollama', icon: 'mdi:whale', sub: '本地 LLM',
    bg: 'bg-amber/15', fg: 'text-amber-dark' },
  { name: 'SQLite', icon: 'mdi:database-outline', sub: '零依赖数据',
    bg: 'bg-cobalt/10', fg: 'text-violet-700' },
]
</script>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-10px); }
}
.section-label {
  display: inline-block;
  font-family: var(--font-sub, 'Barlow Semi Condensed', ui-sans-serif);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.22em;
  color: rgba(100, 116, 139, 0.9);
  text-transform: uppercase;
}
.btn-mag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.18s;
  text-decoration: none;
  white-space: nowrap;
}
.btn-mag-primary {
  background: linear-gradient(135deg, #FF5A1F 0%, #FF3D00 100%);
  color: #FFF;
  border-color: rgba(255,90,31,0.3);
  box-shadow: 0 8px 24px -10px rgba(255,90,31,0.45);
}
.btn-mag-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 32px -12px rgba(255,90,31,0.6);
}
.btn-mag-ghost {
  background: transparent;
  color: #0F172A;
  border-color: rgba(226,232,240,0.9);
}
.btn-mag-ghost:hover {
  background: rgba(255,90,31,0.06);
  border-color: rgba(255,90,31,0.35);
  color: #FF3D00;
}
.chip-mag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(226,232,240,0.9);
  background: rgba(248,250,252,0.7);
  color: rgba(71,85,105,0.95);
}
.card-mag {
  border-radius: 24px;
  border: 1px solid rgba(226,232,240,0.9);
  background: #FFFDF8;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -18px rgba(15,23,42,0.08);
}
</style>
