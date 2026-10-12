// Ask CoCo, part "plans" (frames 47-54): A plan to approve, and planning only.
// Fixtures: f<nn>_ views of tests/coco_ui_fixtures.py for these frames (GESTURES: the decline and the menu switch); look at them
// with tests/coco_harness.py. The registry and the helpers are documented at the top of ../coco.js; markup follows the sheet
// (ui-rebuild/design/CoCo22.dc.html, built by tools/checks/build_coco22.py), styles are in ./plans.css.
//
// The "Plan first" switch is the core's (view.options). A decline reason is read from the field when Decline plan is pressed; it is never required.

part('plans', (C) => {
  const { btn, render, L, E } = C.h;
  const S = C.state('plans');   // declining: the id of the plan whose reason is asked
  const plan = (text, cls = '') => {   // a plan is CoCo's ordered list; anything else is drawn as the text it is
    const html = render(text);
    return html.startsWith('<ol>') ? html.replace('<ol>', `<ol class="ag-plan${cls}">`) : `<div class="ag-plan${cls}">${html}</div>`;
  };
  const acts = (...b) => `<div class="ag-acts">${b.join('')}</div>`;
  const cut = (b) => b.classList.toggle('cut', b.scrollTop + b.clientHeight < b.scrollHeight - 1);   // more of the plan below: its box says so
  const CUT = () => `<p class="ag-kk">${E('plan.approve_note')}</p>`;   // outside the scrolling body: never below the fold
  const waiting = (x) => { const w = (x.view || {}).wait; return w && w.kind === 'plan' ? w : null; };

  C.wait.plan = {
    html(w) {
      const id = w.id, asking = S.declining === id;
      const body = `<div class="ag-body${asking ? ' sh' : ''}" role="region" aria-label="${E('plan.region')}" tabindex="0">${plan(w.text)}</div>`;
      const frame = (inner, tail, buttons) => `<div class="ag-ask" role="group" aria-label="${E('plan.group')}" data-k="plan:${id}">`
        + `<div class="ag-bd"><p class="ag-q">${E('plan.title')}</p>${inner}</div>${tail}${buttons}</div>`;
      return asking
        ? frame(`${body}<div class="ag-fr"><label for="plans-reason">${E('plan.reason')} <span class="mut">${E('common.optional')}</span></label>`
          + '<textarea id="plans-reason" class="in" rows="2" data-f="reason"></textarea></div>', '',
          acts(btn(L('plan.decline_do'), { a: 'decline_plan', id, cls: 'b k' }), btn(L('common.back'), { a: 'plan_back', id })))
        : frame(body, CUT(), acts(btn(L('plan.approve'), { a: 'approve_plan', id, cls: 'b k' }), btn(L('plan.decline'), { a: 'plan_decline', id })));
    },
    announce: () => L('plan.announce'),
  };

  C.block.text = (b) => plan(b.text, ' ev');

  C.strip.push((v) => (v.mode && v.mode.planning
    ? `<div class="ag-mode" role="status"><span>${E('plan.mode')}</span>${v.mode.can_carry_out ? `<button type="button" class="b" data-a="carry_out">${E('plan.carry_out')}</button>` : ''}</div>`
    : ''));

  C.on('approve_plan', (t, x) => { x.settle(t.dataset.id); x.send({ a: 'approve_plan', id: t.dataset.id }); return true; });
  C.on('decline_plan', (t, x) => {
    const reason = x.el.rq.querySelector('[data-f="reason"]')?.value.trim() || '';
    x.settle(t.dataset.id); S.declining = ''; x.send({ a: 'decline_plan', id: t.dataset.id, reason });
    return true;
  });
  C.on('plan_decline', (t, x) => { S.declining = t.dataset.id; x.repaint('[data-f="reason"]'); return true; });
  C.on('plan_back', (t, x) => { S.declining = ''; x.repaint('[data-a="plan_decline"]'); return true; });
  C.on('carry_out', (t, x) => { x.send({ a: 'carry_out' }); if (!x.el.fld.hidden) x.el.ta.focus({ preventScroll: true }); return true; });
  C.escape.push((x) => { const w = waiting(x); if (!w || S.declining !== w.id) return; S.declining = ''; x.repaint('[data-a="plan_decline"]'); return true; });   // Escape in the reason: back to the plan

  C.init.push((x) => x.root.addEventListener('scroll', (e) => { if (e.target.classList?.contains('ag-body')) cut(e.target); }, true));
  C.after.push((v, x) => { x.el.rq.querySelectorAll('.ag-body').forEach(cut); });
});
