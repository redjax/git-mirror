## Add build args.
#  You can pass different args for these values in a docker-compose.yml
#  file's build: section
ARG UV_BASE=${UV_IMG_VER:-0.4.27}
ARG PYTHON_BASE=${PYTHON_IMG_VER:-3.12-slim}

FROM ghcr.io/astral-sh/uv:$UV_BASE as uv
FROM python:$PYTHON_BASE AS base

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git

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
COPY mirrors.json ./mirrors.json

RUN uv sync --all-extras

FROM stage AS run

COPY --from=stage /project /project
COPY --from=uv /uv /bin/

CMD ["uv", "run", "src/git_mirror/main.py"]
