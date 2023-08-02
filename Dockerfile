FROM ubuntu:20.04


ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends wget build-essential libreadline-dev \ 
libncursesw5-dev libssl-dev libsqlite3-dev libgdbm-dev libbz2-dev liblzma-dev zlib1g-dev uuid-dev libffi-dev libdb-dev unzip curl \ 
python3.9 python3-pip

RUN apt install -y python-is-python3

RUN apt-get autoremove -y

COPY scripts/install_chromedriver.sh /tmp/install_chromedriver.sh
RUN chmod +x /tmp/install_chromedriver.sh && /tmp/install_chromedriver.sh

WORKDIR /mnt/app

COPY ./pyproject.toml /mnt/app
COPY ./poetry.lock /mnt/app

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc \
    && echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.bashrc \
    && . ~/.bashrc \
    # && poetry config virtualenvs.create true \ 
    && poetry install --no-root --no-dev

CMD tail -f /dev/null