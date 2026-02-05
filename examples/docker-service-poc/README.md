# Docker Service PoC

This Proof of Concept demonstrates the **"Qwen-as-a-Service"** architecture.
Instead of installing Node.js and the Qwen CLI in every container, we use a single centralized service.

## Architecture

1.  **`qwen-service`**:
    *   Based on Node+Python.
    *   Has `qwen` CLI installed.
    *   Runs a FastAPI server exposing `POST /generate`.
    *   Uses `credential-rotation` to manage account switching.
    *   Mounts `~/.qwen` from the host to persist state.

2.  **`client-app`**:
    *   Lightweight Python container.
    *   **NO** Node.js, **NO** Qwen CLI installed.
    *   Simply sends HTTP requests to `qwen-service`.

## How to Run

1.  Ensure you have configured your accounts on the host:
    ```bash
    account-qwen --setup
    ```

2.  Run the PoC with Docker Compose:
    ```bash
    cd examples/docker-service-poc
    docker-compose up --build
    ```

3.  Observe the output:
    *   The `client-app` will send prompts.
    *   The `qwen-service` will handle them, rotating accounts automatically if quota errors occur.
    *   You can verify the rotation by checking `account-qwen --list` on your host machine (since they share the same directory).
