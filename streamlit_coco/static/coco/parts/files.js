// Ask CoCo, part "files" (frames 70-74): attached files: the control, the lines above the field, a refusal and its reason,
// a drop on the window, the files sent with the message, the message while its files are saved. Shown only when the view has `attach`.
part('files', (C) => {
  const { esc, ic, L, E } = C.h;
  const S = C.state('files');   // files: [{name, size, data: base64 | null, bad, note}]; depth: how many drags are over the window
  S.files ||= [];
  S.depth ||= 0;
  C.h.icon('clip', '<path d="M21 12.5 12.5 21a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.8 1.8 0 0 1-2.6-2.6l8.3-8.3"/>');
  C.h.icon('file', '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5"/>');
  const size = (n) => L(n >= 1e6 ? 'files.mb' : 'files.kb', { n: n >= 1e6 ? +(n / 1e6).toFixed(1) : Math.round(n / 1000) });

  const add = (x, list) => {
    const a = x.view.attach, said = [];
    if (!a.multi) S.files = [];
    list.forEach((file) => {
      const f = { name: file.name, size: file.size, data: null, bad: '', note: '' };
      if (file.size > a.max_mb * 1e6) f.bad = L('files.too_big', { size: size(file.size), max: a.max_mb });
      else if (a.accept.length && !a.accept.some((ext) => file.name.toLowerCase().endsWith(ext.toLowerCase()))) f.bad = L('files.type');
      else if (S.files.some((r) => r.name === file.name && !r.bad)) f.bad = L('files.dup');
      else if (a.existing.includes(file.name)) f.note = L('files.replaces');
      S.files.push(f);
      if (f.bad) said.push(`${file.name}. ${f.bad}`);
      else {
        const reader = new FileReader();
        reader.onload = () => { f.data = String(reader.result).split(',')[1] || ''; x.repaint(); };
        reader.readAsDataURL(file);
      }
    });
    if (said.length) x.announce(said.join('. '));
    x.repaint();
  };
  const lines = () => S.files.map((f, i) => (f.bad
    ? `<div class="ag-file bad"><span class="ag-g">${ic('no')}</span><span class="ag-fn">${esc(f.name)}<span class="ag-n">${esc(f.bad)}</span></span>`
      + `<button type="button" class="ag-ib" data-a="file_remove" data-i="${i}" aria-label="${E('files.dismiss', { name: f.name })}">${ic('bad', 'i s')}</button></div>`
    : `<div class="ag-file"><span class="ag-g">${ic('file', 'i s')}</span><span class="ag-fn">${esc(f.name)}<span class="ag-n">${esc(size(f.size))}${f.note ? `. ${esc(f.note)}` : ''}</span></span>`
      + `<button type="button" class="ag-ib" data-a="file_remove" data-i="${i}" aria-label="${E('files.remove', { name: f.name })}">${ic('bad', 'i s')}</button></div>`)).join('');

  C.composer.push({
    top: (v) => (!v.attach ? '' : S.depth ? `<p class="ag-dz">${E('files.drop')}</p>` : S.files.length ? `<div class="ag-files">${lines()}</div>` : ''),
    left: (v) => (!v.attach ? '' : `<button type="button" class="ag-clip" data-a="attach" aria-label="${E('files.attach')}">${ic('clip', 'i s')}</button>`
      + `<input type="file" hidden${v.attach.multi ? ' multiple' : ''}${v.attach.accept.length ? ` accept="${esc(v.attach.accept.join(','))}"` : ''}>`),
    cls: (v) => (!v.attach ? '' : `ag-at${S.depth ? ' ag-drop' : ''}`),
  });
  C.sendable.push(() => S.files.some((f) => f.data != null));
  // the files go with the message; the ones still being read stay in the field, the refused ones are dropped
  C.collect.send.push(() => {
    const sent = S.files.filter((f) => f.data != null).map(({ name, size: n, data }) => ({ name, size: n, data }));
    S.files = S.files.filter((f) => f.data == null && !f.bad);
    return sent.length ? { files: sent } : {};
  });
  C.decorate.user.push((it, x, d) => {
    if (it.files?.length) d.parts.text += it.files.map((n) => `<span class="ag-att">${ic('file', 'i s')}<span>${esc(n)}</span></span>`).join('');
    if (it.sending) { d.cls += ' ag-qd'; d.inner += `<span class="ag-n">${E(it.sending === 1 ? 'files.sending_one' : 'files.sending_other', { n: it.sending })}</span>`; }
  });
  C.on('attach', (t, x) => { x.root.querySelector('.ag-fleft input[type=file]').click(); return true; });
  C.on('file_remove', (t, x) => {
    const i = Number(t.dataset.i);
    S.files.splice(i, 1);
    x.repaint();
    const rows = x.root.querySelectorAll('.ag-file .ag-ib');   // the focus stays in the list: the next file, else the previous, else the control
    (rows[i] || rows[i - 1] || x.root.querySelector('.ag-clip'))?.focus({ preventScroll: true });
    return true;
  });
  C.change.push((e, x) => {
    if (e.target.type !== 'file') return;
    const list = [...e.target.files];
    e.target.value = '';   // the same file can be chosen again after it was removed
    add(x, list);
  });
  C.init.push((x) => {
    const root = x.root, isFiles = (e) => !!x.view?.attach && [...(e.dataTransfer?.types || [])].includes('Files');
    root.addEventListener('dragenter', (e) => { if (!isFiles(e)) return; e.preventDefault(); if (S.depth++ === 0) x.repaint(); });
    root.addEventListener('dragover', (e) => { if (isFiles(e)) e.preventDefault(); });
    root.addEventListener('dragleave', () => { if (!S.depth) return; S.depth -= 1; if (!S.depth) x.repaint(); });
    root.addEventListener('drop', (e) => {
      if (!isFiles(e)) return;
      e.preventDefault();
      S.depth = 0;
      if (!x.el.fld.hidden) add(x, [...e.dataTransfer.files]);
    });
  });
});
