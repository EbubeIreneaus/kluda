FROM node:22-alpine AS builder

WORKDIR /app

ENV NODE_ENV=production

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./


RUN pnpm install --frozen-lockfile --ignore-scripts

COPY . .


RUN pnpm run build


FROM nginx:alpine

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.output/public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
