FROM node:22-alpine AS base

WORKDIR /frontend

COPY package*.json ./

RUN npm install

COPY ./src ./src
COPY tsconfig.json .
COPY vite.config.ts .
COPY metadata.json .

FROM base AS dev

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


FROM base AS build
RUN npm run build

FROM nginx:alpine AS prod
COPY --from=build /frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
