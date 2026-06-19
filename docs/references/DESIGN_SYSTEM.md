# Contrato Visto — Design System v1.0
> Documento de referência para Codex, ChatGPT ou qualquer agente de IA alinhar novas páginas e componentes ao sistema visual do produto.

---

## 1. FILOSOFIA

- **Dark-first**: o tema escuro é o primário; o claro é derivado e usa as mesmas variáveis CSS.
- **Sofisticação jurídica**: premium, confiável, sem excessos. Nada de neons agressivos.
- **Fluidez**: transições em `.2s ease` por padrão; nada de animações abruptas.
- **Teal como identidade**: `#20c997` é a cor de assinatura. Usada com critério — não em tudo.
- **Hierarquia clara**: títulos bold com letter-spacing negativo; corpo regular; labels em uppercase espaçado.

---

## 2. TOKENS CSS — VARIÁVEIS

```css
/* ══ TEMA ESCURO (padrão, aplicado em [data-theme="dark"] ou :root sem atributo) ══ */
[data-theme="dark"] {
  /* Fundos */
  --bg:        #07080c;
  --surf:      #0c0f16;
  --surf2:     #111622;
  --surf3:     #171e2e;

  /* Bordas */
  --bd:        rgba(255,255,255,.07);
  --bd2:       rgba(255,255,255,.13);
  --bd3:       rgba(255,255,255,.22);

  /* Textos */
  --text:      #e4eaf2;
  --text2:     #7d8fa8;
  --text3:     #3d4f68;

  /* Navbar */
  --nav-bg:    rgba(7,8,12,.82);
  --nav-scrolled: rgba(7,8,12,.96);
  --mobile-menu-bg: rgba(7,8,12,.97);

  /* Scrollbar */
  --scrollbar: rgba(255,255,255,.10);

  /* Inputs */
  --input-bg:  #111622;
  --input-border: rgba(255,255,255,.09);
  --input-focus-bg: rgba(32,201,151,.04);

  /* Login card */
  --card-bg:   rgba(12,15,22,.88);
  --card-border: rgba(255,255,255,.13);

  /* Particles opacity scale */
  --pt-opacity-peak: .35;
  --pt-opacity-tail: .15;
}

/* ══ TEMA CLARO ══ */
[data-theme="light"] {
  /* Fundos */
  --bg:        #f0f6f3;
  --surf:      #ffffff;
  --surf2:     #f5faf7;
  --surf3:     #eaf4ef;

  /* Bordas */
  --bd:        rgba(15,100,70,.09);
  --bd2:       rgba(15,100,70,.16);
  --bd3:       rgba(15,100,70,.28);

  /* Textos */
  --text:      #0d1f1a;
  --text2:     #406858;
  --text3:     #8ab5a2;

  /* Navbar */
  --nav-bg:    rgba(240,246,243,.85);
  --nav-scrolled: rgba(240,246,243,.97);
  --mobile-menu-bg: rgba(240,246,243,.98);

  /* Scrollbar */
  --scrollbar: rgba(15,100,70,.18);

  /* Inputs */
  --input-bg:    #ffffff;
  --input-border: rgba(15,100,70,.14);
  --input-focus-bg: rgba(32,201,151,.05);

  /* Login card */
  --card-bg:    rgba(255,255,255,.92);
  --card-border: rgba(15,100,70,.14);

  /* Particles */
  --pt-opacity-peak: .18;
  --pt-opacity-tail: .07;
}

/* ══ CONSTANTES (independentes de tema) ══ */
:root {
  /* Acento primário (teal) */
  --teal:      #20c997;
  --teal-d:    #17a882;
  --teal-dd:   #0d6b50;
  --teal-dim:  rgba(32,201,151,.12);
  --teal-glow: rgba(32,201,151,.20);

  /* Acento laranja (alertas, highlights) */
  --orange:    #f97316;
  --or-dim:    rgba(249,115,22,.12);

  /* Acento azul (info, badges) */
  --blue:      #60a5fa;
  --blue-dim:  rgba(96,165,250,.10);

  /* Raios de borda */
  --r:         14px;
  --r-sm:      9px;
  --r-xs:      6px;
  --r-pill:    99px;

  /* Safe areas (iOS notch / Android) */
  --safe-t:    env(safe-area-inset-top,  0px);
  --safe-b:    env(safe-area-inset-bottom, 0px);
  --safe-l:    env(safe-area-inset-left, 0px);
  --safe-r:    env(safe-area-inset-right, 0px);

  /* Sombra padrão de card */
  --sh-card:   0 1px 3px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.08);
  --sh-card-hover: 0 8px 32px rgba(0,0,0,.14);

  /* Transição padrão */
  --t:         .2s ease;
  --t-slow:    .35s ease;
  --spring:    cubic-bezier(.34,1.56,.64,1);
  --ease-out:  cubic-bezier(.22,1,.36,1);
}
```

---

## 3. TIPOGRAFIA

```css
/* Família */
font-family: 'Segoe UI', system-ui, sans-serif;

/* Escala */
--fs-hero:   clamp(32px, 6.5vw, 72px);  /* Títulos hero */
--fs-h1:     clamp(26px, 4vw,   46px);  /* Seção título */
--fs-h2:     clamp(22px, 3vw,   36px);  /* Sub-seção */
--fs-body:   15px;                       /* Corpo padrão */
--fs-sm:     13px;                       /* Descrições */
--fs-xs:     11px;                       /* Labels, hints */
--fs-label:  10px; /* uppercase + letter-spacing: 2px */

/* Pesos */
--fw-regular: 400;
--fw-medium:  500;
--fw-semibold: 600;
--fw-bold:    700;
--fw-black:   800;

/* Letter-spacing */
/* Títulos hero: -1.5px a -2px  */
/* Títulos seção: -1px a -1.2px */
/* Labels uppercase: +2px a +2.5px */
/* Body: 0 */
```

---

## 4. PALETA COMPLETA

### Teal (identidade)
| Token | Valor | Uso |
|-------|-------|-----|
| `--teal` | `#20c997` | Hover, focus ring, ícones ativos, dots |
| `--teal-d` | `#17a882` | Botão primário (start) |
| `--teal-dd` | `#0d6b50` | Botão primário (end), sombra |
| `--teal-dim` | `rgba(32,201,151,.12)` | Fundo de badge/tag, hover sutil |
| `--teal-glow` | `rgba(32,201,151,.20)` | Box-shadow de glow |

### Status / Semântica
| Token | Valor | Uso |
|-------|-------|-----|
| `--orange` | `#f97316` | Avisos, badge "pendente", hub da animação |
| `--or-dim` | `rgba(249,115,22,.12)` | Fundo badge laranja |
| `--blue` | `#60a5fa` | Info, badge "em análise" |
| `--blue-dim` | `rgba(96,165,250,.10)` | Fundo badge azul |
| Verde badge OK | `--teal-dim` + `--teal` | Badge "aprovado" |
| Roxo agente | `#a855f7` | Nó "Validação" na animação |
| Rosa processamento | `#ec4899` | Nó "Processamento" |
| Verde base | `#22c55e` | Nó "Base de Dados" |
| Amarelo IA | `#eab308` | Nó "Agente IA" |

### Logo / Brand
```css
.brand-logo {
  background: linear-gradient(145deg, #20d182, #0d9f62);
  box-shadow: 0 2px 12px rgba(13,159,98,.35);
  color: #fff;
}
/* Tema claro: mesmo gradiente, sombra um pouco mais forte */
```

---

## 5. COMPONENTES PRINCIPAIS

### 5.1 Navbar
```
height: 62px
backdrop-filter: blur(24px)
border-bottom: 1px solid var(--bd)
background: var(--nav-bg)   → var(--nav-scrolled) ao rolar >20px

Botão "Entrar": texto, cor var(--text2), hover: var(--teal) + var(--teal-dim) bg
Botão "Solicitar demo": gradiente teal, box-shadow teal, hover translateY(-1px)
Hamburger mobile: ≤760px, min 44×44px touch target
```

### 5.2 Botões

**Primário (btn-primary)**
```css
background: linear-gradient(135deg, var(--teal-d), var(--teal-dd));
padding: 13px 26px; border-radius: 11px; font-weight: 700;
box-shadow: 0 0 0 1px rgba(255,255,255,.12) inset, 0 6px 28px rgba(32,201,151,.32);
/* Hover: translateY(-4px) + sombra mais forte */
/* Animação idle: float 3.8s ease-in-out infinite (sobe 6px) */
/* Efeito: shimmer sweep no ::after no hover */
/* Tema claro: mesma cor, sombra ajustada */
```

**Outline (btn-outline)**
```css
border: 1px solid var(--bd2); background: rgba(255,255,255,.04);
padding: 12px 22px; border-radius: 11px; font-weight: 500;
/* Hover: translateY(-2px), border var(--bd3) */
/* Tema claro: border var(--bd2), bg rgba(0,0,0,.02) */
```

**Ghost (btn-ghost)**
```css
color: var(--text2); padding: 12px 18px; no border/bg;
/* Hover: color var(--teal), bg var(--teal-dim) */
```

### 5.3 Cards

**Padrão (feat-card, step-card)**
```css
background: var(--surf) ou var(--bg) alternados;
border: 1px solid var(--bd); border-radius: var(--r);
padding: 26px 24px;
/* Hover: translateY(-3px), border var(--bd2), sombra elevada */
/* Linha decorativa top no hover: gradiente teal via ::after opacity 0→.5 */
```

**Step card**
```css
/* Barra lateral esquerda 3px no hover (::before): gradiente teal→transparent */
.step-num { color: rgba(255,255,255,.06) escuro / rgba(0,0,0,.06) claro }
```

**Login card**
```css
background: var(--card-bg); border: 1px solid var(--card-border);
border-radius: 22px; padding: 52px 38px;
backdrop-filter: blur(24px);
box-shadow: 0 0 0 1px rgba(255,255,255,.05) inset, 0 32px 80px rgba(0,0,0,.55);
animation: card-in .65s var(--ease-out) both;
```

### 5.4 Inputs
```css
background: var(--input-bg); border: 1px solid var(--input-border);
border-radius: 8px; color: var(--text);
font-size: 16px; /* OBRIGATÓRIO — evita zoom iOS */
height: 48px; padding: 0 44px 0 38px; /* espaço para ícones */

:focus {
  border-color: rgba(32,201,151,.48);
  background: var(--input-focus-bg);
  box-shadow: 0 0 0 3px rgba(32,201,151,.10);
}
/* iOS autofill override obrigatório: */
input:-webkit-autofill { -webkit-box-shadow: 0 0 0 100px var(--input-bg) inset; }
```

### 5.5 Badges / Tags
```css
/* Teal */  bg: var(--teal-dim); color: var(--teal); border: 1px solid rgba(32,201,151,.18);
/* Orange */ bg: var(--or-dim); color: var(--orange); border: 1px solid rgba(249,115,22,.18);
/* Blue */  bg: var(--blue-dim); color: var(--blue); border: 1px solid rgba(96,165,250,.18);

font-size: 10px; font-weight: 700; letter-spacing: .8px; text-transform: uppercase;
padding: 3px 10px; border-radius: var(--r-pill);
```

### 5.6 Section tag (label de seção)
```css
display: inline-flex; align-items: center; gap: 6px;
font-size: 10.5px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
color: var(--teal); background: var(--teal-dim); border: 1px solid rgba(32,201,151,.20);
padding: 4px 12px; border-radius: var(--r-pill); margin-bottom: 16px;
```

### 5.7 Role Selector (login)
```css
.role {
  min-height: 48px; border: 1px solid var(--bd); border-radius: 9px;
  background: rgba(255,255,255,.02) / rgba(0,0,0,.02);
  /* Hover: border var(--bd2), bg mais visível */
  /* Active: bg rgba(32,201,151,.08), border rgba(32,201,151,.32) */
  /* Active label: color var(--teal) */
  /* Active dot: opacity 1, scale(1) — spring animation */
}
```

---

## 6. ANIMAÇÕES

### Pipeline (Canvas Animation)
```
Hub central: laranja (#f97316), gradiente, glow pulsante, 3 anéis concêntricos
Nós externos: 6 ícones com cores únicas
Cometas: viajam de fora para dentro (nó → hub)
Orbs: 3 pontos orbitando em raios diferentes (132, 158, 104 px base)
Frame rate: requestAnimationFrame, pausa com visibilitychange
DPR: Math.min(devicePixelRatio, 2) — HiDPI sem custo excessivo
```

### Botão float
```css
@keyframes btn-float {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(-6px); }
}
duration: 3.8s ease-in-out infinite
```

### Shimmer (botão hover)
```css
.btn::after {
  background: linear-gradient(105deg, transparent 38%, rgba(255,255,255,.16) 50%, transparent 62%);
  transform: translateX(-120%);
  transition: transform .55s ease;
}
:hover::after { transform: translateX(120%); }
```

### Card entrance
```css
@keyframes card-in {
  from { opacity: 0; transform: translateY(30px) scale(.96); }
  to   { opacity: 1; transform: none; }
}
```

### Partículas (artístico)
```
18 pontos pequenos (1.5–4px), cores teal/azul/laranja
Sobem de baixo para cima em loop, opacidade variada
Velocidade: 12–32s por partícula
```

### Ring login (escudo)
```css
@keyframes ring-sp { to { transform: rotate(360deg); } }
/* Conic gradient com ponto de luz que gira */
/* Glow abaixo: radial-gradient pulsante, 3.2s ease-in-out */
```

---

## 7. LAYOUT E BREAKPOINTS

```
Desktop large:  >1200px — max-width containers: 1060px (grid) / 860px (animação) / 820px (dash)
Desktop:        >760px  — layout completo, navbar com links
Tablet:         480–760px — grids 2 colunas, navbar hamburguer
Mobile:         ≤480px  — 1 coluna, padding 16px, font-size reduzido
iPhone SE:      ≤375px  — labels menores, elementos compactados
```

```
Containers:
  .hero:          max-width none (full), padding clamp(60px,10vw,110px) v
  .steps-grid:    max-width 1060px, 4→2→1 cols
  .feats-grid:    max-width 1060px, 3→2→1 cols
  .vis-inner:     max-width 1060px, 2→1 cols
  .prods-grid:    max-width 760px,  2→1 cols
  .sec-box:       max-width 680px,  centrado
  .dash-wrap:     max-width 820px
  .anim-frame:    max-width 860px, h 440→360→300px
  .login-card:    max-width 428px
```

---

## 8. TEMA CLARO — REGRAS ESPECÍFICAS

```
Fundo: #f0f6f3 (verde-branco suave)
Superfície: #ffffff
Texto primário: #0d1f1a (quase preto-verde)
Texto secundário: #406858 (verde médio)
Texto muted: #8ab5a2 (verde suave)

Navbar: fundo rgba(240,246,243,.85), mesmo altura/blur
Cards: fundo branco puro (#fff), sombra suave rgba(0,0,0,.06)
Inputs: fundo branco, borda rgba(15,100,70,.14)
Step numbers: rgba(0,0,0,.05) (quase invisível)
Partículas: opacidade reduzida (peak .18, tail .07)
Login card: fundo rgba(255,255,255,.92) + borda verde suave
Scrollbar: rgba(15,100,70,.18)

NUNCA mudar: --teal, --teal-d, --teal-dd (cores de acento constantes)
NUNCA mudar: --orange, --blue e suas variantes dim
NUNCA mudar: raios, tipografia, breakpoints, animações
```

---

## 9. REGRAS DE ACESSIBILIDADE

```
- font-size: 16px em TODOS os inputs (evita zoom iOS Safari)
- min-height/width: 44px em elementos tocáveis (padrão Apple/Google)
- :focus-visible com outline: 2px solid var(--teal); outline-offset: 2px
- aria-label em botões icônicos
- role="radiogroup" + role="radio" + aria-checked no seletor de perfil
- aria-live="polite" no toast de feedback
- visibilitychange para pausar animação canvas em background
- navigator.vibrate(6) no select de role (Android haptics)
- env(safe-area-inset-*) em nav, footer e login
```

---

## 10. ESTRUTURA DE ARQUIVOS

```
contrato-visto-app.html     ← App principal (landing + login, toggle de tema)
DESIGN_SYSTEM.md            ← Este documento
```

### Estrutura HTML interna
```
<body data-theme="dark">
  #particles                ← Partículas artísticas (fixas, z-index:0)
  .nav                      ← Navbar sticky com toggle de tema
  .mobile-menu              ← Menu mobile deslizante
  #page-landing.page        ← Landing page completa
    .hero
    .ticker
    #como-funciona (.s.s-anim)
    #funcionalidades (.s.s-feats)
    .s.s-vis
    .s.s-prods
    #seguranca (.s.s-sec)
    .s.s-cta
    .foot
  #page-login.page          ← Tela de login
    .login-bg
    .login-card
</body>
```

---

## 11. PADRÃO DE SEÇÃO (template para novas páginas)

```html
<section class="s s-[nome]" id="[ancora]">
  <div class="sec-head sec-center">
    <div><span class="sec-tag">[Label]</span></div>
    <h2 class="sec-title">[Título]</h2>
    <p class="sec-sub">[Subtítulo opcional]</p>
  </div>
  <!-- conteúdo: grid de cards, hero split, etc. -->
</section>
```

```css
/* Seção padrão */
section.s { padding: clamp(64px,10vw,104px) clamp(16px,4vw,24px); }

/* Alternância de fundos entre seções */
.s-anim   { background: var(--bg); }
.s-feats  { background: var(--surf); }
.s-vis    { background: var(--bg); }
.s-prods  { background: var(--surf); }
.s-sec    { background: var(--bg); }
.s-cta    { background: var(--surf); }
```

---

## 12. CHECKLIST PARA NOVAS PÁGINAS

Antes de entregar qualquer nova página ou componente:

- [ ] Usa `var(--bg)`, `var(--text)` etc. — sem valores hardcoded de cor (exceto teal/orange/blue constantes)
- [ ] Testado com `data-theme="dark"` e `data-theme="light"`
- [ ] `font-size: 16px` em todos os `<input>` e `<textarea>`
- [ ] Elementos tocáveis com `min-height: 44px` e `min-width: 44px`
- [ ] `focus-visible` estilizado
- [ ] Transições em `var(--t)` (`.2s ease`)
- [ ] Breakpoints: 760px (mobile menu), 480px (1 coluna), 375px (compacto)
- [ ] `env(safe-area-inset-*)` onde aplicável
- [ ] Animações pausam com `visibilitychange`
- [ ] Sem imports de fontes externas (usa Segoe UI / system-ui)
- [ ] Sem dependências JS externas (vanilla only)

---

*Gerado automaticamente pelo Claude — Contrato Visto Design System v1.0*
