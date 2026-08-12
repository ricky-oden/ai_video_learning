# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.23.2

FROM node:${NODE_VERSION}-alpine@sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32 AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
RUN chown -R node:node /app

FROM base AS dependencies
COPY --chown=node:node package.json package-lock.json ./
USER node
RUN npm ci

FROM base AS production-dependencies
COPY --chown=node:node package.json package-lock.json ./
USER node
RUN npm ci --omit=dev

FROM dependencies AS development
ENV NODE_ENV=development
COPY --chown=node:node . .
USER node
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

FROM dependencies AS build
COPY --chown=node:node . .
RUN npm run build

FROM base AS production
ENV NODE_ENV=production
COPY --from=production-dependencies --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/.next ./.next
COPY --chown=node:node package.json package-lock.json next.config.ts ./
USER node
EXPOSE 3000
CMD ["npm", "run", "start"]
