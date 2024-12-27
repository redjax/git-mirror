## Add build args.
#  You can pass different args for these values in a docker-compose.yml
#  file's build: section
ARG UV_BASE=${UV_IMG_VER:-0.4.27}
ARG PYTHON_BASE=${PYTHON_IMG_VER:-3.12-slim}

FROM ghcr.io/astral-sh/uv:$UV_BASE AS uv
FROM python:$PYTHON_BASE AS base

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        sudo \
        build-essential \
        curl \
        git \
        openssh-server \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

## Create a non-root user 'gituser' and add to sudo group
RUN useradd -ms /bin/bash gituser \
    && usermod -aG sudo gituser \
    && echo "gituser ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/gituser

## Set permissions on gituser home directory
RUN chown -R gituser:gituser /home/gituser \
    && mkdir -pv /home/gituser/.local /home/gituser/.ssh \
    && chmod -R u+w /home/gituser/.local /home/gituser/.ssh

## Create container /data directory
RUN mkdir -pv /data/logs \
    && mkdir -pv /data/repositories

FROM base AS stage
## Add astral.sh/uv to container's /bin/ path
COPY --from=uv /uv /bin/

USER gituser

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

RUN uv sync --all-extras

FROM stage AS run

COPY --from=stage /home/gituser/.ssh /home/gituser/.ssh
COPY --from=stage /data /data
COPY --from=stage /project /project
COPY --from=uv /uv /bin/

# USER root
# RUN sudo chown -R gituser:gituser /data \
#     && chmod -R u+w /data

USER gituser

# RUN sudo chmod -R u+w /home/gituser/data \
#     && sudo chown -R gituser:gituser /home/gituser/data

RUN sudo chown -R gituser:gituser /data
RUN sudo chown -R gituser:gituser /home/gituser/.ssh

CMD ["uv", "run", "src/git_mirror/main.py"]
