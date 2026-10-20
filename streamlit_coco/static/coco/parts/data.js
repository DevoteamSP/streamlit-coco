// Ask CoCo, part "data" (frames 62-69): data in an answer: a table, a query result behind a step, no rows, Open larger,
// an answer that is data, a code block with its own Copy, CSV built here from the rows received. Contract: utils/coco_runtime.py.
part('data', (C) => {
  const { esc, fold, ic, L, E } = C.h;
  C.h.icon('back', '<path d="M19 12H5M11 6l-6 6 6 6"/>');
  const S = C.state('data');   // larger: id of the table shown in the wider view
  const FIVE = 5;
  const num = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const rowsWord = (n) => L(n === 1 ? 'data.rows_one' : 'data.rows_other', { n: num(n) });
  const isData = (b) => b && b.type === 'data';
  const cell = (v) => String(v ?? '').replace(/[\t\r\n]+/g, ' ');
  const tsv = (t) => [t.columns.map((c) => c.name), ...t.rows].map((r) => r.map(cell).join('\t')).join('\n');

  // CSV: quotes, separators and newlines are quoted; a leading = + - @ (or tab, CR) is neutralised so a spreadsheet never runs a cell as a formula
  const csv = (t) => {
    const one = (v) => {
      let s = String(v ?? '');
      if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
      return /[",;\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    return [t.columns.map((c) => c.name), ...t.rows].map((r) => r.map(one).join(',')).join('\r\n') + '\r\n';
  };
  C.h.tableCsv = csv;

  // ---- a table: text wraps, figures do not, the box scrolls inside itself (cells are DATA: escaped, never markup)
  const tableHtml = (t, rows) => {
    const cols = t.columns.map((c) => (c.kind === 'number' ? 'n' : 't'));
    return `<div class="ag-tbl" role="region" aria-label="${esc(t.label || L('data.table'))}" tabindex="0"><table><thead><tr>${t.columns.map((c, i) => `<th class="${cols[i]}">${esc(c.name)}</th>`).join('')}</tr></thead><tbody>`
      + rows.map((r) => `<tr>${cols.map((k, i) => `<td class="${k}">${esc(r[i])}</td>`).join('')}</tr>`).join('') + '</tbody></table></div>';
  };
  const clean = (t) => (t && Array.isArray(t.columns) && Array.isArray(t.rows) && t.rows.length ? t : null);
  const total = (t) => Math.max(Number(t.total) || 0, t.rows.length);

  C.block.data = (b) => {
    const fields = (b.fields || []).map((f) => `<span class="k">${esc(f.label)}</span><span class="v">${esc(f.value)}</span>`).join('');
    const tables = (b.tables || []).map(clean).filter(Boolean).map((t) => {
      const more = t.rows.length > FIVE || total(t) > t.rows.length;
      const foot = more ? `<div class="ag-tf"><span class="cap">${E('data.of', { shown: Math.min(FIVE, t.rows.length), total: rowsWord(total(t)) })}</span><span class="ag-ta"><button type="button" class="b sm" data-a="data-larger" data-id="${esc(t.id)}">${E('data.larger')}</button>`
        + `<button type="button" class="ag-ib" data-a="data-copy-table" data-id="${esc(t.id)}" aria-label="${E('data.copy_table')}">${ic('copy', 'i s')}</button></span></div>` : '';
      return (t.label ? `<p class="cap">${esc(t.label)}</p>` : '') + tableHtml(t, t.rows.slice(0, FIVE)) + foot;
    }).join('');
    const json = b.json ? fold(`dj:${b.id}`, L('data.show_json'), L('data.hide_json'), `<pre>${esc(b.json)}</pre>`) : '';
    return (b.title ? `<b class="b6">${esc(b.title)}</b>` : '') + (fields ? `<div class="ag-fx">${fields}</div>` : '') + tables + json;
  };

  // ---- where the tables are (the wider view and Copy find them by id in the current view)
  const blocksOf = (view) => (view.thread || []).flatMap((it) => [it, ...(it.items || [])]).flatMap((it) => it.blocks || []).filter(isData);
  const findTable = (view, id) => blocksOf(view).flatMap((b) => b.tables || []).reverse().find((t) => clean(t) && String(t.id) === String(id));

  // ---- a step: the exact SQL, then the result
  C.decorate.step.push((s, x, d) => {
    const sql = s.state === 'ok' && s.input && typeof s.input.sql === 'string' ? s.input.sql : '';
    if (sql) { d.parts.tool = ''; d.parts.input = `<p class="cap">${E('data.sql')}</p><pre class="pre">${esc(sql)}</pre>`; }
    if ((s.blocks || []).some(isData)) d.parts.result = `<p class="cap">${E('step.result')}</p>${d.parts.result}`;
  });

  // ---- the wider view: the same window, wider; rendered once per table, not at every poll
  const cache = new Map();
  C.takeover.push((view) => {
    const t = S.larger && findTable(view, S.larger);
    if (!t) { S.larger = ''; return null; }
    const sig = [t.id, t.rows.length, t.total, t.columns.map((c) => c.name).join(), t.rows[0], t.rows.at(-1), t.label].join('|');
    let html = cache.get(sig);
    if (!html) {
      const count = total(t) > t.rows.length ? L('data.first_of', { shown: num(t.rows.length), total: rowsWord(total(t)) }) : rowsWord(t.rows.length);
      html = `<div class="ag-xv"><div class="ag-xh"><button type="button" class="b" data-a="data-back">${ic('back', 'i s')}${E('data.back')}</button><span class="cap">${esc(count)}</span>`
        + `<span class="ag-ta"><button type="button" class="b" data-a="data-copy-table" data-id="${esc(t.id)}" data-t="1">${E('data.copy_table')}</button><button type="button" class="b" data-a="data-csv" data-id="${esc(t.id)}">${E('data.csv')}</button></span></div>${tableHtml(t, t.rows)}</div>`;
      cache.clear(); cache.set(sig, html);
    }
    return { html, cls: 'ag-xl' };
  });

  const duty = (x, id, fn) => { const t = findTable(x.view || {}, id); if (t) fn(t); };
  C.on('data-larger', (t, x) => { S.larger = t.dataset.id; x.repaint('[data-a="data-back"]'); return true; });
  const back = (x) => { const id = S.larger; S.larger = ''; x.repaint(`[data-a="data-larger"][data-id="${CSS.escape(id)}"]`); return true; };
  C.on('data-back', (t, x) => back(x));
  C.escape.push((x) => (S.larger ? back(x) : undefined));   // Escape in the wider view: back to the conversation, the window stays
  C.on('data-copy-table', (t, x) => { duty(x, t.dataset.id, (tb) => x.copy(tsv(tb), t)); return true; });
  C.on('data-csv', (t, x) => {
    duty(x, t.dataset.id, (tb) => {
      const doc = x.root.ownerDocument, url = URL.createObjectURL(new Blob(['﻿', csv(tb)], { type: 'text/csv;charset=utf-8' })), a = doc.createElement('a');
      const stem = L('data.file'); a.href = url; a.download = `${(tb.label || stem).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || stem}.csv`;
      x.root.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      x.announce(L('data.csv_done'));
    });
    return true;
  });

  // ---- Copy of an answer that has blocks: its text, then the blocks as plain text
  const plain = (b) => (isData(b)
    ? [b.title, ...(b.fields || []).map((f) => `${f.label}: ${f.value}`), ...(b.tables || []).map(clean).filter(Boolean).map((t) => (t.label ? `${t.label}\n` : '') + tsv(t))].filter(Boolean).join('\n')
    : b && b.text) || '';
  C.on('copy', (t, x) => {
    const [kind, id] = t.dataset.id.split(/:(.*)/s);
    const it = kind === 'a' && ((x.view || {}).thread || []).find((i) => i.kind === 'answer' && String(i.id) === id);
    if (!it || !(it.blocks || []).some(isData)) return;
    x.copy([it.text, ...it.blocks.map(plain)].filter(Boolean).join('\n\n'), t);
    return true;
  });

  // ---- a fenced code block in an answer: its language and its own Copy
  const pieces = (text) => {   // the fences as the Markdown renderer reads them: an unclosed one runs to the end
    const lines = String(text ?? '').replace(/\r\n?/g, '\n').split('\n'), out = [];
    let md = [];
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(/^\s*```\s*([\w+#.-]*)/);
      if (!m) { md.push(lines[i]); continue; }
      out.push({ md: md.join('\n') }); md = [];
      const code = [];
      for (i++; i < lines.length && !/^\s*```/.test(lines[i]); i++) code.push(lines[i]);
      out.push({ lang: m[1], code: code.join('\n') });
    }
    out.push({ md: md.join('\n') });
    return out;
  };
  C.decorate.answer.push((it, x, d) => {
    if (it.streaming || !/```/.test(it.text || '')) return;
    let n = 0;
    d.parts.text = pieces(it.text).map((p) => (p.code == null ? (p.md.trim() ? C.h.markdown(p.md) : '')
      : `<div class="ag-code"><div class="ag-cb"><span class="cap">${esc((p.lang || L('data.code')).toUpperCase())}</span><button type="button" class="ag-ib" data-a="data-copy-code" data-id="${esc(it.id)}" data-i="${n++}" aria-label="${E('data.copy_code')}">${ic('copy', 'i s')}</button></div><pre>${esc(p.code)}</pre></div>`)).join('');
  });
  C.on('data-copy-code', (t, x) => {
    const it = ((x.view || {}).thread || []).find((i) => i.kind === 'answer' && String(i.id) === t.dataset.id);
    const block = it && pieces(it.text).filter((p) => p.code != null)[Number(t.dataset.i)];
    if (block) x.copy(block.code, t);
    return true;
  });
});
