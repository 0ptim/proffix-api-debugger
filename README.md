# Proffix API Debugger

A small, browser-based tool for testing and debugging requests against the Proffix REST API.

This project keeps the app intentionally simple. Its HTML lives in `index.html`,
with locally served CSS and JavaScript assets for compatibility with the Proffix
Content Security Policy.

## What it includes

- Lightweight UI for manual API testing
- Precompiled Tailwind CSS v4
- Inline Phosphor Icons in the light weight
- Locally served jQuery managed through npm
- No runtime build step

## Run it

1. Run `npm ci`.
2. Open `index.html` in your browser.
3. Enter your API details.
4. Send requests and inspect the responses.

## Deploy debugger into installed Proffix REST API versions

Use the included python script to copy this repository's `index.html` into every detected API version folder under the installed Proffix REST API `Assemblies` directory.

- Default run (auto-discovery):
  - `python deploy_debugger.py`
- Preview only (no changes):
  - `python deploy_debugger.py --dry-run`
- Explicit known path (your machine):
  - `python deploy_debugger.py --assemblies "C:\Program Files\Proffix REST API\Proffix REST API\Assemblies"`
- One specific version:
  - `python deploy_debugger.py --version 4.84.1`

When `--assemblies` is supplied, only that directory is used. Automatic
discovery is disabled for that run.

Run `npm ci` before deploying. The deployment copies jQuery from its npm package
along with the required local assets and third-party notices next to the
deployed HTML file. For modern installations, it also changes the local HTML
base path to `/debugger/`, matching the route used by Proffix.
Deployments also remove the obsolete `debugger-vendor/` directory created by
earlier versions of this project.

## Rebuild CSS

After changing classes or `debugger.source.css`:

1. Run `npm ci`.
2. Run `npm run build:css`.

## Notes

- This is an enhanced, cleaned-up take on the original Proffix debugger.
- Proffix 4.84.1 introduced a restrictive Content Security Policy. Modern
  versions require the `__CSP_NONCE__` placeholder on executable HTML elements.
  The deploy script validates the placeholder and all local assets before it
  replaces a modern `debugger/index.html` file.
- Because it runs in the browser, behavior still depends on your API/CORS setup.
