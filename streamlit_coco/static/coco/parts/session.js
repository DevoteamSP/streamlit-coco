// Ask CoCo, part "session" (frames 79-86): display options, session details, connecting, could not connect, several connection files, raw details, reasoning.
// Every entry draws only what the view carries (options, hidden, session, problem, profile_files, step.raw, reasoning items).
// The switches of view.options are the core's; "shorten" is the one only this window applies (C.local).
part('session', (C) => {
  const { esc, btn, fold, ic, CH, icon, L, E } = C.h;
  const st = C.state('session');   // all: {answer id: true} messages shown whole; pick: {profile, file}; open: the list of profiles; copied
  icon('info', '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>');
  C.local.add('shorten');

  // ------ the menu: Session details, after the other lines
  C.menu.push({ order: 80, items: (v) => (v.session && v.session.length ? `<button type="button" class="it" role="menuitem" data-a="details">${ic('info', 'i s')}<span>${E('session.details')}</span></button>` : '') });
  C.on('details', (t, x) => { x.openPanel('details'); return true; });
  const facts = (v) => v.session || [];
  C.panel.details = (v) => (facts(v).length ? `<div class="ag-pan" role="dialog" aria-label="${E('session.details')}"><p class="ag-q">${E('session.details')}</p><div class="ag-fx">${
    facts(v).map((f) => `<span class="k">${esc(f.label)}</span><span class="v">${esc(f.value)}</span>`).join('')}</div><div class="ag-acts">${
    btn(L(st.copied ? 'common.copied' : 'session.copy'), { a: 'copy_details' })}${btn(L('common.close'), { a: 'panel-close' })}</div></div>` : '');
  C.on('copy_details', (t, x) => {
    const text = facts(x.view).map((f) => `${f.label}: ${f.value}`).join('\n');
    Promise.resolve().then(() => navigator.clipboard.writeText(text)).catch(() => {});
    x.announce(L('common.copied')); st.copied = true; x.repaint();
    setTimeout(() => { st.copied = false; x.repaint(); }, 1500);
    return true;
  });

  // ------ the thread: earlier messages, shortened messages, raw details, reasoning
  C.lead.push((v) => (v.hidden > 0 ? { k: 'more', html: `<button type="button" class="b sm ag-more" data-k="more" data-a="show_earlier">${E(v.hidden === 1 ? 'session.earlier_one' : 'session.earlier_other', { n: Number(v.hidden) })}</button>` } : null));
  C.on('show_earlier', (t, x) => { x.send({ a: 'show_earlier' }); return true; });
  C.decorate.answer.push((it, x, d) => {   // never the latest answer; Show all opens one, Show less shortens it again
    const v = x.view || {}, last = [...(v.thread || [])].reverse().find((q) => q.kind === 'answer');
    if (!x.opt('shorten') || it.streaming || (last && last.id === it.id) || String(it.text || '').length < 240) return;
    const whole = !!st.all[it.id];
    d.cls += ' ag-short';
    d.parts.text = `${whole ? d.parts.text : `<div class="ag-clp">${d.parts.text}</div>`}<div class="act"><button type="button" class="b sm" data-a="show_all" data-id="${esc(it.id)}" aria-expanded="${whole}">${E(whole ? 'session.show_less' : 'session.show_all')}</button></div>`;
  });
  st.all ||= {};
  C.on('show_all', (t, x) => { st.all[t.dataset.id] = !st.all[t.dataset.id]; x.repaint(); return true; });
  C.decorate.step.push((s, x, d) => {
    if (!s.raw || !x.opt('raw')) return;
    Object.assign(d.parts, { tool: '', allowed: '', input: `<p class="cap">${E('session.request')}</p><pre class="pre">${esc(s.raw.request)}</pre>`, result: `<p class="cap">${E('step.result')}</p><pre class="pre">${esc(s.raw.result)}</pre>` });
  });
  C.thread.reasoning = (it) => ({ k: `r:${it.id}`, html: `<details class="ag-step ag-rs st-ok" data-k="r:${esc(it.id)}" data-d="0"><summary><span class="ag-g"></span><span class="ag-tx"><span class="ag-d">${E('session.considered')}</span><span class="sr">, ${E('step.completed')}</span></span>${CH}</summary><div class="ag-det"><p class="ag-nar">${esc(it.text)}</p></div></details>` });

  // ------ the first screen: connecting, could not connect, the profile list grouped by file
  const hasThread = (v) => (v.thread || []).length || (v.queue || []).length;
  C.empty.push((v) => {
    if (hasThread(v)) return;
    if (v.status === 'connecting' && v.type_ahead) return `<span class="ag-run" aria-hidden="true"></span><p class="t">${E('first.connecting', { profile: v.profile || L('first.your_account') })}</p>`;
    if (v.status === 'not_connected' && v.problem) return `<p class="t" role="alert">${v.profile ? E('first.could_not_connect_to', { profile: v.profile }) : E('first.could_not_connect')}</p><p class="cap">${esc(v.problem)}</p>`
      + (v.error ? fold('cn:error', L('session.show_message'), L('session.hide_message'), `<pre>${esc(v.error)}</pre>`) : '');
  });
  const files = (v) => (v.profile_files || []).filter((f) => (f.profiles || []).length);
  const picked = (v) => {
    const all = files(v).flatMap((f) => f.profiles.map((p) => ({ profile: p, file: f.file })));
    return all.find((q) => st.pick && q.profile === st.pick.profile && q.file === st.pick.file) || all.find((q) => q.profile === v.profile) || all[0];
  };
  C.footer.push((v, x, html) => {
    if (v.status !== 'not_connected') return;
    const label = esc(L(v.problem ? 'common.try_again' : 'footer.connect'));
    if (!files(v).length) return v.problem ? html.replace(/(data-a="connect"[^>]*>)[^<]*/, (m, open) => open + label) : undefined;
    const p = picked(v);
    return `<div class="selw"><button type="button" class="in sel" data-a="profiles" aria-label="${E('footer.profile')}" aria-haspopup="listbox" aria-expanded="${!!st.open}"><span>${esc(p.profile)}</span></button>${ic('chev', 'i s')}${st.open ? `<div class="pop ag-ls" role="listbox" aria-label="${E('footer.profile')}">`
      + files(v).map((f) => `<p class="mh">${esc(f.file)}</p>${f.profiles.map((n) => {
        const k = n === p.profile && f.file === p.file;
        return `<button type="button" class="it${k ? ' on' : ''}" role="option" aria-selected="${k}" data-a="pick" data-id="${esc(n)}" data-file="${esc(f.file)}">${esc(n)}</button>`;
      }).join('')}`).join('') + '</div>' : ''}</div>`
      + `<button type="button" class="b k" data-a="connect" data-id="${esc(p.profile)}">${label}</button>`;
  });
  C.collect.connect.push((t, x) => { const p = files(x.view).length && picked(x.view); return p && p.file ? { file: p.file } : {}; });
  C.on('profiles', (t, x) => { st.open = !st.open; x.repaint(st.open ? '.ag-ls .it.on' : '[data-a="profiles"]'); return true; });
  C.on('pick', (t, x) => { st.pick = { profile: t.dataset.id, file: t.dataset.file }; st.open = false; x.repaint('[data-a="profiles"]'); return true; });
  C.escape.push((x) => { if (!st.open) return; st.open = false; x.repaint('[data-a="profiles"]'); return true; });   // Escape closes the list; the window stays
  C.init.push((x) => x.root.addEventListener('keydown', (e) => {
    if (!st.open || (e.key !== 'ArrowDown' && e.key !== 'ArrowUp')) return;
    e.preventDefault();
    const its = [...x.shadow.querySelectorAll('.ag-ls .it')], at = its.indexOf(x.shadow.activeElement);
    its[(at + (e.key === 'ArrowDown' ? 1 : -1) + its.length) % its.length]?.focus();
  }));

  C.after.push((v) => { if (st.open && v.status !== 'not_connected') st.open = false; });
});
