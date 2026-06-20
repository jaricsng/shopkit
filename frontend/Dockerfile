# syntax=docker/dockerfile:1
# Multi-stage: build the static bundle, then serve it with nginx.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# The @playwright/test devDep is only for the e2e job, not the SPA build — skip
# its browser download so the image build stays lean.
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
RUN npm ci
COPY . .
# Bake the API base at build time if provided (defaults to /api via the proxy).
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.29-alpine AS runtime
# Patch base-image OS packages (clears fixable CVEs the Trivy gate flags).
RUN apk upgrade --no-cache
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
