# I want to add file uploads

**For** a developer letting users hand files to the agent · **10 min** · **a working minimal app**

You end up with a way for the app's user to upload files into the agent's
working directory, either from the chat input bar or a dedicated sidebar
uploader.

## Before you start

- A working minimal app ([I want to build a minimal CoCo app](task-build-a-minimal-app.html)).
- Decide the target directory: uploads land under `CocoOptions.cwd` in a
  subdirectory (`_uploads` by default).

## Steps

1. To accept files from the chat input bar directly, set `accept_file` on
   `chat_input_bar()`:

   ```python
   prompt = st_coco.chat_input_bar(
       session,
       accept_file=True,           # or "multiple"
       upload_subdir="_uploads",
       upload_overwrite="replace",  # "error" / "replace" / "skip"
   )
   ```

   With `inject_upload_paths=True` (the default), the uploaded files' paths
   are appended to the prompt text sent to the agent.

2. To offer a standalone uploader (for example in a sidebar), use
   `cwd_uploader()` instead:

   ```python
   with st.sidebar:
       uploaded = st_coco.cwd_uploader(
           session,
           label="Upload a reference file",
           overwrite="error",
       )
   ```

   `cwd_uploader()` wraps `st.file_uploader` and calls `upload_to_cwd()` for
   you, and shows a caption listing what is already in the upload directory.

3. To upload files outside a Streamlit widget entirely (for example files
   already read into memory), call `upload_to_cwd()` directly:

   ```python
   from streamlit_coco import upload_to_cwd

   paths = upload_to_cwd(
       session,                 # or a CocoOptions, or a raw path
       files,
       subdir="_uploads",
       overwrite="error",
   )
   ```

## Result

Uploaded files are written under `<CocoOptions.cwd>/_uploads/` (or the
`subdir`/`upload_subdir` you set), and are then available to any agent tool
that reads from `cwd`. `cwd_uploader()` and `upload_to_cwd()` both return the
list of `UploadedPath` results for the files just written.

## Variations

- `upload_to_cwd()` defaults to `overwrite="error"` (reject a name clash);
  `chat_input_bar()` defaults `upload_overwrite="replace"` — set either
  explicitly if the default for your entry point is not what you want.
- File size and extension are checked against `DEFAULT_MAX_BYTES` (10 MiB)
  and a fixed allowlist of safe document/data extensions
  (`streamlit_coco.upload.DEFAULT_ALLOWED_EXTENSIONS`) unless you pass your
  own `max_bytes` / `allowed_extensions`.

## If it fails

- [Upload rejected: extension](../../technical-guide/help.html#upload-rejected-extension)
- [Upload rejected: size](../../technical-guide/help.html#upload-rejected-size)
- [Upload name conflict](../../technical-guide/help.html#upload-name-conflict)
