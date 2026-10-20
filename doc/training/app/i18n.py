"""UI strings for the training navigator (EN / FR / ES)."""

from __future__ import annotations

LANGS = ("en", "fr", "es")

LANG_LABEL = {"en": "EN", "fr": "FR", "es": "ES"}

LANG_FLAG = {"en": "🇬🇧", "fr": "🇫🇷", "es": "🇪🇸"}

LANG_NAME = {"en": "English", "fr": "français", "es": "español"}

TRACK_ORDER = (
    "enablement",
    "training",
    "certifications",
    "user-guide",
    "technical-guide",
)

TRACK_ICON = {
    "enablement": ":material/rocket_launch:",
    "training": ":material/school:",
    "certifications": ":material/workspace_premium:",
    "user-guide": ":material/menu_book:",
    "technical-guide": ":material/construction:",
}

TRACK_BADGE = {
    "enablement": "red",
    "training": "blue",
    "certifications": "violet",
    "user-guide": "orange",
    "technical-guide": "gray",
}

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Training",
        "brand": "Creative tech for Better Change",
        "language": "Language",
        "track": "Track",
        "document": "Document",
        "empty": "No documents in this track for the selected language.",
        "no_pack": "No training.yml next to this app. Run `$asset-owner-training` first.",
        "quiz_submit": "Score quiz",
        "quiz_reset": "Reset answers",
        "quiz_pass": "Passed",
        "quiz_fail": "Below the pass mark — review the track and retry.",
        "quiz_score": "Score",
        "enablement": "Enablement",
        "training": "Training",
        "certifications": "Certifications",
        "user-guide": "User Guide",
        "technical-guide": "Technical Guide",
        "home": "Home",
        "open": "Open",
        "start": "Start here",
        "back": "Back",
        "hero_kicker": "Training",
        "hero_welcome": "{name}",
        "hero_sub": (
            "Enablement, practice cases, certifications, and the product guides — in your language."
        ),
        "path_title": "Suggested path",
        "path_1_hint": "Set up, tour, demo",
        "path_2_hint": "Three use cases",
        "path_3_hint": "Prove it",
        "explore": "Explore the pack",
        "routes_title": "What are you here to do?",
        "explore_by_track": "Explore by track",
        "route_step": "{track} · Step {n} of {total} — route “{title}”",
        "route_next": "Next",
        "route_back": "Back to the five routes",
        "route_done": "You're done:",
        "scope_title": "Not covered here",
        "contact_title": "If you're stuck",
        "reference": "Reference",
        "docs_n": "{n} documents",
        "quiz_n": "{n} quizzes",
        "pages_n": "{n} pages",
        "blurb_enablement": "Get ready to run and demo {name}.",
        "blurb_training": "Three use cases — guided, then yours, then broken.",
        "blurb_certifications": "Pass the quiz for the track you just completed.",
        "blurb_user-guide": "Tasks, reference, and answers for everyday use.",
        "blurb_technical-guide": "How it is built, run, and extended.",
        "includes_enablement": (
            "Intro, setup, a guided tour of the running product, hands-on exercises, and "
            "a 10-minute demo script."
        ),
        "includes_training": (
            "Simple (guided), intermediate (your data), then advanced (it breaks — you "
            "diagnose from the Technical Guide)."
        ),
        "includes_certifications": (
            "Enablement: 10 questions, pass 8/10. User, Advanced, and Expert: 30 "
            "questions, pass 24/30."
        ),
        "includes_user-guide": (
            "Concepts, getting started, one page per task, reference for every screen, "
            "command and skill, outputs, and FAQ."
        ),
        "includes_technical-guide": (
            "Architecture, install, configuration, security, operations, data contracts, "
            "release, testing, extending, limits, and help by symptom."
        ),
        "time_enablement": "~2 h",
        "time_training": "~2 h",
        "time_certifications": "10–30 questions",
        "time_user-guide": "Look up",
        "time_technical-guide": "Look up",
        "group_start": "Start here",
        "group_start_hint": "What it is, the vocabulary, and a first run.",
        "group_tasks": "Tasks",
        "group_tasks_hint": "One page per job: steps, result, and what to do if it fails.",
        "group_reference": "Reference",
        "group_reference_hint": "Every screen, command, skill, and output — looked up, not read.",
        "group_answers": "Answers",
        "group_answers_hint": "Short answers, known limits, and help by symptom.",
        "group_understand": "Understand",
        "group_understand_hint": "Components, data flow, and the rules that must not break.",
        "group_run": "Run",
        "group_run_hint": "Install, configure, secure, operate, and upgrade.",
        "group_build": "Build on it",
        "group_build_hint": "Data contracts, tests, and extension points.",
        "group_more": "More",
        "group_more_hint": "Other pages in this guide.",
        "previous": "Previous",
        "next": "Next",
        "metric_tracks": "Tracks",
        "metric_docs": "Documents",
        "metric_langs": "Languages",
        "you_are_here": "You are here",
        "pass_mark": "Pass {score}",
        "coco_open": "CoCo",
        "coco_close": "Close CoCo",
        "coco_ask": "Ask CoCo",
        "coco_placeholder": "Ask about this pack — CoCo reads the Markdown in doc/training/",
        "coco_missing": "CoCo needs **streamlit-coco**. The pack still browses without it.",
        "coco_install": "Restart with `streamlit-coco[sdk]` (the Make target already does):",
        "coco_q_start": "Where do I start?",
        "coco_q_start_q": (
            "Read training.yml and recommend a starting path through this pack. Answer in"
            " {lang}. Stay inside this folder."
        ),
        "coco_q_path": "Suggested path",
        "coco_q_path_q": (
            "Read enablement/intro.md and summarize what Enablement covers, then what to "
            "do next. Answer in {lang}."
        ),
        "coco_q_track": "What's in this track?",
        "coco_q_track_q": (
            "List the documents in the `{track}` track (see training.yml) and what each "
            "is for. Answer in {lang}."
        ),
        "coco_q_explain": "Explain this page",
        "coco_q_explain_q": (
            "Read `{source}` and explain the key points. Answer in {lang}. Do not invent "
            "product behaviour."
        ),
        "coco_q_next": "What next?",
        "coco_q_next_q": (
            "I just read `{source}`. What should I open next in this pack? Check "
            "training.yml. Answer in {lang}."
        ),
        "coco_caption": "cwd is this pack. Read / Glob / Grep only.",
        "coco_connect": "Connect a Snowflake CLI profile. CoCo answers from the training Markdown.",
    },
    "fr": {
        "title": "Formation",
        "brand": "Creative tech for Better Change",
        "language": "Langue",
        "track": "Parcours",
        "document": "Document",
        "empty": "Aucun document dans ce parcours pour la langue choisie.",
        "no_pack": "Pas de training.yml à côté de cette app. Lancez `$asset-owner-training`.",
        "quiz_submit": "Noter le quiz",
        "quiz_reset": "Réinitialiser",
        "quiz_pass": "Réussi",
        "quiz_fail": "Sous le seuil — revoir le parcours et réessayer.",
        "quiz_score": "Score",
        "enablement": "Enablement",
        "training": "Training",
        "certifications": "Certifications",
        "user-guide": "Guide utilisateur",
        "technical-guide": "Guide technique",
        "home": "Accueil",
        "open": "Ouvrir",
        "start": "Commencer ici",
        "back": "Retour",
        "hero_kicker": "Formation",
        "hero_welcome": "{name}",
        "hero_sub": (
            "Enablement, cas pratiques, certifications et guides produit — dans votre langue."
        ),
        "path_title": "Parcours suggéré",
        "path_1_hint": "Installer, visiter, démontrer",
        "path_2_hint": "Trois cas d'usage",
        "path_3_hint": "Le prouver",
        "explore": "Explorer le pack",
        "routes_title": "Qu'est-ce que vous venez faire ?",
        "explore_by_track": "Explorer par parcours",
        "route_step": "{track} · Étape {n} sur {total} du parcours « {title} »",
        "route_next": "Ensuite",
        "route_back": "Revenir aux cinq parcours",
        "route_done": "Vous y êtes :",
        "scope_title": "Ce que ça ne couvre pas",
        "contact_title": "Si vous restez bloqué",
        "reference": "Référence",
        "docs_n": "{n} documents",
        "quiz_n": "{n} quiz",
        "pages_n": "{n} pages",
        "blurb_enablement": "Être prêt à faire tourner et démontrer {name}.",
        "blurb_training": "Trois cas — guidé, puis le vôtre, puis cassé.",
        "blurb_certifications": "Valider le quiz du parcours que vous venez de finir.",
        "blurb_user-guide": "Tâches, référence et réponses pour l'usage quotidien.",
        "blurb_technical-guide": "Comment c'est construit, exploité et étendu.",
        "includes_enablement": (
            "Intro, setup, visite guidée du produit, exercices pratiques et un script de "
            "démo de 10 minutes."
        ),
        "includes_training": (
            "Simple (guidé), intermédiaire (vos données), puis avancé (ça casse — vous "
            "diagnostiquez avec le Guide technique)."
        ),
        "includes_certifications": (
            "Enablement : 10 questions, seuil 8/10. User, Advanced et Expert : 30 "
            "questions, seuil 24/30."
        ),
        "includes_user-guide": (
            "Concepts, démarrage, une page par tâche, référence de chaque écran, commande"
            " et skill, sorties, et FAQ."
        ),
        "includes_technical-guide": (
            "Architecture, installation, configuration, sécurité, exploitation, contrats "
            "de données, release, tests, extension, limites, et aide par symptôme."
        ),
        "time_enablement": "~2 h",
        "time_training": "~2 h",
        "time_certifications": "10–30 questions",
        "time_user-guide": "Consulter",
        "time_technical-guide": "Consulter",
        "group_start": "Pour commencer",
        "group_start_hint": "Ce que c'est, le vocabulaire et une première utilisation.",
        "group_tasks": "Tâches",
        "group_tasks_hint": "Une page par tâche : étapes, résultat, et que faire en cas d'échec.",
        "group_reference": "Référence",
        "group_reference_hint": (
            "Chaque écran, commande, skill et sortie — à consulter plutôt qu'à lire."
        ),
        "group_answers": "Réponses",
        "group_answers_hint": "Réponses courtes, limites connues et aide par symptôme.",
        "group_understand": "Comprendre",
        "group_understand_hint": "Composants, flux de données et règles à ne pas casser.",
        "group_run": "Exploiter",
        "group_run_hint": "Installer, configurer, sécuriser, exploiter et mettre à jour.",
        "group_build": "Faire évoluer",
        "group_build_hint": "Contrats de données, tests et points d'extension.",
        "group_more": "Autres pages",
        "group_more_hint": "Autres pages de ce guide.",
        "previous": "Précédent",
        "next": "Suivant",
        "metric_tracks": "Parcours",
        "metric_docs": "Documents",
        "metric_langs": "Langues",
        "you_are_here": "Vous êtes ici",
        "pass_mark": "Seuil {score}",
        "coco_open": "CoCo",
        "coco_close": "Fermer CoCo",
        "coco_ask": "Demander à CoCo",
        "coco_placeholder": (
            "Posez une question sur le pack — CoCo lit le Markdown dans doc/training/"
        ),
        "coco_missing": "CoCo a besoin de **streamlit-coco**. Le pack se parcourt sans lui.",
        "coco_install": "Relancez avec `streamlit-coco[sdk]` (la cible Make le fait déjà) :",
        "coco_q_start": "Par où commencer ?",
        "coco_q_start_q": (
            "Lis training.yml et recommande un parcours de départ. Réponds en {lang}. "
            "Reste dans ce dossier."
        ),
        "coco_q_path": "Parcours suggéré",
        "coco_q_path_q": (
            "Lis enablement/intro.md, résume l'Enablement, puis la suite. Réponds en {lang}."
        ),
        "coco_q_track": "Que contient ce parcours ?",
        "coco_q_track_q": (
            "Liste les documents du parcours `{track}` (voir training.yml) et leur rôle. "
            "Réponds en {lang}."
        ),
        "coco_q_explain": "Expliquer cette page",
        "coco_q_explain_q": (
            "Lis `{source}` et explique les points clés. Réponds en {lang}. N'invente pas"
            " le produit."
        ),
        "coco_q_next": "Et ensuite ?",
        "coco_q_next_q": (
            "Je viens de lire `{source}`. Quelle page ouvrir ensuite ? Consulte "
            "training.yml. Réponds en {lang}."
        ),
        "coco_caption": "cwd = ce pack. Read / Glob / Grep seulement.",
        "coco_connect": "Connectez un profil Snowflake CLI. CoCo répond à partir du Markdown.",
    },
    "es": {
        "title": "Formación",
        "brand": "Creative tech for Better Change",
        "language": "Idioma",
        "track": "Itinerario",
        "document": "Documento",
        "empty": "No hay documentos en este itinerario para el idioma elegido.",
        "no_pack": "No hay training.yml junto a esta app. Ejecute `$asset-owner-training`.",
        "quiz_submit": "Corregir el quiz",
        "quiz_reset": "Reiniciar",
        "quiz_pass": "Aprobado",
        "quiz_fail": "Por debajo del umbral — revise el itinerario e inténtelo de nuevo.",
        "quiz_score": "Puntuación",
        "enablement": "Enablement",
        "training": "Training",
        "certifications": "Certificaciones",
        "user-guide": "Guía de usuario",
        "technical-guide": "Guía técnica",
        "home": "Inicio",
        "open": "Abrir",
        "start": "Empezar aquí",
        "back": "Volver",
        "hero_kicker": "Formación",
        "hero_welcome": "{name}",
        "hero_sub": (
            "Enablement, casos prácticos, certificaciones y guías del producto — en su idioma."
        ),
        "path_title": "Itinerario sugerido",
        "path_1_hint": "Instalar, recorrer, demostrar",
        "path_2_hint": "Tres casos de uso",
        "path_3_hint": "Demostrarlo",
        "explore": "Explorar el pack",
        "routes_title": "¿Qué viene a hacer?",
        "explore_by_track": "Explorar por itinerario",
        "route_step": "{track} · Paso {n} de {total} — itinerario « {title} »",
        "route_next": "Siguiente",
        "route_back": "Volver a los cinco itinerarios",
        "route_done": "Ya está:",
        "scope_title": "Lo que esto no cubre",
        "contact_title": "Si se queda atascado",
        "reference": "Referencia",
        "docs_n": "{n} documentos",
        "quiz_n": "{n} quizzes",
        "pages_n": "{n} páginas",
        "blurb_enablement": "Prepárese para ejecutar y demostrar {name}.",
        "blurb_training": "Tres casos — guiado, luego el suyo, luego roto.",
        "blurb_certifications": "Apruebe el quiz del itinerario que acaba de terminar.",
        "blurb_user-guide": "Tareas, referencia y respuestas para el uso diario.",
        "blurb_technical-guide": "Cómo se construye, se opera y se extiende.",
        "includes_enablement": (
            "Intro, setup, visita guiada del producto, ejercicios prácticos y un guion de"
            " demo de 10 minutos."
        ),
        "includes_training": (
            "Simple (guiado), intermedio (sus datos), luego avanzado (se rompe — "
            "diagnostica con la Guía técnica)."
        ),
        "includes_certifications": (
            "Enablement: 10 preguntas, umbral 8/10. User, Advanced y Expert: 30 "
            "preguntas, umbral 24/30."
        ),
        "includes_user-guide": (
            "Conceptos, primeros pasos, una página por tarea, referencia de cada "
            "pantalla, comando y skill, salidas y FAQ."
        ),
        "includes_technical-guide": (
            "Arquitectura, instalación, configuración, seguridad, operación, contratos de"
            " datos, release, pruebas, extensión, límites y ayuda por síntoma."
        ),
        "time_enablement": "~2 h",
        "time_training": "~2 h",
        "time_certifications": "10–30 preguntas",
        "time_user-guide": "Consultar",
        "time_technical-guide": "Consultar",
        "group_start": "Para empezar",
        "group_start_hint": "Qué es, el vocabulario y un primer uso.",
        "group_tasks": "Tareas",
        "group_tasks_hint": "Una página por tarea: pasos, resultado y qué hacer si falla.",
        "group_reference": "Referencia",
        "group_reference_hint": (
            "Cada pantalla, comando, skill y salida — para consultar, no para leer."
        ),
        "group_answers": "Respuestas",
        "group_answers_hint": "Respuestas cortas, límites conocidos y ayuda por síntoma.",
        "group_understand": "Entender",
        "group_understand_hint": "Componentes, flujo de datos y reglas que no deben romperse.",
        "group_run": "Operar",
        "group_run_hint": "Instalar, configurar, asegurar, operar y actualizar.",
        "group_build": "Extender",
        "group_build_hint": "Contratos de datos, pruebas y puntos de extensión.",
        "group_more": "Más páginas",
        "group_more_hint": "Otras páginas de esta guía.",
        "previous": "Anterior",
        "next": "Siguiente",
        "metric_tracks": "Itinerarios",
        "metric_docs": "Documentos",
        "metric_langs": "Idiomas",
        "you_are_here": "Está aquí",
        "pass_mark": "Umbral {score}",
        "coco_open": "CoCo",
        "coco_close": "Cerrar CoCo",
        "coco_ask": "Preguntar a CoCo",
        "coco_placeholder": "Pregunte por el pack — CoCo lee el Markdown en doc/training/",
        "coco_missing": "CoCo necesita **streamlit-coco**. El pack se recorre sin él.",
        "coco_install": "Reinicie con `streamlit-coco[sdk]` (el target Make ya lo hace):",
        "coco_q_start": "¿Por dónde empiezo?",
        "coco_q_start_q": (
            "Lee training.yml y recomienda un itinerario de inicio. Responde en {lang}. "
            "Quédate en esta carpeta."
        ),
        "coco_q_path": "Itinerario sugerido",
        "coco_q_path_q": (
            "Lee enablement/intro.md, resume Enablement y qué sigue. Responde en {lang}."
        ),
        "coco_q_track": "¿Qué hay en este itinerario?",
        "coco_q_track_q": (
            "Lista los documentos del itinerario `{track}` (ver training.yml) y para qué "
            "sirven. Responde en {lang}."
        ),
        "coco_q_explain": "Explicar esta página",
        "coco_q_explain_q": (
            "Lee `{source}` y explica los puntos clave. Responde en {lang}. No inventes "
            "el producto."
        ),
        "coco_q_next": "¿Y ahora?",
        "coco_q_next_q": (
            "Acabo de leer `{source}`. ¿Qué abro después? Mira training.yml. Responde en {lang}."
        ),
        "coco_caption": "cwd = este pack. Solo Read / Glob / Grep.",
        "coco_connect": "Conecte un perfil Snowflake CLI. CoCo responde desde el Markdown.",
    },
}


def t(lang: str, key: str) -> str:
    bundle = STRINGS.get(lang) or STRINGS["en"]
    return bundle.get(key) or STRINGS["en"].get(key, key)
