# Personal portfolio site for testing the Predictive Auto Deployment Platform.
# Build:  docker build -t portfolio-site .
# Run:    docker run --rm -p 8080:8080 portfolio-site     (then open http://localhost:8080)

# --- Stage 1: run the test suite. A failing test fails the whole build. ---
FROM python:3.12-alpine AS test
WORKDIR /src
COPY site ./site
COPY tests ./tests
RUN python -m unittest discover -s tests -v && touch /tests.passed

# --- Stage 2: stamp the build with version info (served at /version.json) ---
FROM alpine:3.20 AS assemble
ARG APP_VERSION=1.0.0
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
COPY site /site
RUN printf '{"version":"%s","git_sha":"%s","built_at":"%s"}\n' \
      "$APP_VERSION" "$GIT_SHA" "$BUILD_TIME" > /site/version.json

# --- Stage 3: runtime image (nginx as non-root, listens on 8080) ---
FROM nginxinc/nginx-unprivileged:1.27-alpine
# Copying this marker makes the test stage a dependency of the final image,
# so tests always run, even with BuildKit.
COPY --from=test /tests.passed /tmp/.tests-passed
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=assemble /site /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
