FROM node:22-alpine AS builder

WORKDIR /app

ENV NODE_ENV=production

ARG NUXT_PUBLIC_API_BASE=https://api.kluda.app/api/v1
ARG NUXT_PUBLIC_POS_APP_URL=https://pos.kluda.app
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_POS_APP_URL=$NUXT_PUBLIC_POS_APP_URL

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile --ignore-scripts

COPY . .

RUN pnpm run build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

COPY --from=builder /app/.output ./

EXPOSE 3000

CMD ["node", "server/index.mjs"]
