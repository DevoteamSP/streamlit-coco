# Feature: Pluggable text renderer

## What

`panel()`, `render_transcript()`, and `render_output_field()` accept `text_renderer=` so apps can render assistant/user content with any Streamlit text API (or a custom callable) instead of hardcoded `st.markdown`.

## Why

Some apps prefer plain `st.text`, `st.write`, or a custom sanitizer / highlighter.

## How to use

```python
st_coco.panel(session, text_renderer="text")
st_coco.render_transcript(session, text_renderer=st.write)
st_coco.render_output_field(session, text_renderer="caption")
```

Named values: `markdown` (default), `write`, `text`, `caption`, `code` (also accept `st.*` prefixes).

## Limitations

- Tool cards and status chrome still use their own Streamlit widgets.
- CCv2 `chat()` transcript remains plain text in the component DOM.

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
