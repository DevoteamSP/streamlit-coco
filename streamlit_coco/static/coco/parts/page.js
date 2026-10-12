// Ask CoCo, part "page" (frames 75-78): a request a button of the application sent for the user. Its full text sits behind
// "Show full request"; the queued one says "Sent when you connect" (drawn by the core); a prompt that fills the field is the core's.
part('page', (C) => {
  const { esc, fold, L } = C.h;
  const full = (key, text) => (text ? fold(key, L('page.show_full'), L('page.hide_full'), `<pre class="pre">${esc(text)}</pre>`) : '');
  C.decorate.user.push((it, x, d) => { d.inner += full(`full:${it.id}`, it.full); });
  C.decorate.queued.push((q, x, d) => { d.inner += full(`full:q:${q.id}`, q.full); });
});
