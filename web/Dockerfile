# Imagem opcional (build manual). O Compose usa nginx + volumes — sem build local.
FROM nginx:1.27-alpine

COPY index.html /usr/share/nginx/html/
COPY styles /usr/share/nginx/html/styles/
COPY scripts /usr/share/nginx/html/scripts/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
