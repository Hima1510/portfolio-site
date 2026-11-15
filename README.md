# portfolio-site

A personal portfolio website (static HTML/CSS/JS served by nginx) for testing the
**Predictive Auto Deployment Platform**. All names, companies and project links are
sample content; edit `site/index.html` to make it yours.

## How it meets the platform's requirements

| SRS requirement | Where it is met |
|---|---|
| FR2 - repository must contain a Dockerfile | `Dockerfile` in the repo root |
| FR5 - run the test suite during the build | `tests/test_site.py` runs in the Dockerfile's `test` stage; a failing test fails `docker build` |
| FR6 - build image from the Dockerfile | Multi-stage build: test, stamp version, nginx runtime (non-root, port 8080) |
| FR7 / FR8 - commit and build metadata | HTML, CSS, JS, nginx config and tests live in separate files, so commits vary in files and lines changed |
| FR10 - deploy to isolated K8s namespace | `k8s/deployment.yaml`, `k8s/service.yaml` (no hard-coded namespace) |
| FR11 - live health and traffic metrics | `/healthz` for probes, `/nginx_status` (cluster-internal) for connection/request counters; CPU and memory come from Kubernetes; error rate and latency come from probing `/` |
| FR13 / FR16 - rollback | `/version.json` and the footer show which release is live, so you can confirm a rollback |

## Run locally

```bash
docker build -t portfolio-site \
  --build-arg APP_VERSION=1.0.0 \
  --build-arg GIT_SHA=$(git rev-parse --short HEAD) \
  --build-arg BUILD_TIME=$(date -u +%FT%TZ) .
docker run --rm -p 8080:8080 portfolio-site      # http://localhost:8080
```

Run only the tests (no Docker needed, Python 3 standard library):

```bash
python3 -m unittest discover -s tests -v
```

## Endpoints

| Path | Purpose |
|---|---|
| `/` | The portfolio page |
| `/healthz` | Returns `200 ok` (liveness/readiness) |
| `/version.json` | `{"version","git_sha","built_at"}` stamped at build time, never cached |
| `/nginx_status` | nginx stub_status; allowed only from localhost and private networks |

## Test scenarios for your platform

1. **Healthy push** - edit text in `site/index.html` and push. Expect: tests pass, build, low risk, deploy.
2. **Build/test failure** - point a stylesheet or script at a file that doesn't exist (for example change `css/style.css` to `css/missing.css` in `index.html`). `test_local_files_referenced_exist` fails, so `docker build` fails. Expect: a failed run and a high risk score.
3. **Passes tests, fails at runtime** - in `nginx/default.conf`, uncomment `return 503;` inside `location /`. The image builds and `/healthz` stays green, but the site returns 503. Expect the monitor to see the error rate rise and roll back to the previous release.
4. **Large commit** - restyle `site/css/style.css` and edit several HTML sections in one push to exercise the "files / lines changed" features.
5. **Manual rollback** - push two healthy commits, roll back from the dashboard, then check `/version.json` or the footer shows the earlier release.

`.github/workflows/ci.yml` runs the same tests, build and a container smoke test on GitHub Actions.
