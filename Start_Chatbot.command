#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if /usr/bin/curl --fail --silent --max-time 2 http://127.0.0.1:8765/api/bootstrap >/dev/null; then
  /usr/bin/open 'http://127.0.0.1:8765/#tests'
  echo 'The chatbot server is already running.'
  exit 0
fi
if ! command -v python3 >/dev/null; then
  echo 'Python 3 is required. Install Python 3 and try again.'
  read '?Press Enter to close.'
  exit 1
fi
echo 'Starting Lingua Lab at http://127.0.0.1:8765'
echo 'Keep this terminal window open. Press Control+C to stop.'
echo 'Start the Ollama application to enable model responses.'
python3 server.py
read '?Server stopped. Press Enter to close.'
