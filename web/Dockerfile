FROM nginx:1.27-alpine

COPY web /usr/share/nginx/html
COPY styles /usr/share/nginx/html/styles
COPY web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
