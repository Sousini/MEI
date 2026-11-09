FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# Dependências base + repositório PPA do PHP
RUN apt-get update && apt-get install -y \
    software-properties-common curl git unzip ca-certificates \
    && add-apt-repository -y ppa:ondrej/php \
    && apt-get update \
    && apt-get install -y php7.4 \
       php7.4-fpm php7.4-zip php7.4-mbstring php7.4-tokenizer php7.4-mysql \
       php7.4-gd php7.4-xml php7.4-bcmath php7.4-intl php7.4-curl \
       nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Composer v1
RUN curl -sS https://getcomposer.org/installer | php -- --1 \
    && mv composer.phar /usr/bin/composer

# Aplicação
WORKDIR /app
RUN git clone https://github.com/Hackathonners/swap.git .

RUN composer install && npm install

# Ficheiro .env será criado em runtime (ver entrypoint)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
