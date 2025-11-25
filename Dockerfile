FROM eicweb/eic_xl:25.11-stable

WORKDIR /tmp
# Install core system packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      wget bzip2 git make g++ cmake python3-pip ca-certificates which && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV MAMBA_ROOT_PREFIX=/opt/conda

# Install micromamba and Python 3.12
RUN mkdir -p ${MAMBA_ROOT_PREFIX}/bin \
    && ARCH=$(uname -m) \
    && case "${ARCH}" in \
         x86_64) MAMBA_ARCH=64 ;; \
         aarch64) MAMBA_ARCH=aarch64 ;; \
         *) echo "Unsupported architecture: ${ARCH}" && exit 1 ;; \
       esac \
    && MAMBA_TAR=/tmp/micromamba.tar.bz2 \
    && wget -O ${MAMBA_TAR} "https://micro.mamba.pm/api/micromamba/linux-${MAMBA_ARCH}/latest" \
    && tar -xvjf ${MAMBA_TAR} -C /tmp bin/micromamba \
    && mv /tmp/bin/micromamba ${MAMBA_ROOT_PREFIX}/bin/micromamba \
    && chmod +x ${MAMBA_ROOT_PREFIX}/bin/micromamba \
    && rm -rf /tmp/bin ${MAMBA_TAR} \
    && ${MAMBA_ROOT_PREFIX}/bin/micromamba install -y -r ${MAMBA_ROOT_PREFIX} -n base python=3.12 \
    && ${MAMBA_ROOT_PREFIX}/bin/micromamba clean -a -y

ENV PATH=/opt/conda/bin:$PATH

# Install Python packages: Ax stack, dependencies, and workflow clients
RUN pip install --no-cache-dir \
      "ax-platform==1.0.0" \
      "numpy<2" \
      pandas \
      matplotlib \
      "sqlalchemy==1.4.46" \
      uncertainties \
    && pip install --no-cache-dir \
      torch \
      botorch \
      idds-client \
      idds-common \
      idds-workflow \
      panda-client

WORKDIR /opt/conda

RUN cd /opt/conda \
    && git clone https://github.com/eic/epic.git \
    && cd /opt/conda/epic \
    && cmake -B build -S . -DCMAKE_INSTALL_PREFIX=/opt/conda/epic/eic-software \
    && cmake --build /opt/conda/epic/build \
    && cmake --install /opt/conda/epic/build
    
