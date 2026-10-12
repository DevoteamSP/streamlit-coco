// Ask CoCo, part "questions" (frames 38-46): a question from CoCo or from the application: one or several questions, choices,
// 'Something else', a form; answered, skipped, minimised. Contract: utils/coco_runtime.py (wait kind "question", thread item "asked",
// actions answer / skip). The window's own state (question shown, ticked, typed) lives in C.state('questions') and is never sent
// before Send answer. Markup and class names are the sheet's (ui-rebuild/tools/checks/build_coco22.py).
part('questions', (C, name) => {
  const { esc, btn, ic, L, E } = C.h;
  const S = C.state(name);
  const fresh = (w) => { if (S.id !== w.id) Object.assign(S, { id: w.id, i: 0, pick: {}, oth: {}, on: {}, form: {}, sc: 0 }); return S; };
  const val = (q, f) => (S.form[q.id] && f.id in S.form[q.id] ? S.form[q.id][f.id] : f.value || '');
  const ready = (q) => (q.kind === 'form' ? (q.fields || []).every((f) => !f.required || val(q, f).trim())
    : (S.pick[q.id] || []).length > 0 || (S.on[q.id] && (S.oth[q.id] || '').trim() !== ''));
  const answer = (q) => (q.kind === 'form'
    ? { id: q.id, picked: [], other: null, fields: Object.fromEntries((q.fields || []).map((f) => [f.id, val(q, f)])) }
    : { id: q.id, picked: S.pick[q.id] || [], other: S.on[q.id] ? (S.oth[q.id] || '').trim() : null, fields: null });
  const wait = (x) => { const w = (x.view || {}).wait; return w && w.kind === 'question' ? w : null; };

  const choiceHtml = (q) => {
    const kind = q.multi ? 'checkbox' : 'radio', pick = S.pick[q.id] || [], on = !!S.on[q.id];
    const opt = (label, desc, o, checked) => `<label class="ag-opt${checked ? ' on' : ''}"><input type="${kind}" name="o:${esc(q.id)}" data-q="${esc(q.id)}" data-o="${o}" data-f="o${o}"${checked ? ' checked' : ''}>`
      + `<span class="ag-ot">${esc(label)}${desc ? `<span class="ag-od">${esc(desc)}</span>` : ''}</span></label>`;
    const list = (q.options || []).map((o, i) => opt(o.label, o.description, i, pick.includes(o.label))).join('') + (q.other ? opt(q.other.label || L('question.other'), '', 'other', on) : '');
    return `<div class="ag-body"><div class="ag-opts" role="${q.multi ? 'group' : 'radiogroup'}" aria-label="${esc(q.text)}">${list}</div></div>`
      + (q.other && on ? `<textarea class="in ag-oth" rows="2" aria-label="${E('question.your_answer')}" data-q="${esc(q.id)}" data-f="oth">${esc(S.oth[q.id] || '')}</textarea>` : '');
  };
  const formHtml = (q) => `<div class="ag-body">${(q.fields || []).map((f, k) => {
    const id = `ff:${esc(q.id)}:${esc(f.id)}`, v = val(q, f), at = `id="${id}" data-q="${esc(q.id)}" data-ff="${esc(f.id)}" data-f="ff${k}"`;
    const ctl = f.type === 'choice'
      ? `<div class="selw"><select class="in sel" ${at}>${(f.choices || []).map((c) => `<option${c === v ? ' selected' : ''}>${esc(c)}</option>`).join('')}</select>${ic('chev')}</div>`
      : f.type === 'longtext' ? `<textarea class="in" rows="2" ${at}>${esc(v)}</textarea>`
        : `<input class="in" ${f.type === 'number' ? 'inputmode="decimal" ' : ''}value="${esc(v)}" ${at}>`;
    return `<div class="ag-fr"><label for="${id}">${esc(f.label)}${f.required ? '' : ` <span class="mut">${E('common.optional')}</span>`}</label>${ctl}</div>`;
  }).join('')}</div>`;

  C.wait.question = {
    html(w, x) {
      fresh(w);
      const qs = w.questions || [], n = qs.length, i = Math.min(S.i, n - 1), q = qs[i];
      if (!q) return '';
      const last = i === n - 1, usable = last ? qs.every(ready) : ready(q);
      const more = C.h.kicker(w.more);
      const acts = `<div class="ag-acts">${btn(L(n > 1 ? (last ? 'question.send_all' : 'question.next') : 'question.send'), { a: last ? 'answer' : 'q-next', id: w.id, cls: 'b k', off: !usable })}`
        + (i > 0 ? btn(L('common.back'), { a: 'q-back', id: w.id }) : '') + btn(L(n > 1 ? 'question.skip_all' : 'question.skip'), { a: 'skip', id: w.id }) + '</div>';
      return `<div class="ag-ask" role="group" aria-label="${E(w.source === 'app' ? 'question.group_app' : 'question.group_coco')}" data-k="q:${esc(w.id)}">`
        + `<div class="ag-bd">${n > 1 ? `<p class="ag-kk">${E('question.n_of', { i: i + 1, n })}</p>` : ''}${more}<p class="ag-q">${esc(q.text)}</p>${q.kind === 'form' ? formHtml(q) : choiceHtml(q)}</div>${acts}</div>`;
    },
    announce: (w) => L(w.source === 'app' ? 'question.asks_app' : 'question.asks_coco', { text: ((w.questions || [])[0] || {}).text || '' }),
  };

  C.thread.asked = (it) => ({ k: `n:${it.id}`, html: `<div class="msg" data-k="n:${esc(it.id)}"><span class="sr">${E('thread.coco')}</span>${esc(it.text)}${it.note ? `<span class="ag-n">${esc(it.note)}</span>` : ''}</div>` });

  C.on('q-next', (t, x) => { const w = wait(x); if (w && !t.classList.contains('ag-off')) { S.i = Math.min(S.i + 1, w.questions.length - 1); S.sc = 0; x.repaint('[data-a="q-next"], [data-a="answer"]'); } return true; });
  C.on('q-back', (t, x) => { S.i = Math.max(S.i - 1, 0); S.sc = 0; x.repaint('[data-a="q-back"], [data-a="q-next"], [data-a="answer"]'); return true; });
  C.on('answer', (t, x) => {
    const w = wait(x);
    if (!w || t.classList.contains('ag-off')) return true;
    x.settle(w.id); x.send({ a: 'answer', id: w.id, answers: w.questions.map(answer) });
    return true;
  });
  C.on('skip', (t, x) => { const w = wait(x); if (w) { x.settle(w.id); x.send({ a: 'skip', id: w.id }); } return true; });

  const of = (e, x) => { const w = wait(x), n = e.target.closest && e.target.closest('.ag-ask[data-k^="q:"]'); return w && n ? w.questions.find((k) => k.id === e.target.dataset.q) : null; };
  C.change.push((e, x) => {
    const t = e.target, qu = of(e, x);
    if (qu && t.matches('select[data-ff]')) { (S.form[qu.id] ||= {})[t.dataset.ff] = t.value; x.repaint(); return; }   // a select is chosen, not typed
    if (!qu || t.dataset.o == null) return;
    const cur = S.pick[qu.id] || [], label = t.dataset.o === 'other' ? null : qu.options[Number(t.dataset.o)].label;
    if (!qu.multi) { S.pick[qu.id] = label == null ? [] : [label]; S.on[qu.id] = label == null; }
    else if (label == null) S.on[qu.id] = t.checked;
    else S.pick[qu.id] = t.checked ? [...cur, label] : cur.filter((l) => l !== label);
    x.repaint();
  });
  C.input.push((e, x) => {
    const t = e.target, qu = of(e, x);
    if (!qu) return;
    if (t.dataset.ff) (S.form[qu.id] ||= {})[t.dataset.ff] = t.value; else if (t.dataset.f === 'oth') S.oth[qu.id] = t.value; else return;
    x.repaint();
  });
  C.init.push((x) => x.root.addEventListener('scroll', (e) => { if (e.target.matches && e.target.matches('.ag-ask .ag-body')) S.sc = e.target.scrollTop; }, true));
  C.after.push((v, x) => {   // a repaint rebuilds the block: its scroll comes back, and 'cut' says there is more below
    const b = x.el.rq.querySelector('.ag-ask .ag-body');
    if (b) { if (S.sc && b.scrollTop !== S.sc) b.scrollTop = S.sc; b.classList.toggle('cut', b.scrollHeight > b.clientHeight + 1); }
  });
});
