## Add build args.
#  You can pass different args for these values in a docker-compose.yml
#  file's build: section
ARG UV_BASE=${UV_IMG_VER:-0.5.11}
ARG PYTHON_BASE=${PYTHON_IMG_VER:-3.12-slim}

FROM ghcr.io/astral-sh/uv:$UV_BASE AS uv
FROM python:$PYTHON_BASE AS base

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        sudo \
        build-essential \
        curl \
        git \
        openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

## Create container /data directory
RUN mkdir -pv /data/logs && \
    mkdir -pv /data/repositories

# ## Seed app log files
# RUN touch /data/logs/app.log \
#     && touch /data/logs/error.log

FROM base AS stage
## Add astral.sh/uv to container's /bin/ path
COPY --from=uv /uv /bin/

## Set environment variables. These will be passed
#  to stages that inherit from this layer
ENV PYTHONDONTWRITEBYTECODE 1 \
  PYTHONUNBUFFERED 1

## Set CWD in container
WORKDIR /project

## Copy project files & install with uv
COPY pyproject.toml uv.lock ./
COPY src/ ./src
COPY README.md ./README.md
COPY mirrors.json ./mirrors.json

USER root
RUN uv sync

FROM stage AS run

# COPY --from=stage /root/.ssh /root/.ssh
COPY --from=stage /project /project
COPY --from=stage /data /data
COPY --from=uv /uv /bin/
# COPY ./containers/docker-entrypoint/entrypoint.sh /project/entrypoint.sh

USER root

CMD ["uv", "run", "src/git_mirror/main.py"]
