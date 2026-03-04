FROM ghcr.io/prefix-dev/pixi:0.65.0 AS build

RUN mkdir /app
COPY pixi.lock pyproject.toml /app
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/rattler pixi install --all --frozen --skip pydeface
RUN pixi shell-hook -e default --as-is > /shell-hook.sh
RUN pixi shell-hook -e dev --as-is > /shell-hook-dev.sh

RUN echo 'exec "$@"' >> /shell-hook.sh
RUN echo 'exec "$@"' >> /shell-hook-dev.sh

COPY . /app
RUN --mount=type=cache,target=/root/.cache/rattler pixi install --frozen
RUN --mount=type=cache,target=/root/.cache/rattler pixi install -e dev --frozen


FROM debian:trixie-slim AS base

ARG DEBIAN_FRONTEND=noninteractive

# Unless otherwise specified each process should only use one thread - nipype
# will handle parallelization
ENV MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1

ENTRYPOINT ["/bin/bash", "/shell-hook.sh"]
WORKDIR /app

FROM base AS test

COPY --link --from=build --exclude=.pixi/envs/default /app /app
COPY --link --from=build /shell-hook-dev.sh /shell-hook.sh

CMD ["pytest", "-v"]

FROM base AS production

COPY --link --from=build /app/.pixi/envs/default /app/.pixi/envs/default
COPY --link --from=build /shell-hook.sh /shell-hook.sh

ENTRYPOINT ["/bin/bash", "/shell-hook.sh", "pydeface"]
