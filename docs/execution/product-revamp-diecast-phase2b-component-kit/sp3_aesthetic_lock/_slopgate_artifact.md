# Slop-gate artifact — Diecast signature screen (REV 2, em-dash copy fixes applied)

> STATIC SOURCE REVIEW (no browser). Rendered component HTML/CSS SOURCE of the signature app screen.

## WHAT this screen is

Signature goal-canvas of **Diecast** (agentic software-delivery product): three-pane shell (goal nav · canvas · Guide chat rail) on warm cream paper, IBM Plex Mono + DM Sans, one raspberry accent reserved for needs-you. Canvas top→bottom: crumb + goal header; hue-free Guide narration line (diamond mark); StageSpine (watermarked); NudgeCard (ink do-line + why-line); In-flight work = three line-density ColleagueCards; Stage artifacts = one E1 EvidenceBlock; receipt trail = 6A Decision pills. Anti-generic-SaaS, editorial, calm.

**REV 2 note:** the three em-dashes the prior tone pass flagged were removed (Guide narration split into two sentences; receipt-trail empty-state and drill-in stub now use the `·` middot the rest of the UI uses).

## Design tokens (:root)
```css
:root{
  --cream:#F5F4F0; --cream-deep:#EDEBE4; --cream-shadow:#E3E0D6;
  --paper:#FFFFFF; --ink:#1A1A28; --ink-60:#4A4860; --ink-35:#9C99AC;
  --hairline:#DDD8CD; --hairline-soft:#E8E5DC;
  --rasp:#D6235C; --rasp-08:rgba(214,35,92,.08); --rasp-15:rgba(214,35,92,.15);
  --maker:#3B5BB0; --checker:#6B47B0; --ok:#2D7D4F; --warn:#B5821A;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --sans:'DM Sans',system-ui,sans-serif;

  /* ── Motion tokens (Contract 6) — consumed by 1.2/1.3. ── */
  --morph-duration:350ms;
  --ease-morph:cubic-bezier(0.2,0.8,0.2,1);
  --motion-fast:120ms;
  /* reduced-motion fade target = 180ms (consumed in 1.2/1.3 reduced-motion branch). */

  /* ── Radius tokens. ── */
  --radius-sm:4px;
  --radius-md:8px;

  /* ── 2b additions (Contract 7) — extend, never rename. ── */
  --fail:#B22439;            /* test-red for E2/E3 repro — semantic red, DISTINCT from raspberry (needs-you). */
  /* L-level badge mapping → .lbadge--l1/l2/l3 (L1=--ink-35 · L2=--warn · L3=--rasp). Implemented as classes below. */
  /* Confidence glyphs ● high / ◐ med / ○ low are a render convention (confGlyph), never a percentage. */
}
```

## Shell + canvas layout CSS
```css
/* ── Three-tier shell: nav rail · CanvasFrame · ChatRail (layout reference: app-shell.html). ── */
#app{width:min(1280px,100%);}
.shell{
  display:grid;grid-template-columns:236px minmax(0,1fr) 304px;
  height:min(780px,calc(100vh - 56px));
  background:var(--cream);border:1px solid var(--hairline);
  box-shadow:0 24px 60px -30px rgba(26,26,40,.25), 0 2px 6px rgba(26,26,40,.05);
  border-radius:14px;overflow:hidden;
}

/* Left nav rail — persistent (vt-nav-rail anchor; mounted across BOTH families). */
.nav-rail{
  background:var(--cream);border-right:1px solid var(--hairline);
  display:flex;flex-direction:column;padding:20px 12px 14px;gap:2px;
  view-transition-name:vt-nav-rail;        /* 1.3 anchor (Contract 5) — glides, never crossfades. */
}
.brand{font-family:var(--mono);font-weight:600;font-size:18px;letter-spacing:-.5px;}
.brand em{color:var(--rasp);font-style:normal;}
.tagline{font-size:11px;color:var(--ink-35);margin:2px 0 16px;}
.rail-h{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-35);margin:12px 4px 6px;}
.nav-goal{display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:var(--radius-sm);
  cursor:pointer;color:var(--ink-60);text-decoration:none;}
.nav-goal:hover{background:var(--cream-deep);}
.nav-goal.sel{background:var(--rasp-08);color:var(--ink);}
.nav-goal .fam{font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.04em;
  color:var(--ink-35);min-width:34px;}
.nav-goal.sel .fam{color:var(--rasp);}
.nav-goal .t{flex:1;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.nav-dead{color:var(--ink-35);cursor:default;}
.nav-dead:hover{background:transparent;}
.nav-spacer{flex:1;}

/* Center CanvasFrame — renders the resolved route's view. */
.canvas-frame{
  position:relative;overflow-y:auto;padding:26px 32px 30px;
  background:
    radial-gradient(circle, rgba(26,26,40,.045) 1px, transparent 1.2px) 0 0/18px 18px,
    var(--cream);
}

/* Right ChatRail — persistent across routes (vt-chat-rail anchor). */
.chat-rail{
  background:var(--paper);border-left:1px solid var(--hairline);
  display:flex;flex-direction:column;min-height:0;padding:18px 16px;
  view-transition-name:vt-chat-rail;       /* 1.3 anchor (Contract 5). */
}
.chat-h{display:flex;align-items:center;gap:10px;padding-bottom:14px;
  border-bottom:1px solid var(--hairline-soft);}
.chat-h .t{font-family:var(--mono);font-weight:600;font-size:13px;}
.chat-h .s{font-size:11px;color:var(--ink-35);}
.chat-body{flex:1;display:flex;align-items:center;justify-content:center;
  color:var(--ink-35);font-size:12px;text-align:center;padding:0 8px;}
.chat-inp{border:1px solid var(--hairline);border-radius:var(--radius-md);
  padding:9px 11px;color:var(--ink-35);font-size:12px;}

/* ── GoalCanvas (two-part anatomy stubs). ── */
.crumb{font-family:var(--mono);font-size:11px;color:var(--ink-60);margin-bottom:14px;}
.crumb b{color:var(--ink);}
.goal-header{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
  view-transition-name:vt-goal-header;     /* 1.3 anchor (Contract 5) — title/crumb glide; fampill content crossfades. */
  padding:2px 0;}
.gtitle{font-family:var(--mono);font-weight:500;font-size:22px;letter-spacing:-.4px;}
.fampill{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;padding:3px 8px;border-radius:999px;
  background:var(--rasp-08);color:var(--rasp);}
.fampill.debug{background:rgba(107,71,176,.1);color:var(--checker);}
.guide-line{display:flex;align-items:center;gap:8px;margin:14px 0 4px;
  font-size:12.5px;color:var(--ink-60);}
/* ── Stage-spine ZONE WRAPPER. Carries NO view-transition-name → it rides the root
   crossfade, so on a morph the feature segment bar dissolves into the debug loop band
   ("same goal, new shape"). The four shapes + the PLACEHOLDER watermark now render through
   the StageSpine component (spine-* prefix, 2b.2a); the Phase-1 inline shape/`.ph-mark`
   CSS retired in 2b.3 with the stub markup it styled (dead-class + raw-hex sweep). ── */
.spine-zone{position:relative;margin:20px 0 18px;}
/* 2b.2b: the nudge ZONE WRAPPER — keeps the vt-nudge-card morph anchor (Contract 5/9) on a
   stable shell element; the visual card now renders INSIDE via the NudgeCard component
   (.nudge-card, nudge-* prefix). The stub child rules (.nudge .who/.do/.why) retired with the stub. */
.nudge{margin:6px 0 20px;
  view-transition-name:vt-nudge-card;      /* 1.3 anchor (Contract 5) — zone glides; NudgeCard copy crossfades. */}
/* GoalCanvas Part-2 body — stacked zones (2b.3): the work stream (line-density
   ColleagueCards) above the stage-artifacts EvidenceBlock. Was a 1fr·1fr grid of stub
   panels; the E1 block needs the full content width, so the body now flows in one column. */
.body{display:flex;flex-direction:column;gap:24px;margin-top:10px;}
.body > section{min-width:0;}
.sect-h{font-family:var(--mono);font-size:11px;color:var(--ink-60);margin-bottom:9px;}
.sect-h .k{color:var(--ink);font-weight:600;}
.panel{border:1px solid var(--hairline);border-radius:var(--radius-md);
  background:var(--paper);padding:14px;color:var(--ink-35);font-size:12px;}
/* work stream — a column of line-density ColleagueCards (the In-flight-work zone). */
.work-stream{display:flex;flex-direction:column;gap:8px;max-width:460px;}
.receipt-trail{margin-top:18px;padding-top:12px;border-top:1px dashed var(--hairline);
  font-family:var(--mono);font-size:11px;color:var(--ink-35);min-height:18px;
  display:flex;flex-direction:column;align-items:flex-start;gap:6px;
  view-transition-name:vt-receipt-trail;   /* 1.3 anchor (Contract 5) — trail glides; receipt pill crossfades in. */}
```

## Guide voice + chat-rail CSS
```css
/* ── Guide character — chosen treatment A (diamond + mono wordmark; voice = typography
   + structure, NO new hue). GuideMark reuses the Avatar diamond (single-source grammar). ── */
.gm{display:inline-flex;align-items:center;gap:7px;}
.gm-word{font-family:var(--mono);font-weight:600;font-size:11px;letter-spacing:.14em;color:var(--ink);}
/* chat voice: hairline left-rule + cream-deep tint (color-free distinction). */
.gv-chat-h{display:flex;align-items:center;gap:9px;padding-bottom:9px;
  border-bottom:1px solid var(--hairline-soft);}
.gv-chat-sub{font-family:var(--mono);font-size:11px;color:var(--ink-35);}
.gv-chat-msg{margin-top:10px;padding:9px 12px;font-size:12.5px;color:var(--ink);
  border-left:2px solid var(--ink);background:var(--cream-deep);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;}
/* nudge attribution (card carries the needs-you accent; the Guide mark stays ink). */
.gv-nudge{border:1px solid var(--hairline);border-left:3px solid var(--rasp);
  border-radius:var(--radius-md);background:var(--paper);padding:12px 14px;max-width:360px;}
.gv-nudge-who{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;
  letter-spacing:.05em;color:var(--ink-60);text-transform:uppercase;}
.gv-nudge-do{font-weight:600;font-size:14px;margin:5px 0 2px;}
.gv-nudge-why{font-size:12px;color:var(--ink-60);}
/* receipt byline. */
.gv-receipt{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;
  color:var(--ink-60);border:1px solid var(--hairline);border-radius:999px;
  background:var(--paper);padding:4px 11px;}
.gv-receipt-by{display:inline-flex;align-items:center;gap:5px;color:var(--ink-35);}

/* ── ChatRail conversation log + "Next ▸" scripted-send control. ── */
.chat-log{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:12px;
  padding:14px 2px;min-height:0;}
.chat-empty{margin:auto;color:var(--ink-35);font-size:12px;text-align:center;}
.msg{display:flex;flex-direction:column;gap:3px;}
.msg .mfrom{font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink-35);}
.msg .mtext{font-size:12.5px;color:var(--ink);border-radius:var(--radius-md);
  padding:8px 10px;background:var(--cream-deep);}
.msg.you{align-items:flex-end;}
.msg.you .mtext{background:var(--rasp-08);}
/* Guide voice (locked, 2b.3): hue-free — a left-rule + the ◈ diamond carry the Guide's
   identity, NOT color (the label-free distinctness contract; the Guide is never the checker hue). */
.msg.guide .mfrom{color:var(--ink-60);}
.msg.guide .mtext{border-left:2px solid var(--ink);border-radius:0 var(--radius-md) var(--radius-md) 0;}
.msg.system .mtext{background:transparent;color:var(--ink-35);font-style:italic;padding:2px 10px;}
.msg .mops{display:flex;gap:6px;margin-top:2px;}
.opbtn{font-family:var(--mono);font-size:11px;cursor:pointer;border:1px solid var(--rasp-15);
  background:var(--paper);color:var(--rasp);border-radius:var(--radius-sm);padding:4px 9px;}
.opbtn:hover{background:var(--rasp-08);}
.next-btn{font-family:var(--mono);font-size:12px;font-weight:500;cursor:pointer;
  border:1px solid var(--rasp);background:var(--rasp);color:var(--paper);border-radius:var(--radius-md);
  padding:9px 12px;margin:10px 0;}
.next-btn:hover{filter:brightness(1.05);}
.next-btn:disabled{background:var(--cream-deep);color:var(--ink-35);border-color:var(--hairline);
  cursor:default;filter:none;}

/* ════════════════════════════════════════════════════════════════════════
```

## ColleagueCard CSS
```css
/* ── ColleagueCard (Contract 1, pick 4C+4B): ONE component, two densities. The five
   lockup slots render in IDENTICAL order both densities (zero field drift); density is
   purely a container-layout concern + the card-only stat footer. ── */
.cc{--avatar-size:30px;font-size:12.5px;color:var(--ink);}
.cc-slot{display:inline-flex;align-items:center;gap:7px;min-width:0;}
.cc-slot--head{gap:8px;}
.cc-name{font-family:var(--mono);font-weight:600;font-size:13px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.cc-pair{font-family:var(--mono);font-size:11px;color:var(--ink-60);}
.cc-pair .cc-tie{color:var(--ink-35);margin-right:2px;}
.cc-pair--broken{color:var(--rasp);font-weight:600;}   /* missing checker = needs-you, never silent */
.cc-pair--solo{color:var(--ink-35);}
.cc-meter{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);
  font-size:11px;color:var(--ink-60);}
.cc-meter > i.cc-seg{width:11px;height:5px;border-radius:2px;background:var(--hairline);}
.cc-meter > i.cc-seg--used{background:var(--warn);}
.cc-meter--na{color:var(--ink-35);}
.cc-flight{font-family:var(--mono);font-size:11px;color:var(--checker);}
.cc-flight--idle{color:var(--ink-35);}                 /* inflight:null → visible absence, not a gap */

/* card density — 4C mini-card: head spans the top, the other four slots flow into a
   four-column row beneath (order preserved), stat footer last. */
.cc--card{--avatar-size:34px;display:grid;grid-template-columns:auto auto auto auto;
  gap:9px 16px;align-items:center;max-width:380px;
  border:1px solid var(--hairline);border-radius:var(--radius-md);
  background:var(--paper);padding:13px 15px;}
.cc--card .cc-slot--head{grid-column:1 / -1;}
.cc--card .cc-foot{grid-column:1 / -1;display:flex;justify-content:space-between;
  border-top:1px solid var(--hairline-soft);padding-top:9px;margin-top:1px;
  font-family:var(--mono);font-size:11px;color:var(--ink-35);}

/* line density — 4B compact row: same five slots, one line. */
.cc--line{--avatar-size:22px;display:flex;align-items:center;flex-wrap:wrap;gap:6px 13px;
  padding:8px 11px;border:1px solid var(--hairline-soft);border-radius:var(--radius-sm);
  background:var(--paper);}
.cc--line .cc-name{font-size:12px;}
```

## EvidenceBlock E1 CSS
```css
/* E1 · Acceptance Panel — stat tiles + screenshot strip + checker-compliance rows + PR. */
.ev-tiles{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:13px;}
.ev-tile{border:1px solid var(--hairline-soft);border-radius:var(--radius-sm);
  padding:7px 12px;background:var(--cream);min-width:74px;}
.ev-tile-n{font-family:var(--mono);font-size:17px;font-weight:600;color:var(--ink);line-height:1.1;}
.ev-tile-n--muted{color:var(--ink-35);}
.ev-tile-n--delta{color:var(--ink-60);}
.ev-tile-k{font-size:9px;color:var(--ink-35);text-transform:uppercase;letter-spacing:.05em;margin-top:2px;}
.ev-shots{display:flex;gap:8px;margin-bottom:13px;}
.ev-shot{width:84px;}
.ev-shot svg{display:block;border:1px solid var(--hairline);border-radius:var(--radius-sm);}
.ev-shot-bg{fill:var(--paper);}
.ev-shot-bar{fill:var(--cream-shadow);}
.ev-shot-ln{fill:var(--hairline);}
.ev-shot-cap{display:block;font-family:var(--mono);font-size:9px;color:var(--ink-35);margin-top:3px;text-align:center;}
.ev-checks{display:flex;flex-direction:column;gap:5px;margin-bottom:11px;}
.ev-check{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;color:var(--ink-60);}
.ev-check-code{font-weight:600;color:var(--ink);}
.ev-check--flag{color:var(--rasp);}
.ev-check--flag .ev-check-code{color:var(--rasp);}
.ev-attrib{margin-top:4px;}
.ev-attrib-lbl{font-family:var(--mono);font-size:9px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--ink-35);margin-bottom:5px;}
```

## NudgeCard CSS
```css
/* ── NudgeCard (3B): primary do-line CTA (INK-filled — hue-neutral; raspberry stays
   reserved for the needs-you rail/dial per accent discipline) + ALWAYS-present
   subordinate why-line (3B thesis: the product justifies, not just points) + ◈ Guide. ── */
.nudge-card{border:1px solid var(--hairline);border-left:3px solid var(--ink);
  border-radius:var(--radius-md);background:var(--paper);padding:13px 15px;max-width:380px;}
.nudge-who{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;
  letter-spacing:.05em;text-transform:uppercase;color:var(--ink-60);}
.nudge-do{display:inline-block;margin:9px 0 7px;padding:8px 14px;border:none;cursor:pointer;
  font-family:var(--sans);font-size:14px;font-weight:600;color:var(--cream);
  background:var(--ink);border-radius:var(--radius-sm);text-align:left;}
.nudge-do:hover{filter:brightness(1.14);}
.nudge-do:focus-visible{outline:2px solid var(--maker);outline-offset:2px;}
.nudge-why{font-size:12px;color:var(--ink-60);}
.nudge-card--empty{color:var(--rasp);font-family:var(--mono);font-size:12px;
  border:1px dashed var(--rasp);border-radius:var(--radius-md);padding:12px 14px;background:var(--rasp-08);}
```

## Decision 6A pill CSS
```css
/* 6A · inline pill: ⚖ + field diff (mono scan-line) + L-badge + DEC id. */
.dec-pill{display:inline-flex;align-items:center;gap:7px;
  border:1px solid var(--hairline);border-radius:999px;background:var(--paper);
  padding:4px 11px 4px 9px;font-size:12px;color:var(--ink-60);
  box-shadow:0 1px 2px rgba(26,26,40,.04);}
.dec-scale{font-size:13px;color:var(--ink-35);line-height:1;}
.dec-diff{font-family:var(--mono);font-size:11px;color:var(--ink);font-weight:500;}
.dec-id{font-family:var(--mono);font-size:10px;color:var(--ink-35);letter-spacing:.02em;}
.dec-pill--superseded .dec-diff{text-decoration:line-through;color:var(--ink-35);font-weight:400;}
.dec-pill--awaiting{border-style:dashed;}
/* awaiting tag — NON-animated (visible, not modal). */
.dec-await-tag{font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.05em;
  text-transform:uppercase;color:var(--warn);border:1px solid var(--warn);border-radius:999px;padding:0 6px;}
```

## Signature-screen markup

### GoalCanvas (center)
```js
function GoalCanvas() {
  const fam = appState.family;
  const spine = appState.spines[fam];
  const isDebug = fam === 'debug';
  const devMode = location.hash.includes('/dev');   // dev op-strip gated behind a #/dev suffix (1.3 handoff tidy)
  return html`
    <div class="goal-view">
      <div class="crumb">${appState.goal.crumb.replace(' / ', ' ')} <b>${appState.goal.id.toLowerCase()}</b></div>

      <!-- Part 1 · goal anatomy (header / guide / spine / nudge) -->
      <div class="goal-header">
        <span class="gtitle">${appState.goal.title}</span>
        <span class=${'fampill' + (isDebug ? ' debug' : '')}>${fam}</span>
      </div>

      <!-- Guide narration — 2b.3: the locked Guide voice (GuideMark diamond, hue-free) +
           real narration derived from ORG (FLAGGED_RULE, never hand-typed). Replaced the
           Phase-1 "character design lands in Phase 2b" placeholder. -->
      <div class="guide-line">
        <${GuideMark} size=${16}/>
        <span>The Guide is tracking this goal. It flagged ${FLAGGED_RULE} on the open PR and queued a review for you.</span>
      </div>

      <!-- Stage spine — 2b.2a: swapped from the Phase 1 inline placeholder markup to the
           StageSpine component (data UNCHANGED: appState.spines.<family>). The .spine-zone
           wrapper + its (absent) anchor placement are kept BYTE-IDENTICAL — only the inner
           content changes — so the morph contract holds: no vt-name here → the zone rides
           the root crossfade, the feature segment bar dissolving into the debug loop band
           ("same goal, new shape"). StageSpine renders its own PLACEHOLDER watermark. -->
      <div class="spine-zone">
        <${StageSpine} spine=${spine}/>
      </div>

      <!-- Nudge zone — 2b.2b: swapped from the Phase 1 inline stub to the NudgeCard (3B)
           component. The .nudge ZONE WRAPPER keeps the vt-nudge-card anchor (Contract 9 —
           anchor on the wrapper, NEVER on the kit component); only the inner content changes,
           so the morph contract holds. data-op="nudge:n2" still cycles the card's content. -->
      <div class="nudge">
        <${NudgeCard} nudge=${appState.nudge}/>
      </div>

      <!-- Part 2 · work stream + stage artifacts — 2b.3 composition: every zone renders through
           a kit component (zero Phase-1 stub markup remains). The In-flight work stream is three
           LINE-density ColleagueCards drawn from FIXTURES (the 2b kit's fixture source, C4); the
           real per-goal renderer that reads ORG.goals[id].work_stream is Phase 3. Stage artifacts
           is ONE E1 EvidenceBlock (placeholder evidence content; real wiring is Phase 3). The same
           FIXTURES.CO object is rendered at 4C density on #/board — same fixture, no field drift
           (the density-drift check). -->
      <div class="body">
        <section>
          <div class="sect-h"><span class="k">In flight</span> work</div>
          <div class="work-stream">
            <${ColleagueCard} agent=${FIXTURES.CO} density="line"/>
            <${ColleagueCard} agent=${FIXTURES.CC} density="line"/>
            <${ColleagueCard} agent=${FIXTURES.YOU} density="line"/>
          </div>
        </section>
        <section>
          <div class="sect-h"><span class="k">Stage</span> artifacts</div>
          <${EvidenceBlock} kind="E1" data=${FIXTURES.EVIDENCE.E1}/>
        </section>
      </div>

      <!-- Pinned objects — created by promote (chat artifact) / pin (canvas-local stub). -->
      ${appState.pinned.length > 0 ? html`
        <div class="pinned-wrap">
          <div class="sect-h"><span class="k">Pinned</span> on canvas</div>
          ${appState.pinned.map((p) => html`
            <div class="pinned-card">
              <div class="name">${p.title}</div>
              <div class="prov">${p.provenance}</div>
            </div>`)}
        </div>` : null}

      <!-- Drill-in execution panel — toggled by drillInto:execution (real run_node.html lift = Phase 3). -->
      ${appState.drill === 'execution' ? html`
        <div class="drill-panel">
          <div class="sect-h"><span class="k">Execution</span> drill-in (stub)</div>
          <div class="panel">run_node.html lifts here in Phase 3 · this labeled panel proves the drillInto toggle.</div>
        </div>` : null}

      <!-- receipt-trail — 2b.3: each morph receipt renders through the kit Decision component at
           the 6A pill layer (the receipt's {decision_id, label, level} map to the pill's {id,
           diff, reversibility}). The .receipt-trail ZONE WRAPPER keeps its vt-receipt-trail morph
           anchor (Contract 9 — anchor on the wrapper, never on the kit component); only the inner
           content changes, so the Phase-1 morph contract holds. -->
      <div class="receipt-trail">
        ${appState.receipts.length === 0
          ? html`receipt trail · decision receipts appear here.`
          : appState.receipts.map((r) => html`
              <${Decision} layer="pill"
                atom=${{ id: r.decision_id, diff: r.label, reversibility: r.level, status: r.status || 'recorded' }}/>`)}
      </div>

      <!-- DEV OP STRIP — GATED behind a #/dev hash suffix (1.3 handoff tidy). The showable
           goal route never renders it; append /dev (e.g. the goal hash + /dev) to expose the
           raw op buttons + the deliberately bad op (unknown-op console.warn guard path).
           Verification crutch only — not part of the showable artifact. -->
      ${devMode ? html`
        <div class="dev-strip">
          <span class="dev-label">DEV · ops</span>
          <button data-op="morph:debug">morph:debug</button>
          <button data-op="nudge:n2">nudge</button>
          <button data-op="promote:a1">promote</button>
          <button data-op="drillInto:execution">drillInto</button>
          <button data-op="pin:c1">pin</button>
          <button data-op="morf:debug">⚠ bad-op</button>
        </div>` : null}
    </div>`;
}
```

### ChatRail (right, Guide voice)
```js
function ChatRail() {
  const msgs = appState.chat.messages;
  const done = appState.chat.scriptIndex >= script.length;
  // 2b.3: the rail header speaks in the LOCKED Guide voice — the GuideMark (ink diamond +
  // mono wordmark), no checker hue. The handle derives from the routed goal title (no
  // hand-typed canonical token — the 2a.3 drift rule).
  const handle = appState.goal.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return html`
    <aside class="chat-rail">
      <div class="chat-h">
        <${GuideMark} size=${20} wordmark=${true}/>
        <div class="s">${handle}</div>
      </div>
      <div class="chat-log">
        ${msgs.length === 0
          ? html`<div class="chat-empty">Click <b>Next ▸</b> to walk the scripted demo.</div>`
          : msgs.map((m) => html`
              <div class=${'msg ' + (m.from || 'narration')}>
                <div class="mfrom">${labelFor(m.from)}</div>
                <div class="mtext">${m.text}</div>
                ${m.ops ? html`
                  <div class="mops">
                    ${m.ops.map((o) => html`<button class="opbtn" data-op=${o.op}>${o.label}</button>`)}
                  </div>` : null}
              </div>`)}
      </div>
      <!-- "Next ▸" is scenario-advance (NOT an op) — wired to advance() directly, kept
           visibly the same grammar as the data-op buttons it sits beside. -->
      <button class="next-btn" onClick=${advance} disabled=${done}>
        ${done ? 'Script complete · reload to replay' : 'Next ▸'}
      </button>
      <div class="chat-inp">Steer, ask, or override the Guide… ⏎</div>
    </aside>`;
}
```

### ColleagueCard component
```js
function ColleagueCard({ agent, density = 'card' }) {
  // The five lockup fields, in ONE fixed order — shared verbatim by both densities.
  const slots = html`
    <span class="cc-slot cc-slot--head">
      <${Avatar} kind=${agent.kind} initials=${agent.id}/>
      <span class="cc-name">${agent.slug}</span>
    </span>
    <span class="cc-slot cc-slot--pair"><${PairedTie} agent=${agent}/></span>
    <span class="cc-slot cc-slot--meter"><${ReworkMeter} rework=${agent.rework}/></span>
    <span class="cc-slot cc-slot--badge"><${LBadge} level=${agent.autonomy}/></span>
    <span class="cc-slot cc-slot--flight"><${InflightPill} agent=${agent}/></span>`;
  const foot = (density === 'card' && agent.stats)
    ? html`<div class="cc-foot"><span>${agent.stats.compliancePct}% compliant</span>
        <span>${agent.stats.loops} loops · ${agent.stats.runs} runs</span></div>`
    : null;
  return html`<div class=${'cc cc--' + density} data-agent=${agent.id}>${slots}${foot}</div>`;
}
```

### NudgeCard component
```js
function NudgeCard({ nudge }) {
  if (!nudge) { console.warn('NudgeCard: missing nudge'); return html`<div class="nudge-card--empty">⚠ no nudge</div>`; }
  return html`
    <div class="nudge-card">
      <div class="nudge-who"><${GuideMark} size=${16}/> ${nudge.who} · next step</div>
      <button class="nudge-do" data-op="nudge:n2">${nudge.do}</button>
      <div class="nudge-why">${nudge.why}</div>
    </div>`;
}
```

### DecisionPill (6A) component
```js
function DecisionPill({ atom }) {                    // 6A — inline pill
  const sup = atom.status === 'superseded';
  const awaiting = atom.status === 'awaiting_human';
  return html`
    <span class=${'dec-pill' + (sup ? ' dec-pill--superseded' : '') + (awaiting ? ' dec-pill--awaiting' : '')}>
      <span class="dec-scale">⚖</span>
      <span class="dec-diff">${atom.diff || atom.title}</span>
      <${LBadge} level=${atom.reversibility}/>
      ${awaiting ? html`<span class="dec-await-tag">awaiting</span>` : null}
      <span class="dec-id">${atom.id}</span>
    </span>`;
}
```

