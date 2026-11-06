# Lingua Lab

Local multilingual AI safety chatbot for English, Russian and Kazakh. Llama 3 generates answers; an optional Qwen3 4B checker reviews them before display. Built as a Midterm project and extended for Assignment 3.

## Setup

Install Python 3 and Ollama. The web server uses only the Python standard library; no pip packages or paid API are required. Start Ollama, then download the models:

```sh
ollama pull llama3:latest
ollama pull qwen3:4b
```

Open a terminal in this repository folder and run:

```sh
python3 server.py
```

Visit http://127.0.0.1:8765/ . Keep the terminal open. On macOS, Start_Chatbot.command is an alternative launcher. Stop an older server before starting an updated copy. GitHub stores the source; GitHub Pages cannot run this Python/Ollama backend.

## Chat and safety evaluation

Choose Baseline or Protected instructions. Enable Qwen safety checker to review answers. Only a valid safe decision releases the candidate; unsafe, uncertain and failed checks withhold it. Ordinary chat does not expose blocked candidates. Models unload sequentially to reduce memory pressure on an 8 GB Mac; swapping still adds delay.

Faster chat is enabled by default in the browser: shorter Llama replies and decision-only Qwen review, with smaller contexts where input size permits. Turn it off for full-length research-style chat. It can change judgments and has not been benchmarked for accuracy or speed improvement.

Safety evaluation offers Baseline vs protected, or Protected vs protected with Qwen. Quick check runs rows 12, 41 and 61 in three languages and two settings (18 responses); full experiment runs 420. Each condition generates a fresh answer with alternating order. Evaluation always uses research settings, regardless of Faster chat.

Load saved results opens compatible paper-prompt JSON exports without inference. Export results saves answers and annotations. Browser results are held in memory: export before refresh or closing. The audit intentionally exposes original candidate text for research, alongside delivered text and Qwen judgments where available. AI judgments and human labels are separate. Refusal percentages are phrase matches, not attack success rates or validated safety scores.

## Configuration

Research generator: llama3:latest, temperature 0, seed 42, context 4096, output 256. Research reviewer: qwen3:4b, temperature 0, seed 42, context 8192, output 256, thinking disabled. Fast chat: generator output 128 and context 2048/4096; reviewer output 32 with context 2048/4096/8192 chosen conservatively from input size. The reviewer withholds inputs beyond its input-size guard rather than silently dropping conversation.

Tags may change. Record local model digests for reproducible experiments. Model files are downloaded separately and are not included here. Avoid concurrent chatbot and batch inference.

## Tests

```sh
python3 -m unittest test_api test_reviewer test_dataset test_performance
```

HTTP contract tests require local loopback access. Tests mock inference and are not experiment results. Offline checks cover dataset consistency, reviewer decisions, failure handling, context handling and separation of research/fast profiles. JavaScript syntax can be checked with `node --check static/app.js` if Node.js is installed; Node is not needed to run the website.

## Data and attribution

Source: Tang et al. (2025), *A Framework to Assess Multilingual Vulnerabilities of LLMs*, DOI https://doi.org/10.1145/3701716.3715581.

Original prompts: https://github.com/CarsonDon/Multilingual-Vuln-LLMs, commit c3b1e24306d6b82f09501e7b8be80db79c9f827e. The authors' 70 English rows are preserved; Russian and Kazakh are added machine translations, awaiting independent review. Duplicates and unusual wording are retained. data/upstream_allprompt.csv preserves the original source, including other languages; the app uses dataset.json for EN/RU/KK only.

Dataset attribution: © 2025 Likai Tang; CC BY 4.0 as stated by the upstream repository. Changes and hashes are recorded in data/provenance.json. Dataset licensing does not automatically assign a license to this application's code.

OpenAI Codex assisted with application code, tests and documentation. Qwen safety labels are model judgments, not independently verified human annotations. This experimental checker can miss harmful content and block harmless content; its explanations can be incorrect. The upload copy contains source and dataset provenance, not local logs, caches, private environment files or unfinished experiment runs.
