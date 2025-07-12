FROM node:22.15.0-alpine AS build

ENV NUXT_PUBLIC_AUTH_API_URL=http://192.168.72.52:30010
ENV NUXT_PUBLIC_PEERFLOW_API_URL=http://192.168.72.52:30060
ENV NUXT_PUBLIC_FILE_STORAGE_URL=http://192.168.72.52:30031

WORKDIR /app/src

# Install dependencies first to leverage Docker cache
COPY ./src/ /app/src/
RUN rm -rf node_modules package-lock.json
RUN npm install --legacy-peer-deps
RUN npm run build

RUN cp -r ./.output /app/build

WORKDIR /app

RUN rm -rf /app/src



EXPOSE 3000

CMD [ "node", "./build/server/index.mjs" ]