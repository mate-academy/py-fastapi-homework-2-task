# Selecting a working directory
WORKDIR /usr/src/poetry

# Install dependencies with Poetry (с флагом совместимости для pydantic-core)
RUN export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 && \
    poetry lock && \
    poetry install --no-root --only main

# Selecting a working directory
WORKDIR /usr/src/fastapi

# Copy the source code
COPY ./src .

# Copy commands
COPY ./commands /commands

# Ensure Unix-style line endings for scripts
RUN dos2unix /commands/*.sh

# Add execute bit to commands files
RUN chmod +x /commands/*.sh
