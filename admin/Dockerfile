FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-*.yaml ./

RUN pnpm install --frozen-lockfile --ignore-scripts

COPY . .

ENV NUXT_PUBLIC_API_BASE=https://api.kluda.app/api/v1
ENV NUXT_PUBLIC_DOMAIN_NAME=kluda.app

RUN pnpm run build

FROM nginx:alpine
COPY --from=builder /app/.output/public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
