FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    FSLDIR=/opt/pixi/envs/default \
    PATH=/opt/pixi/envs/default/bin:$PATH

# 1) Install system deps
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bzip2 \
           ca-certificates \
           curl \
    && rm -rf /var/lib/apt/lists/*

# 2) Install pixi (https://pixi.prefix.dev/latest/installation/)
RUN curl -fsSL https://pixi.sh/install.sh | sh
ENV PATH="/root/.pixi/bin:$PATH"

USER neuro

# 3) Create pixi project with FSL (https://fsl.fmrib.ox.ac.uk/fsl/docs/install/conda.html)
RUN pixi init --non-interactive && \
    pixi project channel add https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/ && \
    pixi project channel add conda-forge && \
    pixi add fsl python=3.14 nipype nibabel pytest

# 5) Install environment
RUN pixi install

# 6) Get pydeface

COPY [".", "/pydeface"]
USER root
RUN chown -R neuro:users /pydeface
USER neuro
RUN conda install -y --name test \
    && bash -c "source activate test \
    && python -m pip install --no-cache-dir \
             "-e" \
             "/pydeface"" \
    && conda clean --all --yes && sync \
    && rm -rf ~/.cache/pip/*
