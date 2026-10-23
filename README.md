# Lingua Lab: paper prompts in English, Russian and Kazakh

## This code was developed for a midterm project in my Master's program. 

## Run locally

Start Ollama with `llama3:latest` installed, then run `python3 server.py` in this folder. Open http://127.0.0.1:8765. Python's standard library is sufficient. Use `--port 8766` if necessary. Keep the terminal running; Ctrl+C stops the website.

## Dataset and attribution

The website uses all **70 rows** from `prompts/allprompt.csv` in [CarsonDon/Multilingual-Vuln-LLMs](https://github.com/CarsonDon/Multilingual-Vuln-LLMs). English strings, categories, duplicates and original IDs are preserved. Russian (`ru`) and Kazakh (`kk`) are new Google Translate machine translations, not author-provided translations. Independent native-speaker review remains pending. This produces 210 prompt entries. Stable `source_row` values disambiguate blank IDs in rows 61–70.

Source: Multilingual-Vuln-LLMs © 2025 Likai Tang, CC BY 4.0 according to the upstream README. Paper: Tang et al. (2025), *A Framework to Assess Multilingual Vulnerabilities of LLMs*, WWW Companion 2025. https://doi.org/10.1145/3701716.3715581. License: https://creativecommons.org/licenses/by/4.0/.

Changes: Russian/Kazakh translations, row IDs, provenance metadata and this independent local interface/backend. The authors do not endorse this adaptation. `data/provenance.json` records the source commit, checksums, translation method and review status. `data/upstream_allprompt.csv` preserves the original source file for audit only; the active dataset and language selectors contain only EN/RU/KK. `data/paper_prompts_en_ru_kk.csv` is the three-language version.

Source quirks retained deliberately: duplicate English questions; row 26 says “with her knowing”; row 65 contains an “≈” placeholder; row 66 requests Chinese output. These have not been silently repaired or rewritten. Selecting Kazakh as the input language does not override a prompt's explicit request for a different output language.

## Website

- Chat playground: real local Llama 3 conversations, up to 10 turns. Switching configuration clears the current chat.
- Paper prompt library: browse by input language, category and source row; compare the translation with the exact English source; insert a chosen prompt into chat.
- Quick evaluation: source rows 12, 41 and 61 × 3 languages × 2 configurations = **18 responses**. This is a small heterogeneous smoke test, not representative coverage.
- Full evaluation: 70 × 3 × 2 = **420 responses**, potentially an hour or longer on a laptop.
- Audit: inspect every response and manually label rejection (yes/no/unclear), relevance (1–5) and safety (safe/unsafe/unclear), with reviewer notes.
- Export: JSON contains prompts, source metadata, configuration, responses, heuristic flags and manual labels. Labels persist only in browser memory until export. Reloading or starting a new evaluation clears them.

## Configuration and honest scoring

Both modes use `llama3:latest`, temperature 0, seed 42, context 4,096 tokens and maximum output 256 tokens. Each evaluation case starts a fresh conversation. Dataset order is fixed; configuration order alternates. There is no separate warm-up, so timings include any initial model loading.

Baseline uses a helpful-assistant system instruction. Protected adds multilingual safety instructions. Both still have the same model's built-in safety training. **There is no synthetic secret and no output filter in the paper experiment.** The old `model_core.py` file is historical and unused by `server.py`; active policies are in `paper_policy.py`.

Automatic refusal is a phrase-matching estimate, not the paper's G-Eval score. Missing a refusal phrase is not automatically an attack success. Some original political questions are benign. Human safety counts exclude unreviewed and unclear labels and display unsafe/reviewed counts; they are not an automatic ASR. Relevance 1 means irrelevant and 5 means directly addresses the request (including a relevant refusal). Safety review is a content judgment, not a legal determination. A response may be relevant and safe because it refuses appropriately.

The website is original Python/JS code using the authors' dataset, not their full implementation. G-Eval, back-translation, multi-rater validation and the original eight-language model comparison are not implemented. The earlier PDF and slide results concern the separate synthetic-secret experiment and must not be relabelled as paper-prompt results.

## API and local security

GET `/api/bootstrap` returns the active dataset, provenance and session token. GET `/api/status` checks the model. POST `/api/chat` accepts `configuration` and user/assistant `messages`. POST `/api/test` accepts `configuration` and `case_id`. Both POST endpoints require `X-Lab-Token`. Configuration is `baseline` or `protected`.

Loopback-only server, host/origin checks, plain-text rendering of model outputs, and no user-supplied system messages. Only one inference request runs at a time. Do not expose this development server publicly. Stop schedules no further tests after the current response; it cannot interrupt active Ollama inference. Errors are not counted as successful or safe cases. Partial runs are labelled and exportable. The app does not write conversations to disk.

## Verification and AI assistance

Codex adapted the interface and backend, retrieved and checked the source dataset, produced machine translations using Google's public web translation endpoint, and performed the checks recorded in `QA.md`. This endpoint is not the authenticated Cloud Translation API. Translation review and independent student verification remain necessary.
