// Ask CoCo, part "standing" (frames 55-61): two things wait; the standing permission offered on a request, granted, taken back.
// Nothing is drawn unless the host sends request.standing / view.granted. The tick is the window's own (C.state), sent with Allow.
part('standing', (C) => {
  const { esc, btn, L, E } = C.h;
  const S = C.state('standing');   // { ticked: { request id: true } }
  S.ticked ||= {};
  C.h.icon('shield', '<path d="M12 3 5 6v6c0 4.5 3 7.7 7 9 4-1.3 7-4.5 7-9V6z"/>');
  const granted = (v) => (v && Array.isArray(v.granted) ? v.granted : []);

  C.decorate.request.push((r, x, d) => {
    const s = r.standing;
    if (!s) return;
    const on = !!S.ticked[r.id];
    d.parts.extra += `<div class="ag-std"><label><input type="checkbox" data-f="std" data-id="${esc(r.id)}"${on ? ' checked' : ''}><span>${esc(s.label)}</span></label>`
      + (on ? `<div class="ag-fx"><span class="k">${E('standing.covers')}</span><span class="v">${esc(s.covers)}</span><span class="k">${E('standing.until')}</span><span class="v">${esc(s.until)}</span></div>` : '') + '</div>';
    if (on) d.parts.allow = E('standing.allow');
  });
  C.collect.allow.push((t) => (S.ticked[t.dataset.id] ? { standing: true } : {}));
  C.change.push((e, x) => { if (e.target.matches('input[data-f="std"]')) { S.ticked[e.target.dataset.id] = e.target.checked; x.repaint(); } });

  C.decorate.step.push((s, x, d) => { if (s.standing && !s.allowed) d.parts.allowed = `<p class="cap">${E('standing.not_asked')}</p>`; });

  C.menu.push({ order: 70, items: (v) => {
    const n = granted(v).length;
    return n ? `<button type="button" class="it" role="menuitem" data-a="granted">${C.h.ic('shield', 'i s')}<span>${E('standing.menu')}<span class="ag-sub">${E(n === 1 ? 'standing.menu_one' : 'standing.menu_other', { n })}</span></span></button>` : '';
  } });
  C.on('granted', (t, x) => { x.openPanel('without_asking'); return true; });
  C.on('revoke', (t, x) => { x.send({ a: 'revoke', id: t.dataset.id }); return true; });
  C.panel.without_asking = (v) => {
    const g = granted(v);
    if (!g.length) return '';
    return `<div class="ag-pan" role="dialog" aria-label="${E('standing.menu')}"><p class="ag-q">${E('standing.panel_title')}</p>`
      + g.map((p) => `<div class="ag-pr"><span>${esc(p.text)}</span><button type="button" class="b" data-a="revoke" data-id="${esc(p.id)}" aria-label="${E('standing.ask_again_for', { text: p.text })}">${E('standing.ask_again')}</button></div>`).join('')
      + `<p class="ag-kk">${E(g.length > 1 ? 'standing.ends_many' : 'standing.ends_one')}</p><div class="ag-acts">${btn(L('common.close'), { a: 'panel-close' })}</div></div>`;
  };
  C.confirm.push((v) => (granted(v).length ? L('standing.confirm') : ''));
});
