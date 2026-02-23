# Proffix API Debugger

A small, browser-based tool for testing and debugging requests against the Proffix REST API.

This project keeps things intentionally simple: the whole app lives in a single `index.html` file.

## What it includes

- Lightweight UI for manual API testing
- Tailwind CSS v4 (via browser runtime)
- Bootstrap Icons (via CDN)
- No build step

## Run it

1. Open `index.html` in your browser.
2. Enter your API details.
3. Send requests and inspect the responses.

## Deploy debugger into installed Proffix REST API versions

Use the included python script to copy this repository's `index.html` into every detected API version folder under the installed Proffix REST API `Assemblies` directory.

- Default run (auto-discovery):
  - `python deploy_debugger.py`
- Preview only (no changes):
  - `python deploy_debugger.py --dry-run`
- Explicit known path (your machine):
  - `python deploy_debugger.py --assemblies "C:\Program Files\Proffix REST API\Proffix REST API\Assemblies"`

## Notes

- This is an enhanced, cleaned-up take on the original Proffix debugger.
- Because it runs in the browser, behavior still depends on your API/CORS setup.
