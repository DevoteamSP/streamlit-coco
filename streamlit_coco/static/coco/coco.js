// Ask CoCo: the launcher and the floating window (st.components.v2, isolated styles).
// It renders `data.view` (doc/features/cockpit-ask-coco.md section 9) and sends one action at a time through the
// trigger value "act". It holds no conversation logic: opening, minimising, the menu, folds, the half-typed message
// and the scroll position are the window's own and live in `globalThis.__cocoUI`, so they survive a page change.
// Nothing here may touch `document` at import time: the Markdown renderer is also run by the unit tests under node.
//
// FEATURE PARTS. The window's features beyond the first 37 frames live in static/coco/parts/<group>.js (and <group>.css), seven
// groups: questions, plans, standing, data, files, page, session. components/coco_assets.py appends them to this file in that
// order (CSS too), so this file is one component: no import, no dependency. A part is one call that registers renderers;
// it never edits this file and never touches another part's code:
//
//     part('questions', (C) => { C.wait.question = { html(w, x) { ... }, announce(w) { ... } }; });
//
// C (the registry) and x (the window, handed to every callback) are the whole interface. C is static, x is the window in front of the user.
//
//   C.h  pure helpers: esc(v) wb(v) inline(text) markdown(src) render(src) ic(name, cls) icon(name, svgPaths) CH
//        btn(label, {a, id, cls, off, html})  fold(key, off, on, html, {open, cls})  kicker(more)  blocks(list, x)
//        shell({name, kicker, title, body, acts, key})   the one waiting block: .ag-ask, pinned, answered inside itself
//        Every string that reaches markup is escaped by esc() or comes from another helper. Never put a model's text in html unescaped.
//   C.thread[kind] = (item, x, n) => {k, html} | null          a thread item of a kind the core does not know (also inside a section's items)
//   C.lead.push((view, x) => {k, html} | null)                 an item before the thread's first one
//   C.block[type] = (block, x) => html                          a block of an answer or a step (view contract: Block)
//   C.wait[kind] = {html(w, x), announce(w)}                    the pinned block of view.wait for a kind other than "request"
//   C.decorate[slot].push((item, x, d) => {})                   slot: user | queued | answer | step | system | request. d = {cls, inner, parts}:
//                                                               append to d.cls (with a leading space) and d.inner (markup at the end of the
//                                                               element), or replace a piece in d.parts (step: tool input result allowed;
//                                                               answer: text blocks copy; user: text; queued: text; system: text button;
//                                                               request: kicker extra allow decline)
//   C.pill[kind] = 'aw' | 'dn' | 'er'                           the launcher's class for a pill kind; question and plan are set (a waiting kind takes 'aw')
//   C.menu.push({order, items(view, x) => html})                menu lines (.it buttons) after the switches, sorted by order (default 50); a divider
//                                                               stands between New conversation / Disconnect, the switches and these lines. The switches
//                                                               (view.options) are drawn and handled by the core, in the host's order; C.local.add(id)
//                                                               for an option only this window applies (nothing is sent)
//   C.strip.push((view, x) => html)                             a strip between the header and the thread
//   C.composer.push({top(view, x), left(view, x), cls(view, x)}) markup above and left of the textarea inside .fld, and its classes
//   C.sendable.push((x) => bool)                                something besides text can be sent (the send button turns on)
//   C.panel[name] = (view, x) => html                           a panel over the window; x.openPanel(name), data-a="panel-close"
//   C.takeover.push((view, x) => {html, cls, claims} | null)    replaces the thread (not the header or the field); claims: hides the pinned block
//   C.footer.push((view, x, html) => html | undefined)          the footer's fix area; C.empty: the same for the empty-state body
//   C.confirm.push((view, kind) => sentence | '')               one more sentence in the New conversation / Disconnect confirmation
//   C.on(action, (target, x, event) => true | undefined)       a click on [data-a=action]; any number of parts; true: nothing more is done
//   C.input.push((event, x) => {})  C.change.push(...)          an input / change anywhere in the window, the pinned block included
//   C.escape.push((x) => true | undefined)                      Escape, after the confirmation, the menu and the panel: true when it went back one level
//   C.collect[action] = [(target, x) => fields]                 fields added to the action the core sends (send, allow, connect, ...);
//                                                               called as the action is built, it may consume local state
//   C.init.push((x) => {})                                      once per window: listeners (change, input, drag) on x.root
//   C.after.push((view, x) => {})                               after every paint
//   C.state(name)                                               an object per part that survives page changes (the window's own state)
//
//   x  view (the current view) send(action) announce(text, assertive) copy(text, button) repaint(focusSelector?) settle(id) applyOpen(node)
//      openPanel(name) closePanel() opt(id) (the state of a switch as shown) root shadow el S (the window state; parts keep theirs in C.state)
//   A render callback is called again on every view and every repaint: derive from the view and C.state, store nothing in the DOM.
//   A control typed into inside a pinned block keeps its focus across a repaint when it has data-f="<stable name>"; a button that is rebuilt
//   (a menu line, Show all) gets the focus back when another with the same data-a, data-id, data-i, data-opt is found.

const ICONS = {
  min: '<path d="M5 12h14"/>', rail: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
  dots: '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', out: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  chev: '<path d="m6 9 6 6 6-6"/>', arr: '<path d="M5 12h14M13 6l6 6-6 6"/>', send: '<path d="M12 19V5M5 12l7-7 7 7"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>', ok: '<path d="M20 6 9 17l-5-5"/>', bad: '<path d="M18 6 6 18M6 6l12 12"/>', no: '<path d="M5 12h14"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
};
const ic = (name, cls = 'i') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`;
const CH = '<svg class="ag-ch rot" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';   // the sheet's chevron: a small filled triangle
const wb = (v) => esc(v).replace(/([/_-])/g, '$1<wbr>');   // a path or a name breaks at its separators before it breaks mid-word
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------------------------------------------------------------- the sentences: one table, sent with the view (streamlit_coco/labels.py)
// L(key, vars) is the text of 'window.<key>' with {name} filled in; E() is the same escaped for markup. Never write a sentence here.
let LABELS = {}, AVOID = '', EXCLUDE = [];
const L = (key, vars) => String(LABELS[`window.${key}`] ?? `window.${key}`).replace(/\{(\w+)\}/g, (m, n) => (vars && n in vars ? vars[n] : m));
const E = (key, vars) => esc(L(key, vars));

// ---------------------------------------------------------------- Markdown from a model, rendered safely:
// everything is escaped first; the only tags that exist are the ones written below; links keep http(s) and mailto only.
const SAFE_URL = /^(https?:\/\/|mailto:)/i;
function inline(text) {
  const out = [];
  text.split(/(`[^`\n]+`)/).forEach((part, i) => {
    if (i % 2) return out.push(`<code>${esc(part.slice(1, -1))}</code>`);
    let s = esc(part);
    s = s.replace(/!\[([^\]\n]{0,200})\]\([^)\s]{1,500}\)/g, (m, alt) => `<i>[image${alt ? `: ${alt}` : ''}]</i>`);   // an image is never fetched: its description stands for it
    s = s.replace(/\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)/g, (m, label, url) => {   // bounded: an unclosed "[x](" repeated a million times must not cost a million scans
      const raw = url.replace(/&amp;/g, '&');
      return SAFE_URL.test(raw) ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>` : label;
    });
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<b>$1</b>').replace(/(^|[\s(])__([^_\s][^_\n]*?)__(?=$|[\s).,;:!?])/g, '$1<b>$2</b>').replace(/(^|[\s(])\*([^*\s][^*\n]*?)\*(?=$|[\s).,;:!?])/g, '$1<i>$2</i>')
      .replace(/(^|[\s(])_([^_\s][^_\n]*?)_(?=$|[\s).,;:!?])/g, '$1<i>$2</i>');
    out.push(s);
  });
  return out.join('');
}
const listHtml = (items) => {   // a deeper indent opens a list inside the previous item
  const open = [];
  let html = '';
  items.forEach((it) => {
    while (open.length && it.d < open.at(-1).d) html += `</li></${open.pop().tag}>`;
    if (!open.length || it.d > open.at(-1).d) { html += `<${it.tag}>`; open.push(it); } else html += '</li>';
    html += `<li>${inline(it.text)}`;
  });
  return html + open.reverse().map((o) => `</li></${o.tag}>`).join('');
};
export function renderMarkdown(src) {
  const lines = String(src ?? '').replace(/\r\n?/g, '\n').split('\n');
  const html = [];
  let para = [], list = null, quote = [];
  const flush = () => {
    if (para.length) html.push(`<p>${para.map(inline).join('<br>')}</p>`);
    if (list) html.push(listHtml(list));
    if (quote.length) html.push(`<blockquote>${quote.map(inline).join('<br>')}</blockquote>`);
    para = []; list = null; quote = [];
  };
  const cells = (row) => row.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let m;
    if ((m = line.match(/^\s*```/))) {                       // fenced code; an unclosed fence (still streaming) runs to the end
      flush();
      const code = [];
      for (i++; i < lines.length && !/^\s*```/.test(lines[i]); i++) code.push(lines[i]);
      html.push(`<pre><code>${esc(code.join('\n'))}</code></pre>`);
    } else if (!line.trim()) flush();
    else if ((m = line.match(/^#{1,6}\s+(.*)$/))) { flush(); html.push(`<p class="mdh" role="heading" aria-level="3">${inline(m[1])}</p>`); }
    else if (/^\s*([-*_])\s*(\1\s*){2,}$/.test(line)) { flush(); html.push('<hr>'); }
    else if (line.includes('|') && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(lines[i + 1])) {
      flush();
      const head = cells(line), rows = [];
      for (i += 2; i < lines.length && lines[i].includes('|') && lines[i].trim(); i++) rows.push(cells(lines[i]));
      i--;
      html.push(`<div class="tw"><table><thead><tr>${head.map((c) => `<th>${inline(c)}</th>`).join('')}</tr></thead><tbody>`
        + rows.map((r) => `<tr>${head.map((_, k) => `<td>${inline(r[k] ?? '')}</td>`).join('')}</tr>`).join('') + '</tbody></table></div>');
    } else if ((m = line.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/))) {
      const it = { tag: /\d/.test(m[2]) ? 'ol' : 'ul', d: Math.min(m[1].replace(/	/g, '    ').length, 12), text: m[3] };   // at most twelve levels
      if (list && list[0].tag !== it.tag && it.d <= list[0].d) flush();
      (list ||= []).push(it);
    } else if ((m = line.match(/^\s*>\s?(.*)$/))) { if (!quote.length) flush(); quote.push(m[1]); }
    else { if (list || quote.length) flush(); para.push(line.trim()); }
  }
  flush();
  return html.join('');
}

const settled = new Map();   // a settled answer is rendered once, not at every poll
const markdown = (src) => {
  let html = settled.get(src);
  if (html === undefined) { html = renderMarkdown(src); settled.set(src, html); if (settled.size > 300) settled.delete(settled.keys().next().value); }
  return html;
};
const withCursor = (html) => (/<\/(p|li)>$/.test(html) ? html.replace(/<\/(p|li)>$/, '<span class="ag-cur"></span></$1>') : `${html}<span class="ag-cur"></span>`);

// ---------------------------------------------------------------- the seams for the feature parts (see the top of this file)
const WORD = (kind) => L(`wait.word_${['request', 'question', 'plan'].includes(kind) ? kind : 'other'}`);
const handlers = {};   // action -> [fn]: any number of parts may answer the same click
const COCO = {
  h: {
    esc, wb, inline, markdown, render: renderMarkdown, ic, CH, L, E,
    icon: (name, paths) => { ICONS[name] = paths; },
    btn: (label, o = {}) => `<button type="button" class="${o.cls || 'b'}${o.off ? ' ag-off' : ''}" data-a="${esc(o.a || '')}"${o.id == null ? '' : ` data-id="${esc(o.id)}"`}${o.off ? ' aria-disabled="true"' : ''}>${o.html ? label : esc(label)}</button>`,
    fold: (key, off, on, html, o = {}) => `<details class="ag-ev${o.cls ? ` ${o.cls}` : ''}" data-k="${esc(key)}" data-d="${o.open ? '1' : '0'}"><summary>${CH}<span class="off">${esc(off)}</span><span class="on">${esc(on)}</span></summary>${html}</details>`,
    kicker: (more) => (more && more.count > 1 ? `<p class="ag-kk">${E('wait.first_of', { count: Number(more.count), next: WORD(more.next) })}</p>` : ''),
    shell: (o) => `<div class="ag-ask" role="group" aria-label="${esc(o.name)}" data-k="${esc(o.key)}">${o.kicker || ''}<p class="ag-q">${esc(o.title)}</p>${o.body || ''}${o.acts || ''}</div>`,
    blocks: (list, x) => blocksHtml(list, x),
    request: (r, answered, x) => requestHtml(r, answered, x),
  },
  thread: {}, lead: [], block: {}, wait: {}, pill: { question: 'aw', plan: 'aw' }, panel: {}, collect: { send: [], allow: [], decline: [], connect: [] },
  on: (action, fn) => { (handlers[action] ||= []).push(fn); },
  local: new Set(),   // options of view.options that only this window applies: a click on their switch sends nothing
  decorate: { user: [], queued: [], answer: [], step: [], system: [], request: [] },
  menu: [], strip: [], composer: [], sendable: [], takeover: [], footer: [], empty: [], confirm: [], init: [], after: [], input: [], change: [], escape: [],
  state: (name) => ((store().parts ||= {})[name] ||= {}),
};
const promptOf = (p) => (typeof p === 'string' ? { title: p, text: p, fill: false } : p || {});   // a first-screen prompt: a text, or {title, text, fill}
const safe = (fn, dflt) => { try { return fn(); } catch (e) { globalThis.console?.error('CoCo part', e); return dflt; } };   // a part that throws costs that part only
const part = (name, fn) => { try { fn(COCO, name); } catch (e) { globalThis.console?.error(`CoCo part ${name}`, e); } };   // a part that fails to register costs that part only
const blocksHtml = (blocks, cx) => (Array.isArray(blocks) ? blocks : []).map((b) => (b && COCO.block[b.type] ? safe(() => COCO.block[b.type](b, cx), '') : '')).join('');
const deco = (slot, item, cx, parts) => {
  const d = { cls: '', inner: '', parts };
  COCO.decorate[slot].forEach((f) => safe(() => f(item, cx, d)));
  return d;
};

// ---------------------------------------------------------------- the view, as markup
const fmtElapsed = (s) => (s < 60 ? L('time.seconds', { s: Math.floor(s) }) : L('time.minutes', { m: Math.floor(s / 60), s: Math.floor(s % 60) }));

function stepHtml(s, now, key, cx) {
  const state = ['run', 'ok', 'bad', 'no'].includes(s.state) ? s.state : 'ok';
  const glyph = state === 'run' ? '<span class="ag-run" aria-hidden="true"></span>' : ic(state);
  const word = L({ run: 'step.running', ok: 'step.completed', bad: 'step.failed', no: 'step.not_run' }[state]);
  let started = Number(s.started) || 0;
  if (started > 1e11) started /= 1000;
  const waited = state === 'run' ? Number(s.elapsed) || (started ? now - started : 0) : 0;
  const notes = [s.note, s.reason, waited > 30 ? L('step.so_far', { time: fmtElapsed(waited) }) : ''].filter(Boolean).map((n) => `<span class="ag-n">${esc(n)}</span>`).join('');
  const input = typeof s.input === 'string' ? s.input : s.input && typeof s.input.command === 'string' && Object.keys(s.input).length === 1 ? s.input.command : s.input && Object.keys(s.input).length ? JSON.stringify(s.input, null, 2) : '';
  const d = deco('step', s, cx, { tool: s.tool ? `<p class="cap">${esc(s.tool)}</p>` : '', input: input ? `<pre class="pre">${esc(input)}</pre>` : '',
    result: blocksHtml(s.blocks, cx) || (s.result ? `<p class="cap">${E('step.result')}</p><pre class="pre">${esc(s.result)}</pre>` : ''), allowed: s.allowed ? `<p class="cap">${E('step.allowed_by_you')}</p>` : '' });
  const detail = d.parts.tool + d.parts.input + d.parts.result + d.parts.allowed + d.inner;
  return `<details class="ag-step st-${state}${d.cls}" data-k="${esc(key)}" data-d="0"><summary><span class="ag-g">${glyph}</span><span class="ag-tx"><span class="ag-d">${esc(s.label)}</span>`
    + `<span class="sr">, ${esc(word)}</span>${notes}</span>${CH}</summary><div class="ag-det">${detail}</div></details>`;
}
const rowHtml = (s, now, key, cx) => {   // a step, or the item of a kind a part draws inside a section (reasoning)
  const own = COCO.thread[s.kind];
  return own ? ((safe(() => own(s, cx)) || {}).html || '') : stepHtml(s, now, key, cx);
};

function requestHtml(r, answered, cx) {
  const ch = r.kind === 'change' && r.changes;
  const change = ch && (typeof ch === 'string' ? ch : ch.file), howMuch = ch && typeof ch === 'object' ? ch.note : '';
  const label = r.evidence_label || L(change ? 'request.show_change' : 'request.show_command');
  const proof = Array.isArray(r.evidence) ? r.evidence : r.evidence ? [{ text: r.evidence }] : [];
  const off = esc(label), on = esc(label.replace(/^Show/, 'Hide'));
  const row = (k, v, w) => `<span class="k">${k}</span><span class="v${w ? ' w' : ''}">${wb(v)}</span>`;
  const dis = answered ? ' disabled' : '';
  const d = deco('request', r, cx, { kicker: COCO.h.kicker(((cx.view || {}).wait || {}).more), extra: '', allow: E('request.allow'), decline: E('request.decline') });
  return `<div class="ag-ask${d.cls}" role="group" aria-label="${E('request.group', { question: r.question })}" data-k="req:${esc(r.id)}"><div class="ag-bd">${d.parts.kicker}<p class="ag-q">${esc(r.question)}</p>`
    + `<div class="ag-fx">${r.where ? row(E('request.where'), r.where) : ''}${r.reads ? row(E('request.reads'), r.reads) : ''}${change ? row(E('request.changes'), change, true) : ''}${howMuch ? row(E('request.how_much'), howMuch) : ''}</div>`
    + (proof.length ? `<details data-k="ev:${esc(r.id)}" data-d="0" data-n="${proof.length}"><summary>${CH}<span class="off">${off}</span><span class="on">${on}</span></summary>${proof.map((p) => `${p.label && proof.length > 1 ? `<p class="cap">${esc(p.label)}</p>` : ''}<pre class="pre">${esc(p.text)}</pre>`).join('')}</details>` : '')
    + `</div>${d.parts.extra}<div class="ag-acts"><button class="b k big" data-a="allow" data-id="${esc(r.id)}"${dis}>${d.parts.allow}</button><button class="b big" data-a="decline" data-id="${esc(r.id)}"${dis}>${d.parts.decline}</button></div>${d.inner}</div>`;
}

function threadItems(view, now, cx) {
  const items = [];
  const running = (s) => s && s.state === 'run';
  let last = null;
  COCO.lead.forEach((f) => { const r = safe(() => f(view, cx)); if (r) items.push(r); });
  (view.thread || []).forEach((it, n) => {
    last = it;
    if (it.kind === 'user') {
      const d = deco('user', it, cx, { text: esc(it.text) });
      items.push({ k: `u:${it.id}`, html: `<div class="msg me${d.cls}" data-k="u:${esc(it.id)}"><span class="sr">${E('thread.you')}</span>${d.parts.text}${d.inner}</div>` });
    }
    else if (it.kind === 'scope') items.push({ k: `sc:${n}`, html: `<p class="cap" data-k="sc:${n}">${esc(it.text)}</p>` });
    else if (it.kind === 'step') items.push({ k: `s:${it.id}`, html: stepHtml(it, now, `s:${it.id}`, cx) });
    else if (it.kind === 'steps') {
      const list = it.items || [], said = it.summary;   // said: the sentence CoCo said before the group, its summary
      if (!list.length) { if (said) items.push({ k: `n:${it.id}`, html: `<p class="ag-nar" data-k="n:${esc(it.id)}">${inline(said)}</p>` }); return; }   // a sentence alone is not a trail
      if (list.length === 1 && !said) { items.push({ k: `g:${it.id}`, html: rowHtml(list[0], now, `s:${list[0].id}`, cx).replace(/data-k="[^"]*"/, `data-k="g:${esc(it.id)}"`) }); return; }   // a lone step is its own summary
      const rows = list.map((row, j) => rowHtml(row, now, `s:${row.id ?? `${it.id}.${j}`}`, cx)).join('');
      const fold = it.folded ? '0' : '1';
      items.push({ k: `g:${it.id}`, html: `<details class="ag-trail" data-k="g:${esc(it.id)}" data-d="${fold}"><summary><span class="ag-tx">${said ? inline(said) : E('thread.steps', { n: list.length })}</span>${CH}</summary><div class="ag-rows">${rows}</div></details>` });
    } else if (it.kind === 'answer') {
      if (!it.text && it.streaming) return;
      const copy = it.streaming ? '' : `<button class="ag-cp" data-a="copy" data-id="a:${esc(it.id)}" aria-label="${E('thread.copy_answer')}">${ic('copy', 'i s')}</button>`;
      const d = deco('answer', it, cx, { text: it.streaming ? withCursor(renderMarkdown(it.text)) : markdown(it.text), blocks: blocksHtml(it.blocks, cx), copy });
      items.push({ k: `a:${it.id}`, html: `<div class="msg md${it.streaming ? '' : ' ag-cpy'}${d.cls}"${it.streaming ? ' aria-busy="true"' : ''} data-k="a:${esc(it.id)}"><span class="sr">${E('thread.coco')}</span>${d.parts.text}${d.parts.blocks}${d.parts.copy}${d.inner}</div>` });
    } else if (it.kind === 'draft') {
      const title = it.title ? `<b>${esc(it.title)}</b>\n` : '';
      items.push({ k: `d:${it.id}`, html: `<div class="msg ag-cpy ag-draft" data-k="d:${esc(it.id)}">${title}${esc(it.text)}<button class="ag-cp" data-a="copy" data-id="d:${esc(it.id)}" aria-label="${E('thread.copy_draft')}${it.title ? ` ${esc(it.title.replace(/^To\s+/i, L('thread.draft_to')))}` : ''}">${ic('copy', 'i s')}</button></div>` });
    } else if (it.kind === 'system') {
      const retry = it.action === 'retry' ? `<button class="b sm" data-a="retry">${E('common.try_again')}</button>`
        : it.action && it.action.label ? `<button class="b sm" data-a="system_action" data-id="${esc(it.id)}">${esc(it.action.label)}</button>` : '';
      const more = it.detail ? `<details data-k="yd:${n}" data-d="0"><summary>${E('common.show_details')}</summary><pre class="pre">${esc(it.detail)}</pre></details>` : '';
      const d = deco('system', it, cx, { text: esc(it.text), button: retry });
      items.push({ k: `y:${n}`, html: `<div class="ag-sys${d.cls}" role="status" data-k="y:${n}"><div><span>${d.parts.text}</span>${d.parts.button}</div>${more}${d.inner}</div>` });
    } else if (COCO.thread[it.kind]) { const r = safe(() => COCO.thread[it.kind](it, cx, n)); if (r) items.push(r); }
  });
  const busy = (view.thread || []).some((it) => (it.kind === 'step' && running(it)) || (it.kind === 'steps' && (it.items || []).some(running)));
  const speaking = last && last.kind === 'answer' && last.streaming && last.text;
  if (view.status === 'working' && !busy && !speaking && !view.request) items.push({ k: 'dots', html: `<div class="msg ty" role="status" aria-label="${E('thread.working')}" data-k="dots"><i></i><i></i><i></i></div>` });
  (view.queue || []).forEach((q) => {
    const short = q.text.length > 40 ? `${q.text.slice(0, 40)}...` : q.text;
    const d = deco('queued', q, cx, { text: esc(q.text) });
    items.push({ k: `q:${q.id}`, html: `<div class="msg me ag-qd${d.cls}" data-k="q:${esc(q.id)}"><span class="sr">${E('thread.you')}</span>${d.parts.text}<span class="ag-n">${esc(q.note || L('queue.queued'))}<button class="tk" data-a="unqueue" data-id="${esc(q.id)}" aria-label="${E('queue.take_back_for', { text: short })}">${E('queue.take_back')}</button></span>${d.inner}</div>` });
  });
  return items;
}

function patchList(parent, items, applyOpen) {
  const have = new Map([...parent.children].map((c) => [c.dataset.k, c]));
  let prev = null;
  const added = [];
  for (const it of items) {
    let node = have.get(it.k);
    have.delete(it.k);
    if (!node || node._h !== it.html) {
      const t = parent.ownerDocument.createElement('template');
      t.innerHTML = it.html;
      const fresh = t.content.firstElementChild;
      fresh._h = it.html;
      if (node && node.classList.contains('md') && node.className === fresh.className) {   // a streaming answer: only the blocks after the first change are touched
        const old = [...node.children], now = [...fresh.children];
        let n = 0;
        while (n < old.length && n < now.length && old[n].isEqualNode(now[n])) n++;
        old.slice(n).forEach((c) => c.remove());
        node.append(...now.slice(n));
        node._h = it.html;
      } else {
        if (node) node.replaceWith(fresh);
        node = fresh;
        added.push(node);
      }
    }
    const want = prev ? prev.nextElementSibling : parent.firstElementChild;
    if (node !== want) parent.insertBefore(node, want);
    prev = node;
  }
  for (const n of have.values()) n.remove();
  added.forEach(applyOpen);
}

// ---------------------------------------------------------------- the component
const store = () => (globalThis.__cocoUI ||= { open: false, draft: '', folds: {}, scroll: 0, seq: 0, out: [], inflight: null, stale: false, sess: '', token: 0, ack: 0, pend: {}, answered: {}, restored: '', announced: '', menu: false, confirm: '', panel: '', parts: {}, follow: { id: '', away: false } });
const hide = (n, h) => { if (n.hidden !== h) n.hidden = h; };
const attr = (n, k, v) => { if (n.getAttribute(k) !== v) n.setAttribute(k, v); };
const guard = (fn) => { try { return fn(); } catch { return undefined; } };

function build(root, shadow, spark) {
  const S = store();
  S.pend ||= {};
  const sparkSvg = (cls) => `<svg class="${cls}" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path fill="#5498FF" d="${spark}"/></svg>`;
  root.innerHTML = `<div class="sr" role="status" aria-live="polite" id="lv"></div><div class="sr" role="alert" id="al"></div>
    <button type="button" class="cl" data-a="open"><span class="lb" aria-hidden="true">${E('launcher.label')}</span><svg viewBox="1 1 30 30" fill="none" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="#16181D"/><path transform="translate(8 8)" fill="#5498FF" d="${spark}"/></svg></button>
    <section class="cc" role="dialog" aria-label="${E('dialog.label')}" tabindex="-1" hidden>
      <div class="hd">${sparkSvg('sk')}<div class="tt"><h2>${E('header.title')}</h2></div>
        <button type="button" class="ib" data-a="min" aria-label="${E('header.minimise')}">${ic('min')}</button>
        <button type="button" class="ib" data-a="menu" id="mb" aria-label="${E('header.menu')}" aria-haspopup="menu" aria-expanded="false">${ic('dots')}</button></div>
      <div class="ag-top" hidden></div>
      <div class="bd"><div class="emp" hidden></div><div class="thr" role="log" aria-relevant="additions" aria-label="${E('thread.label')}" hidden></div><div class="ag-tk" hidden></div></div>
      <div class="rq" hidden></div>
      <p class="cap ag-off" role="status" hidden>${E('offline')}</p>
      <div class="pop mn" role="menu" aria-label="${E('header.menu')}" hidden></div>
      <div class="ag-cf" role="alertdialog" aria-labelledby="cft" aria-describedby="cfd" hidden></div>
      <div class="ag-pan-host" hidden></div>
      <div class="ft"><div class="fix" hidden></div><div class="fld"><div class="ag-ftop" hidden></div><span class="ag-fleft" hidden></span><textarea rows="1" aria-label="${E('field.label')}" placeholder="${E('field.placeholder')}"></textarea><span class="sdw"></span></div></div>
    </section>`;
  const q = (s) => root.querySelector(s);
  const el = { lv: q('#lv'), al: q('#al'), cl: q('.cl'), lb: q('.cl .lb'), cc: q('.cc'), hd: q('.hd'), ft: q('.ft'), rq: q('.rq'), off: q('.ag-off'), bd: q('.bd'), emp: q('.emp'), thr: q('.thr'), menu: q('.mn'), mb: q('#mb'), cf: q('.ag-cf'), top: q('.ag-top'), tk: q('.ag-tk'), pan: q('.ag-pan-host'), ftop: q('.ag-ftop'), fleft: q('.ag-fleft'), fix: q('.fix'), fld: q('.fld'), ta: q('textarea'), sdw: q('.sdw') };
  const I = { root, view: null, set: () => {}, bar: null };
  const x = {   // the window as a part sees it (top of this file); the functions defined further down are reached lazily
    get view() { return I.view; }, root, shadow, el, S,
    send: (a) => send(a), announce: (text, assertive) => say(assertive ? el.al : el.lv, text), copy: (text, btn) => copy(text, btn), repaint: (focus) => paint(focus),
    settle: (id) => {   // the block is answered: the focus goes back to the field before its buttons are disabled
      S.answered[id] = true;
      if (el.rq.contains(shadow.activeElement) && !el.fld.hidden) el.ta.focus({ preventScroll: true });
      el.rq.querySelectorAll('.b').forEach((b) => { b.disabled = true; });
    },
    applyOpen: (node) => applyOpen(node), openPanel: (name) => { S.panel = name; S.menu = false; paint('.ag-pan .b'); }, closePanel: () => { S.panel = ''; paint('#mb'); },   // the focus goes into the panel, and back to the menu button
    opt: (id) => option(I.view || {}, id),
  };
  // a switch of view.options as shown: what was just pressed until the host has answered (a refusal puts the real state back), the window's own ones for good
  const option = (v, id) => { const o = (v.options || []).find((q) => q.id === id); return !!o && (id in S.pend ? S.pend[id].v : o.on); };
  const collect = (a, t) => Object.assign({}, ...(COCO.collect[a] || []).map((f) => safe(() => f(t, x)) || {}));
  // What the user has in front of them when the message leaves: the page's own text without the navigation rail (the
  // window lives in a shadow root, so it is not in it), an open dialog, and what they selected. Cut here, and again on
  // the server. Typing in the window takes the selection away from the page, so the last one made there is remembered.
  root.ownerDocument.addEventListener('selectionchange', () => {
    const doc = root.ownerDocument, host = root.getRootNode().host || root;
    if (doc.activeElement !== host) S.sel = String(doc.defaultView.getSelection() || '').trim();
  });
  const screen = () => {
    const doc = root.ownerDocument, text = (n) => (n ? n.innerText.replace(/\n{3,}/g, '\n\n').trim() : '');
    let main = text(doc.querySelector('[data-testid="stMain"]') || doc.body);
    EXCLUDE.forEach((sel) => { const t = guard(() => text(doc.querySelector(sel))); if (t) main = main.replace(t, ''); });
    return { text: main.trim().slice(0, 12000),
             dialog: text(doc.querySelector('[data-testid="stDialog"]')).slice(0, 4000),
             selection: (S.sel || '').slice(0, 2000) };
  };
  const send = (a) => {
    if (I.view && I.view.page_text && (a.a === 'send' || a.a === 'prompt')) a.screen = screen();
    const last = S.out.at(-1);
    const same = (p, o) => Object.keys({ ...p, ...o }).every((k) => k === 'seq' || k === 'screen' || JSON.stringify(p[k]) === JSON.stringify(o[k]));
    if (last && a.a !== 'send' && same(last, a)) return;   // a double click is one action
    a.seq = ++S.seq; S.out.push(a); pump();
  };
  const pump = () => {
    if (S.inflight || !S.out.length) return;
    S.inflight = { a: S.out[0], t: Date.now(), t0: Date.now() };
    I.set('act', S.inflight.a);
  };
  const say = (node, text) => { node.textContent = ''; requestAnimationFrame(() => { node.textContent = text; }); };
  const applyOpen = (node) => [node, ...node.querySelectorAll('details[data-k]')].forEach((d) => {
    if (d.tagName !== 'DETAILS') return;
    const o = S.folds[d.dataset.k], base = d.dataset.d === '1';
    d.open = o && o.base === base ? o.v : base;
  });

  // ------ opening, minimising, focus
  const seeIfOpen = () => {   // an answer or a failure is acknowledged once the window shows it; a request pill goes when it is answered
    const pill = I.view && I.view.pill;
    if (!pill || !S.open || pill.kind === 'request' || COCO.pill[pill.kind]) { if (!pill) S.seenPill = ''; return; }
    const key = `${pill.kind}:${pill.label}`;
    if (S.seenPill !== key) { S.seenPill = key; send({ a: 'seen' }); }
  };
  const setOpen = (open, focus = true) => {
    S.open = open;
    if (!open) { S.menu = false; S.confirm = ''; S.panel = ''; }
    paint();
    if (open) seeIfOpen();
    if (!focus) return;
    requestAnimationFrame(() => {
      if (open) { (!el.fld.hidden ? el.ta : el.cc.querySelector('.ft button, .emp button, .bd button') || el.cc).focus({ preventScroll: true }); }
      else el.cl.focus({ preventScroll: true });
    });
  };
  const sizeField = () => { if (!el.ta.getClientRects().length || el.ta._v === el.ta.value) return; el.ta._v = el.ta.value; el.ta.style.height = 'auto'; el.ta.style.height = `${Math.min(el.ta.scrollHeight, parseFloat(getComputedStyle(el.ta).maxHeight) || 999)}px`; el.ta.style.overflowY = el.ta.scrollHeight > el.ta.clientHeight + 1 ? 'auto' : 'hidden'; };   // scrolls only beyond its largest size

  const canSend = () => COCO.sendable.some((f) => safe(() => f(x), false));
  const answering = (v) => ['ready', 'working', 'waiting'].includes(v.status);
  const composer = (v) => answering(v) || (v.status === 'connecting' && !!v.type_ahead);   // the field is free while connecting when the host takes what is sent meanwhile
  // ------ the launcher: rest, hover, pill, pending arc, above an action bar
  const paintLauncher = (v) => {
    const pill = v.pill, cls = pill ? { request: 'aw', answer: 'dn', failed: 'er', ...COCO.pill }[pill.kind] || '' : '';
    const intro = S.introOn && !pill && v.status !== 'working';
    attr(el.cl, 'class', `cl${cls ? ` ${cls}` : ''}${!pill && v.status === 'working' ? ' pn' : ''}${intro ? ' ex' : ''}${answering(v) ? '' : ' off'}`);   // off: CoCo cannot answer
    const label = pill ? pill.label : L('launcher.label');
    if (el.lb.textContent !== label) el.lb.textContent = label;
    const name = pill ? (pill.name ? L('launcher.pill_named', { label: pill.label, name: pill.name }) : pill.label) : v.status === 'working' ? L('launcher.working') : L('launcher.label');
    attr(el.cl, 'aria-label', name);
    if (pill && pill.name) el.cl.title = name; else el.cl.removeAttribute('title');
  };

  // ------ the window
  const paintFooter = (v) => {
    const st = v.status, profiles = v.profiles || [];
    let fix = '';
    if (st === 'not_installed') {
      const set = v.setup || {}, pkg = set.missing !== 'program';
      fix = `<details><summary>${E('footer.missing')}</summary><p class="cap">${pkg ? E('footer.package_missing') : esc(set.command)}</p>${pkg ? `<pre class="pre">${esc(set.command)}</pre>` : ''}</details>`;
    }
    else if (st === 'not_connected') {
      const choose = profiles.length > 1;
      const sel = S.profile && profiles.includes(S.profile) ? S.profile : v.profile && profiles.includes(v.profile) ? v.profile : profiles[0];
      fix = (choose ? `<div class="selw"><select class="in" aria-label="${E('footer.profile')}">${profiles.map((p) => `<option${p === sel ? ' selected' : ''}>${esc(p)}</option>`).join('')}</select>${ic('chev', 'i s')}</div>` : '')
        + (profiles.length ? `<button type="button" class="b k" data-a="connect"${choose ? '' : ` data-id="${esc(profiles[0])}"`}>${choose ? E('footer.connect') : E('footer.connect_to', { profile: profiles[0] })}</button>` : '');
    } else if (st === 'lost') fix = `<button type="button" class="b k" data-a="reconnect">${E('footer.reconnect')}</button>`;
    COCO.footer.forEach((f) => { const r = safe(() => f(v, x, fix)); if (typeof r === 'string') fix = r; });
    const isFix = !composer(v) && !!fix, hadFocus = shadow.activeElement === el.ta;
    hide(el.fix, !isFix); hide(el.fld, !composer(v)); hide(el.ft, !isFix && !composer(v));
    if (el.fix._h !== fix) { el.fix.innerHTML = fix; el.fix._h = fix; }
    if (!composer(v)) { if (hadFocus) (el.fix.querySelector('button, select') || el.cc).focus({ preventScroll: true }); return; }   // the field went away: keep the focus inside the window
    sizeField();
    const slot = (name) => COCO.composer.map((c) => (c[name] ? safe(() => c[name](v, x), '') : '')).join(''), top = slot('top'), left = slot('left');
    [[el.ftop, top], [el.fleft, left]].forEach(([node, html]) => { hide(node, !html); if (node._h !== html) { node.innerHTML = html; node._h = html; } });
    const fcls = COCO.composer.map((c) => (c.cls ? safe(() => c.cls(v, x), '') : '')).filter(Boolean).join(' ');
    attr(el.fld, 'class', fcls ? `fld ${fcls}` : 'fld');
    const held = !!v.send_held, ready = !held && (!!el.ta.value.trim() || canSend());
    const btn = st === 'working' ? `<button type="button" class="sd st" data-a="stop" aria-label="${E('field.stop')}"><span class="arc" aria-hidden="true"></span>${ic('stop', 'i s')}</button>`
      : `<button type="button" class="sd${ready ? ' on' : ''}" data-a="send" aria-label="${E('field.send')}"${ready ? '' : ' aria-disabled="true"'}>${ic('send', 'i s')}</button>`;   // always there: quiet while empty
    if (el.sdw._h !== btn) { el.sdw.innerHTML = btn; el.sdw._h = btn; }
    attr(el.ta, 'placeholder', L(v.send_held ? 'field.held' : st === 'working' ? 'field.ahead_working' : st === 'waiting' ? 'field.ahead_waiting' : 'field.placeholder'));
  };
  const paintBody = (v, opening, tk) => {
    const st = v.status, hasThread = (v.thread || []).length || (v.queue || []).length;
    let emp = '';
    if (!hasThread) {
      if (st === 'ready') emp = `<p class="t">${E('first.title')}</p><p class="cap">${E('first.sub')}</p><div class="pps">${(v.prompts || []).map((p, i) => { const o = promptOf(p); return `<button type="button" class="pp" data-a="prompt" data-i="${i}"${o.text !== o.title ? ` title="${esc(o.text)}"` : ''}>${esc(o.title)}${ic('arr', 'i s')}</button>`; }).join('')}</div>`;
      else if (st === 'not_installed') emp = `<p class="t">${E('first.not_installed')}</p><p class="cap">${E('first.not_installed_sub')}</p>`;
      else if (st === 'connecting') emp = `<p class="t"><span class="dot3" aria-hidden="true"></span>${E('first.connecting', { profile: v.profile || L('first.your_account') })}</p>`;
      else if (st === 'lost') emp = `<p class="t">${E('first.lost')}</p>`;
      else if (st === 'not_connected') {
        const n = (v.profiles || []).length;
        emp = v.error && n ? `<p class="t" role="alert">${ic('bad')}${v.profile ? E('first.could_not_connect_to', { profile: v.profile }) : E('first.could_not_connect')}</p><p class="cap">${E(n > 1 ? 'first.choose_or_retry' : 'first.retry')}</p><div class="fix"><details><summary>${E('common.show_details')}</summary><pre class="pre">${esc(v.error)}</pre></details></div>`
          : n === 0 ? `<p class="t">${E('first.no_connection')}</p><div class="fix"><details><summary>${E('first.where')}</summary><p class="cap">${E('first.where_answer')}</p></details></div>`
          : `<p class="t">${E(n > 1 ? 'first.choose' : 'first.connect')}</p><p class="cap">${E('first.works_with')}</p>`;
      }
    }
    COCO.empty.forEach((f) => { const r = safe(() => f(v, x, emp)); if (typeof r === 'string') emp = r; });
    el.bd.classList.toggle('conv', !!hasThread);
    hide(el.emp, !emp || tk); hide(el.thr, !hasThread || tk);
    if (el.emp._h !== emp) { el.emp.innerHTML = emp; el.emp._h = emp; }
    if (hasThread) {
      const quiet = !el.thr.childElementCount || opening;   // the history shown at once is not read out: only what arrives afterwards
      if (quiet) attr(el.thr, 'aria-live', 'off');
      patchList(el.thr, threadItems(v, Date.now() / 1000, x), applyOpen); followAnswer(v);
      if (quiet) requestAnimationFrame(() => el.thr.removeAttribute('aria-live'));
    }
  };
  const paintRequest = (v, claimed) => {
    const w = v.wait && v.wait.kind !== 'request' ? v.wait : null, r = w ? null : v.request, kind = w && COCO.wait[w.kind];
    const html = kind ? safe(() => kind.html(w, x), '') || '' : r ? requestHtml(r, S.answered[r.id], x) : '';
    hide(el.rq, !html || claimed);
    if (el.rq._h !== html) {
      const f = shadow.activeElement, mark = f && el.rq.contains(f) && f.dataset ? f.dataset.f : '', at = mark ? f.selectionStart : null;   // a repaint keeps the focus of what is typed into
      el.rq.innerHTML = html; el.rq._h = html; applyOpen(el.rq);
      const n = mark && el.rq.querySelector(`[data-f="${CSS.escape(mark)}"]`);
      if (n) { n.focus({ preventScroll: true }); guard(() => n.setSelectionRange(at, at)); }
    }
  };
  const paintStrip = (v) => {
    const html = COCO.strip.map((f) => safe(() => f(v, x), '')).join('');
    hide(el.top, !html);
    if (el.top._h !== html) { el.top.innerHTML = html; el.top._h = html; applyOpen(el.top); }
  };
  const paintPanel = (v) => {
    const make = S.panel && COCO.panel[S.panel], html = make ? safe(() => make(v, x), '') || '' : '';
    if (S.panel && !html) S.panel = '';   // what it showed is gone
    hide(el.pan, !html);
    if (el.pan._h !== html) { el.pan.innerHTML = html; el.pan._h = html; applyOpen(el.pan); }
  };
  const paintTakeover = (v) => {   // returns the takeover when one replaces the thread
    const t = COCO.takeover.map((f) => safe(() => f(v, x))).find(Boolean) || null, cls = t && t.cls ? t.cls : '';
    if (el.cc._tk !== cls) { if (el.cc._tk) el.cc.classList.remove(...el.cc._tk.split(' ')); if (cls) el.cc.classList.add(...cls.split(' ')); el.cc._tk = cls; }
    hide(el.tk, !t);
    if (t && el.tk._h !== t.html) { el.tk.innerHTML = t.html; el.tk._h = t.html; applyOpen(el.tk); }
    return t;
  };
  // a long answer: the view follows it only until its top reaches the top of the thread, then stays; a user who scrolled is not moved
  const followAnswer = (v) => {
    const last = (v.thread || []).at(-1);
    if (!last || last.kind !== 'answer') return;
    if (S.follow.id !== last.id) {
      if (!last.streaming) return;
      S.follow = { id: last.id, away: el.bd.scrollTop < -40 };
    }
    const node = !S.follow.away && el.thr.querySelector(`[data-k="a:${last.id}"]`);
    if (node) {
      const rem = parseFloat(getComputedStyle(root).fontSize) || 14;
      const over = el.bd.getBoundingClientRect().top + rem * 0.5 - node.getBoundingClientRect().top;
      if (over > 0) el.bd.scrollTop -= over;
    }
    if (!last.streaming) S.follow = { id: '', away: false };
  };
  // what a rebuilt button is found again by: the focus is given back to it (a menu line, Show all)
  const sig = (n) => (n && n.dataset && n.dataset.a ? `[data-a="${CSS.escape(n.dataset.a)}"]${['id', 'i', 'opt', 'file'].map((k) => (n.dataset[k] == null ? '' : `[data-${k}="${CSS.escape(n.dataset[k])}"]`)).join('')}` : '');
  const paintMenu = (v) => {
    const live = ['ready', 'working', 'waiting', 'lost'].includes(v.status), has = (v.thread || []).length || (v.queue || []).length || v.status === 'working';
    const more = COCO.menu.map((m, i) => ({ m, i })).sort((p, q) => (p.m.order ?? 50) - (q.m.order ?? 50) || p.i - q.i).map(({ m }) => guard(() => m.items(v, x)) || '').join('');
    const switches = (v.options || []).map((o) => {
      const on = option(v, o.id);
      return `<button type="button" class="it" role="menuitemcheckbox" aria-checked="${on}" data-a="set" data-opt="${esc(o.id)}"><span class="ag-sl${on ? ' on' : ''}" aria-hidden="true">${on ? ic('ok', 'i') : ''}</span>`
        + `<span>${esc(o.label)}${o.sub ? `<span class="ag-sub">${esc(o.sub)}</span>` : ''}</span></button>`;
    }).join('');
    const sub = (text) => (more || switches ? `<span class="ag-sub">${esc(text)}</span>` : '');   // with the other lines, the first two say what they do (frame 60)
    const core = (has ? `<button type="button" class="it" role="menuitem" data-a="new">${ic('plus', 'i s')}<span>${E('menu.new')}</span></button>` : '')
      + (live ? `<button type="button" class="it" role="menuitem" data-a="disc">${ic('out', 'i s')}<span>${E('menu.disconnect')}${sub(v.profile || '')}</span></button>` : '');
    const all = [core, switches, more].filter(Boolean).join('<hr>');
    if (el.menu._h !== all) {
      const had = el.menu.contains(shadow.activeElement) ? sig(shadow.activeElement) : '';
      S.rebuild = true;   // the focus leaving a line that is being replaced is not the user leaving the menu
      el.menu.innerHTML = all; el.menu._h = all;
      if (had) el.menu.querySelector(had)?.focus({ preventScroll: true });
      S.rebuild = false;
    }
    el.menu.classList.toggle('ag-mw', !!(more || switches));
    hide(el.mb, !all);
    const open = S.menu && !!all;
    hide(el.menu, !open); attr(el.mb, 'aria-expanded', String(open));
  };
  const paintConfirm = (v) => {
    [el.hd, el.top, el.bd, el.rq, el.ft, el.menu, el.pan].forEach((n) => { if (n.inert !== !!S.confirm) n.inert = !!S.confirm; });   // nothing else can be activated, by mouse or keyboard
    if (!S.confirm) { hide(el.cf, true); return; }
    const changed = (v.thread || []).some((it) => [it, ...(it.items || [])].some((x) => x.kind === 'step' && x.state === 'ok' && ['edit', 'write'].includes(String(x.tool).toLowerCase())));
    const said = [v.status === 'working' ? L('confirm.stops') : '', v.request ? L('confirm.request') : '',
      (v.queue || []).length ? L(v.queue.length === 1 ? 'confirm.queued_one' : 'confirm.queued_other', { n: v.queue.length }) : '', changed ? L('confirm.changed') : '',
      ...COCO.confirm.map((f) => safe(() => f(v, S.confirm), ''))].filter(Boolean).join(' ');
    const disc = S.confirm === 'disc';
    const html = `<p class="ag-q" id="cft">${disc ? E('confirm.disconnect_title', { profile: v.profile || L('confirm.your_account') }) : E('confirm.new_title')}</p>`
      + `<p class="ag-cft" id="cfd">${E(disc ? 'confirm.forgets_disconnect' : 'confirm.forgets_new')} ${esc(said)}</p>`
      + `<div class="ag-acts"><button type="button" class="b k sm" data-a="${disc ? 'disc!' : 'new!'}">${E(disc ? 'confirm.disconnect_do' : 'confirm.new_do')}</button><button type="button" class="b sm" data-a="keep">${E(disc ? 'confirm.disconnect_keep' : 'confirm.new_keep')}</button></div>`;
    if (el.cf._h !== html) { el.cf.innerHTML = html; el.cf._h = html; }
    hide(el.cf, false);
  };
  const paint = (focus) => {
    const v = I.view;
    if (!v) return;
    const back = el.cl.hidden && !S.open;
    paintLauncher(v);
    hide(el.cl, S.open);
    if (back) { el.cl.className = el.cl.className.replace(/ (aw|dn|er|ex)/g, ''); void el.cl.offsetWidth; requestAnimationFrame(() => paintLauncher(I.view)); }   // coming back from the window: a pill grows from the disc, it does not appear open
    const opening = el.cc.hidden && S.open;
    hide(el.cc, !S.open);
    if (!S.open) return;
    const was = shadow.activeElement, wasSig = sig(was);
    paintMenu(v); paintConfirm(v); paintStrip(v);
    const tk = paintTakeover(v);
    paintBody(v, opening, !!tk); paintRequest(v, !!(tk && tk.claims)); paintPanel(v); paintFooter(v); paintOff();
    COCO.after.forEach((f) => safe(() => f(v, x)));
    if (was && !was.isConnected && wasSig) shadow.querySelector(wasSig)?.focus({ preventScroll: true });   // a button that was rebuilt
    if (focus) shadow.querySelector(focus)?.focus({ preventScroll: true });
    if (was && (!was.isConnected || was === el.cc) && (!shadow.activeElement || shadow.activeElement === el.cc)) (!el.fld.hidden ? el.ta : el.cc).focus({ preventScroll: true });   // what had the focus is gone: keep it in the window
  };

  // ------ a view arrives
  // The texts build() wrote once follow the host's labels: an application may change them between two runs (another language).
  const shell = () => {
    [[el.cc, 'dialog.label'], [q('[data-a=min]'), 'header.minimise'], [q('[data-a=rail]'), 'header.rail'], [el.mb, 'header.menu'], [el.menu, 'header.menu'], [el.thr, 'thread.label'], [el.ta, 'field.label']].forEach(([n, k]) => { if (n) attr(n, 'aria-label', L(k)); });
    [[q('.hd h2'), 'header.title'], [el.off, 'offline']].forEach(([n, k]) => { if (n.textContent !== L(k)) n.textContent = L(k); });
  };
  const placeRail = (on) => {
    let btn = q('[data-a=rail]');
    if (!on) { if (btn) btn.remove(); return; }
    if (!btn) q('[data-a=min]').insertAdjacentHTML("beforebegin", `<button type="button" class="ib" data-a="rail" aria-label="${E('header.rail')}">${ic('rail')}</button>`);
  };
  I.update = (data) => {
    placeRail(!!data.rail);
    shell();
    const v = data.view || {};
    const first = !I.view;
    I.view = v;
    if (data.sess !== S.sess) {   // the Cockpit forgot this window (restart): what was still on its way was meant for a conversation that no longer exists; a message goes back into the field
      const lost = S.out.filter((a) => a.a === 'send').map((a) => a.text);
      if (S.sess && lost.length) { S.draft = [...lost, S.draft].filter(Boolean).join('\n'); el.ta.value = S.draft; }
      if (S.sess) { S.out = []; S.inflight = null; }
      S.sess = data.sess;
    }
    if (S.inflight && Number(data.ack) >= S.inflight.a.seq) { S.out.shift(); S.inflight = null; }
    S.ack = Math.max(S.ack, Number(data.ack) || 0);
    Object.keys(S.pend).forEach((id) => { if (S.pend[id].seq && S.pend[id].seq <= S.ack) delete S.pend[id]; });   // the host has answered: its state is the switch's
    S.stale = false;
    if (Number(data.open_token) > S.token) { S.token = Number(data.open_token); if (!S.open) { S.open = true; S.openFocus = true; } }
    if (v.restore && S.restored !== `${v.rev}:${v.restore}`) {
      S.restored = `${v.rev}:${v.restore}`;
      el.ta.value = el.ta.value.trim() ? `${v.restore}\n${el.ta.value}` : v.restore; S.draft = el.ta.value;
    }
    const w = v.wait && v.wait.kind !== 'request' ? v.wait : null, wid = w ? w.id : v.request ? v.request.id : null;
    S.answered = wid ? { [wid]: S.answered[wid] } : {};
    const key = v.request ? `r:${v.request.id}` : w ? `w:${w.id}` : v.pill ? `p:${v.pill.kind}:${v.pill.label}` : '';
    if (key && key !== S.announced) {
      S.announced = key;
      const text = v.request ? L('announce.asks', { question: v.request.question, where: v.request.where || '' }) : w ? (safe(() => (COCO.wait[w.kind] || {}).announce?.(w)) || L('announce.waiting')) : `${v.pill.label}`;
      say(v.request || w ? el.al : el.lv, text);
    }
    if (!key) S.announced = '';
    paint();
    if (first) { el.ta.value = S.draft; sizeField(); if (S.open) el.bd.scrollTop = S.scroll; if (S.open) paint(); if (S.inflight) { S.inflight.t0 = Date.now(); I.set('act', S.inflight.a); } }   // new window, same page change: what was sent may not have arrived
    if (S.openFocus) { S.openFocus = false; requestAnimationFrame(() => (!el.fld.hidden ? el.ta : el.cc).focus({ preventScroll: true })); }
    seeIfOpen();
    pump();
    arm();
  };

  // ------ polling: only while there is something to wait for; a tab nobody looks at asks less, and asks at once when shown
  const arm = () => {
    clearTimeout(S.timer);
    const v = I.view || {}, wait = { working: 350, waiting: 2000, connecting: 800 }[v.status];
    if (!wait && !S.inflight) return;
    S.timer = setTimeout(() => {
      if (!root.isConnected) return;
      const f = S.inflight, now = Date.now();
      if (f && now - f.t > 4000) { f.t = now; I.set('act', f.a); }   // lost on the way: the server ignores a repeat
      else if (!f && !S.out.length && wait) send({ a: 'poll' });
      if (!!f && now - f.t0 > 8000 !== S.stale) { S.stale = !S.stale; paintOff(); }   // no answer for a while: the window says so
      arm();
    }, Math.max(wait || 1000, root.ownerDocument.hidden ? 2000 : 0));
  };
  const paintOff = () => hide(el.off, !S.stale || !S.open);
  root.ownerDocument.addEventListener('visibilitychange', () => { if (!root.ownerDocument.hidden && root.isConnected && !S.inflight && !S.out.length && ['working', 'waiting', 'connecting'].includes((I.view || {}).status)) send({ a: 'poll' }); arm(); });

  // ------ the action bar of the page: the launcher and the window clear it by 1rem
  const clearBar = () => {
    if (!root.isConnected) return;
    const doc = root.ownerDocument;
    const bar = (AVOID ? guard(() => [...doc.querySelectorAll(AVOID)]) || [] : []).find((b) => { const r = b.getBoundingClientRect(); return r.height > 0 && r.top > 0 && getComputedStyle(b).position === 'fixed'; });
    if (bar !== I.bar) { I.ro?.disconnect(); I.bar = bar || null; if (bar) (I.ro ||= new ResizeObserver(() => requestAnimationFrame(clearBar))).observe(bar); }
    const rem = parseFloat(getComputedStyle(doc.documentElement).fontSize) || 14;
    shadow.host.style.setProperty('--coco-bottom', bar ? `${Math.round(doc.defaultView.innerHeight - bar.getBoundingClientRect().top + rem)}px` : '');
  };
  let raf = 0;
  const later = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(clearBar); };
  new MutationObserver(later).observe(root.ownerDocument.body, { childList: true, subtree: true });
  root.ownerDocument.defaultView.addEventListener('resize', later);
  later();

  // ------ events
  const copy = async (text, btn) => {
    try { await navigator.clipboard.writeText(text); } catch {
      const t = root.ownerDocument.createElement('textarea'); t.value = text; root.appendChild(t); t.select(); guard(() => root.ownerDocument.execCommand('copy')); t.remove();
    }
    const was = btn.innerHTML, label = btn.getAttribute('aria-label');   // an icon button shows the tick, a text button says it, for a moment
    const done = L('common.copied'); btn.innerHTML = btn.querySelector('svg') ? ic('ok', 'i s') : esc(done); if (label) btn.setAttribute('aria-label', done); say(el.lv, done);
    setTimeout(() => { btn.innerHTML = was; if (label) btn.setAttribute('aria-label', label); }, 1500);
  };
  const doSend = () => {
    const text = el.ta.value.trim();
    if ((!text && !canSend()) || (I.view && I.view.send_held)) return;
    send({ a: 'send', text, ...collect('send', null) });
    el.ta.value = ''; S.draft = ''; sizeField(); paintFooter(I.view);
  };
  root.addEventListener('click', (e) => {
    const sum = e.target.closest('summary');
    if (sum && sum.parentElement.dataset.k) { const d = sum.parentElement; S.folds[d.dataset.k] = { v: !d.open, base: d.dataset.d === '1' }; return; }
    const t = e.target.closest('[data-a]');
    if (!t || t.disabled) return;
    const v = I.view || {}, a = t.dataset.a;
    if (S.menu && a !== 'menu' && a !== 'set') { S.menu = false; }   // a switch keeps the menu open
    if ((handlers[a] || []).map((f) => safe(() => f(t, x, e))).includes(true)) { /* a part handled it */ }
    else if (a === 'open') { setOpen(true); }
    else if (a === 'set') {
      const id = t.dataset.opt, value = !option(v, id);
      if (COCO.local.has(id)) S.pend[id] = { v: value, seq: 0 };
      else { send({ a: 'set', option: id, value }); S.pend[id] = { v: value, seq: S.seq }; }   // until the host has answered this action
      paint();
    }
    else if (a === 'rail') { setOpen(false); send({ a: 'rail' }); }
    else if (a === 'min') { setOpen(false); }
    else if (a === 'menu') { S.menu = !S.menu; paintMenu(v); if (S.menu) requestAnimationFrame(() => el.menu.querySelector('.it')?.focus()); }
    else if (a === 'new' || a === 'disc') {
      const has = (v.thread || []).length || (v.queue || []).length || v.status === 'working';
      if (a === 'disc' && !has) { send({ a: 'disconnect' }); paintMenu(v); } else { S.confirm = a; paintMenu(v); paintConfirm(v); requestAnimationFrame(() => el.cf.querySelector('.b.k')?.focus()); }
    } else if (a === 'new!' || a === 'disc!') { S.confirm = ''; send({ a: a === 'new!' ? 'new' : 'disconnect' }); paintConfirm(v); el.ta.focus(); }
    else if (a === 'keep') { S.confirm = ''; paintConfirm(v); el.mb.focus(); }
    else if (a === 'prompt') {
      const p = promptOf((v.prompts || [])[Number(t.dataset.i)]);
      if (p.fill && p.text) { el.ta.value = p.text; S.draft = p.text; sizeField(); paintFooter(v); el.ta.focus(); }   // for a prompt meant to be edited first
      else if (p.text) send({ a: 'prompt', text: p.text });
    }
    else if (a === 'send') doSend();
    else if (a === 'stop') send({ a: 'stop' });
    else if (a === 'allow' || a === 'decline') { x.settle(t.dataset.id); send({ a, id: t.dataset.id, ...collect(a, t) }); if (!el.fld.hidden) el.ta.focus({ preventScroll: true }); }
    else if (a === 'system_action') send({ a, id: t.dataset.id });
    else if (a === 'panel-close') x.closePanel();
    else if (a === 'unqueue') send({ a: 'unqueue', id: t.dataset.id });
    else if (a === 'retry' || a === 'reconnect') send({ a });
    else if (a === 'connect') { const sel = el.fix.querySelector('select'); const profile = t.dataset.id || (sel && sel.value); if (profile) { S.profile = profile; send({ a: 'connect', profile, ...collect('connect', t) }); } }
    else if (a === 'copy') {
      const [kind, id] = t.dataset.id.split(/:(.*)/s);
      const it = (v.thread || []).find((x) => String(x.id) === id && (kind === 'a' ? x.kind === 'answer' : x.kind === 'draft'));
      if (it) copy(kind === 'd' && it.title ? `${it.title}\n${it.text}` : it.text, t);
    }
    paintMenu(v);
  });
  root.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && S.open) {
      e.stopPropagation();
      if (S.confirm) { S.confirm = ''; paintConfirm(I.view); el.mb.focus(); }
      else if (S.menu) { S.menu = false; paintMenu(I.view); el.mb.focus(); }
      else if (S.panel) x.closePanel();
      else if (!COCO.escape.some((f) => safe(() => f(x)) === true)) setOpen(false);   // a list, the wider view: back one level before the window goes
    } else if (e.target === el.ta && e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); doSend(); }
    else if (S.menu && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      const its = [...el.menu.querySelectorAll('.it')], at = its.indexOf(shadow.activeElement);
      its[(at + (e.key === 'ArrowDown' ? 1 : -1) + its.length) % its.length]?.focus();
    }
  });
  el.ta.addEventListener('input', () => { S.draft = el.ta.value; sizeField(); paintFooter(I.view); });
  root.addEventListener('input', (e) => COCO.input.forEach((f) => safe(() => f(e, x))));   // what is typed in the pinned block, the panels, the field
  root.addEventListener('change', (e) => COCO.change.forEach((f) => safe(() => f(e, x))));
  el.fix.addEventListener('change', (e) => { if (e.target.matches('select')) S.profile = e.target.value; });
  const away = () => { S.follow.away = true; };
  ['wheel', 'touchstart'].forEach((type) => el.bd.addEventListener(type, away, { passive: true }));
  el.bd.addEventListener('pointerdown', (e) => { if (e.target === el.bd) away(); });   // the scrollbar
  el.bd.addEventListener('keydown', (e) => { if (e.target === el.bd) away(); });
  el.bd.addEventListener('scroll', () => { S.scroll = el.bd.scrollTop; el.cc.classList.toggle('scr', Math.abs(el.bd.scrollTop) > 2); }, { passive: true });
  root.addEventListener('focusout', (e) => { if (S.menu && !S.rebuild && root.ownerDocument.hasFocus() && !el.menu.contains(e.relatedTarget) && e.relatedTarget !== el.mb) { S.menu = false; guard(() => paintMenu(I.view)); } });

  COCO.init.forEach((f) => safe(() => f(x)));
  // first session: the label shows once, then the launcher rests
  if (!guard(() => sessionStorage.getItem('coco-intro'))) { S.introOn = true; guard(() => sessionStorage.setItem('coco-intro', '1')); setTimeout(() => { S.introOn = false; if (I.view) paintLauncher(I.view); }, 6000); }
  return I;
}

// A shadow root does not register its own @font-face: the font goes into the page's font set, from the package (no request, no CDN).
const fonts = (doc, font) => {
  if (doc._cocoFonts || typeof COCO_FONTS === 'undefined' || (font && !/montserrat/i.test(font)) || !doc.fonts || typeof FontFace === 'undefined') return;
  doc._cocoFonts = true;
  Object.entries(COCO_FONTS).forEach(([weight, b64]) => guard(() => {
    const face = new FontFace('Montserrat', Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer, { weight });
    doc.fonts.add(face);
    face.load().catch(() => {});
  }));
};
// theme: {name: value} becomes --coco-<name> on the window's root (the defaults are in coco.css); `avoid` is the selectors of what the launcher must clear
const theme = (root, I, wanted) => {
  const next = Object.entries(wanted || {}).filter(([k, v]) => k !== 'avoid' && v != null && v !== '');
  (I.themed || []).forEach((k) => { if (!next.some(([n]) => n === k)) root.style.removeProperty(`--coco-${k}`); });
  next.forEach(([k, v]) => root.style.setProperty(`--coco-${k}`, v));
  I.themed = next.map(([k]) => k);
};

export default function ({ data, parentElement, setTriggerValue }) {
  LABELS = data.labels || {}; AVOID = (data.theme || {}).avoid || ''; EXCLUDE = data.exclude || [];
  const root = parentElement.querySelector('.coco-root');
  fonts(root.ownerDocument, (data.theme || {}).font);
  const I = root._coco || (root._coco = build(root, parentElement, data.spark));
  theme(root, I, data.theme);
  ['calm', 'nocopy', 'nosteps'].forEach((c, i) => root.classList.toggle(c, [(data.features || {}).motion, (data.features || {}).copy, (data.features || {}).steps][i] === false));   // Features(motion, copy, steps) off
  I.set = setTriggerValue;
  I.update(data);
}
