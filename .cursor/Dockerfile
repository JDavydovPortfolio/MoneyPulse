# Use Ubuntu as the base image for background agents
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Update package list and install essential development tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    jq \
    unzip \
    ca-certificates \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -s /bin/bash ubuntu

# Set the working directory to the user's home directory
WORKDIR /home/ubuntu

# Change ownership of the working directory to the user
RUN chown -R ubuntu:ubuntu /home/ubuntu

# Switch to the non-root user
USER ubuntu

# Set default shell
SHELL ["/bin/bash", "-c"]

# Install common development tools via pip and npm as the ubuntu user
RUN pip3 install --user \
    requests \
    beautifulsoup4 \
    pandas \
    numpy \
    selenium \
    lxml \
    openai \
    python-dotenv \
    && npm install -g \
    typescript \
    @types/node \
    yarn

# Add user's local bin to PATH
ENV PATH="/home/ubuntu/.local/bin:${PATH}"

# Create common directories that background agents might need
RUN mkdir -p /home/ubuntu/projects /home/ubuntu/.ssh

# Keep the container running
CMD ["/bin/bash"]
