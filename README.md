# flx-demo-apps

Public source for small demo apps deployed onto the [FLX application
hosting platform](https://github.com/fluxraum/poc-flx-application-hosting-service)
via its catalog templates (e.g. the `streamlit` template).

This repo is deliberately **public** and separate from the platform's
own (private) infra repo: GHCR container packages inherit their source
repo's visibility, and the platform's cluster nodes need to pull these
images without a per-app pull secret. Nothing sensitive belongs here --
if an app needs a secret at runtime, that's wired in at deploy time via
the platform's control-plane, not committed here.

## Layout

Each `apps/<name>/` directory is a self-contained image: a `Dockerfile`
plus whatever source it needs. `.github/workflows/build.yml` builds and
pushes every entry listed in its matrix to
`ghcr.io/fluxraum/<name>:latest` on every push to `main`.

## Apps

- **four-eyes-demo** -- a maker-checker (Vier-Augen-Prinzip) demo: whoever
  submits a request can't approve it themselves, enforced against the
  real logged-in identity forwarded by the platform's oauth2-proxy
  (`X-Auth-Request-Email`), not a fake user picker.
