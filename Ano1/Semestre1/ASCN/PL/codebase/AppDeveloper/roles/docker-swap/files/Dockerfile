FROM ubuntu:24.04

# Set the noninteractive mode
ARG DEBIAN_FRONTEND=noninteractive

# Swap commit to build
ARG SWAP_REF=347f8e0

# Default values for the environment variables
ENV SEED=false

# Install PHP 7.4, Node and tools
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:ondrej/php && \
    apt-get update && \
    apt-get install -y php7.4 php7.4-fpm php7.4-zip \
        php7.4-mbstring php7.4-tokenizer php7.4-mysql \
        php7.4-gd php7.4-xml php7.4-bcmath php7.4-intl \
        php7.4-curl nodejs npm curl git unzip

# Install Composer v1
RUN curl -sS https://getcomposer.org/installer | php -- --1 && \
    mv composer.phar /usr/bin/composer

# Clone Swap at a fixed commit
RUN git clone https://github.com/Hackathonners/swap.git /swap && \
    git -C /swap checkout "$SWAP_REF"

WORKDIR /swap

# Create Swap configuration file
RUN cp .env.example .env

# Install Swap PHP dependencies
RUN composer install

# Install Swap Node dependencies
RUN npm install

# Copy start script
COPY ./start.sh .

# Add execution permission to start script
RUN chmod +x start.sh

# Expose port 8000
EXPOSE 8000

# Start Swap server
CMD [ "./start.sh" ]