# Je veux ajouter des téléversements de fichiers

**Pour** un développeur laissant les utilisateurs remettre des fichiers à l'agent · **10 min** · **une app minimale fonctionnelle**

Vous obtenez un moyen pour l'utilisateur de l'app de téléverser des fichiers
dans le répertoire de travail de l'agent, soit depuis la barre de saisie du
chat, soit via un téléverseur dédié dans la barre latérale.

## Avant de commencer

- Une app minimale fonctionnelle ([Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)).
- Décider du répertoire cible : les téléversements atterrissent sous
  `CocoOptions.cwd` dans un sous-répertoire (`_uploads` par défaut).

## Étapes

1. Pour accepter des fichiers directement depuis la barre de saisie du chat,
   définissez `accept_file` sur `chat_input_bar()` :

   ```python
   prompt = st_coco.chat_input_bar(
       session,
       accept_file=True,           # ou "multiple"
       upload_subdir="_uploads",
       upload_overwrite="replace",  # "error" / "replace" / "skip"
   )
   ```

   Avec `inject_upload_paths=True` (le défaut), les chemins des fichiers
   téléversés sont ajoutés au texte du prompt envoyé à l'agent.

2. Pour proposer un téléverseur autonome (par exemple dans une barre
   latérale), utilisez plutôt `cwd_uploader()` :

   ```python
   with st.sidebar:
       uploaded = st_coco.cwd_uploader(
           session,
           label="Upload a reference file",
           overwrite="error",
       )
   ```

   `cwd_uploader()` encapsule `st.file_uploader` et appelle
   `upload_to_cwd()` pour vous, et affiche une légende listant ce qui se
   trouve déjà dans le répertoire de téléversement.

3. Pour téléverser des fichiers entièrement en dehors d'un widget Streamlit
   (par exemple des fichiers déjà lus en mémoire), appelez directement
   `upload_to_cwd()` :

   ```python
   from streamlit_coco import upload_to_cwd

   paths = upload_to_cwd(
       session,                 # ou un CocoOptions, ou un chemin brut
       files,
       subdir="_uploads",
       overwrite="error",
   )
   ```

## Résultat

Les fichiers téléversés sont écrits sous `<CocoOptions.cwd>/_uploads/` (ou
le `subdir`/`upload_subdir` que vous avez défini), et sont ensuite
disponibles pour tout outil de l'agent lisant depuis `cwd`. `cwd_uploader()`
et `upload_to_cwd()` retournent tous deux la liste des résultats
`UploadedPath` pour les fichiers qui viennent d'être écrits.

## Variations

- `upload_to_cwd()` a pour défaut `overwrite="error"` (rejeter un conflit de
  nom) ; `chat_input_bar()` a pour défaut `upload_overwrite="replace"` —
  définissez l'un ou l'autre explicitement si le défaut de votre point
  d'entrée n'est pas celui que vous voulez.
- La taille et l'extension des fichiers sont vérifiées par rapport à
  `DEFAULT_MAX_BYTES` (10 Mio) et à une liste blanche fixe d'extensions de
  documents/données sûres (`streamlit_coco.upload.DEFAULT_ALLOWED_EXTENSIONS`),
  sauf si vous passez vos propres `max_bytes` / `allowed_extensions`.

## En cas d'échec

- [Téléversement rejeté : extension](../../technical-guide/help.html#upload-rejected-extension)
- [Téléversement rejeté : taille](../../technical-guide/help.html#upload-rejected-size)
- [Conflit de nom de téléversement](../../technical-guide/help.html#upload-name-conflict)
