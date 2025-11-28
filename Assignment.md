# Take-home Assignment: WhatsApp Router with PyWA, FastAPI & Docker

## 1. Context & Goal

This assignment is designed to evaluate how you:

- **Adopt and integrate FOSS libraries** (especially [PyWA](https://pypi.org/project/pywa/) and [FastAPI](https://fastapi.tiangolo.com/)).
- **Use modern Python tooling** — specifically **[uv](https://docs.astral.sh/uv/)** for packaging & environments.
- **Design and containerize microservices** with **Docker** and **docker-compose**.
- **Write automated tests** for FastAPI applications (using `pytest` and `httpx`’s TestClient equivalents).
- Provide **clear, reproducible instructions** for running and testing everything.

You will build a small system with **two microservices**:

1. **Router service** (FastAPI + PyWA):

   - Receives WhatsApp Cloud API webhooks.
   - Calls the Server service to compute a reply.
   - Sends the reply back to the user via PyWA.

2. **Server service** (FastAPI):
   - Accepts a text message.
   - Returns a deterministic string:
     > `"I received your message: '<TEXT>' and here is a random number: <RANDOM_NUMBER>"`

Everything runs **locally** in Docker containers, wired via **docker-compose**.
WhatsApp Cloud API is accessed over the internet; your local router is exposed via **ngrok**.

> 🎯 **Expected time:** 2 focused hours.  
> Please prioritize correctness, clarity, and tests over adding extra features.

---

## 2. High-level Architecture

**Message flow:**

1. You send a WhatsApp message from your phone to the **Meta test number** (WhatsApp Cloud API).
2. Meta sends a webhook to your **Router** (`/webhook`).
3. Router extracts the text and calls **Server** (`/process`).
4. Server returns:  
   `"I received your message: '<TEXT>' and here is a random number: <RANDOM_NUMBER>"`.
5. Router sends this reply back to the same WhatsApp user.
6. Router responds `{"status": "ok"}` to Meta.

The **Router** and **Server** are separate FastAPI apps, each running in its own Docker container, orchestrated by `docker-compose`.

---

## 3. Tooling Requirements

You **must** use:

- **Python** 3.10+ (inside containers, you can pick 3.10, 3.11 or 3.12).
- **[uv](https://docs.astral.sh/uv/)** as the Python package/project manager for the codebase.
  - Recommended docs:
    - Overview: <https://docs.astral.sh/uv/>
    - First steps: <https://docs.astral.sh/uv/getting-started/first-steps/>
- **FastAPI** for both services.
- **[PyWA](https://pywa.readthedocs.io/en/latest/)** for WhatsApp Cloud API integration in the Router.
- **pytest** for tests (and `httpx` or FastAPI’s `TestClient`).
- **Docker** & **docker-compose**.
- **Makefile** with a **single main target**, for example:

```bash
    make up
```

This should:

- Build Docker images for both services.

- Start them via `docker-compose`.

- Ideally, provide another target like `make test` to run the test suite via uv.

- **ngrok** (or equivalent) to expose your local Router service to the WhatsApp Cloud API webhook:

  - [https://ngrok.com/](https://ngrok.com/)

---

## 4. WhatsApp Cloud API Setup

Follow Meta’s official **Cloud API** getting-started flow:

1. Go to **Meta for Developers**:
   [https://developers.facebook.com/](https://developers.facebook.com/)

2. Create or switch to a **Developer account**.

3. Create a new **App**, and add the **WhatsApp** product. [PyWa Documentation]

4. In the **WhatsApp → API Setup / Getting Started** screen:

   - Meta provides a **test business phone number**.
   - Add your own phone number as a **test recipient** (up to 5).
   - Verify it via the OTP you receive on WhatsApp.
   - Send the `hello_world` template from the UI to confirm that messages work.

5. Collect these values:

   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_ACCESS_TOKEN` (temporary token is fine for this assignment)
   - A `WHATSAPP_WEBHOOK_VERIFY_TOKEN` — **you choose this string**.

You’ll use these in the Router service’s environment.

---

## 5. Project Structure (Suggested)

You can adjust slightly, but please keep a similar layout and document it.

```text
.
├─ router/
│  ├─ app/
│  │  ├─ __init__.py
│  │  └─ main.py          # FastAPI + PyWA webhook + call server
│  ├─ tests/
│  │  └─ test_router.py
│  ├─ Dockerfile
│  └─ pyproject.toml      # managed via uv
├─ server/
│  ├─ app/
│  │  ├─ __init__.py
│  │  └─ main.py          # FastAPI /process endpoint
│  ├─ tests/
│  │  └─ test_server.py
│  ├─ Dockerfile
│  └─ pyproject.toml      # managed via uv
├─ docker-compose.yml
├─ Makefile
├─ .env.example           # all env vars (no secrets)
└─ ASSIGNMENT_NOTES.md    # optional: your thinking, notes, etc.
```

> ✅ **Each service** (`router/`, `server/`) should be its **own uv project**, with its own `pyproject.toml` and lockfile managed via `uv`.

---

## 6. Using uv (Required)

Install `uv` following the docs:
[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

Example workflow for each service:

```bash
cd server
uv init --package server  # or similar; creates pyproject.toml

# Add dependencies
uv add fastapi uvicorn pytest httpx

cd ../router
uv init --package router
uv add fastapi uvicorn pytest httpx pywa python-dotenv
```

You can then:

- Run apps locally (for your own dev) with:

  ```bash
  uv run uvicorn app.main:app --reload --port 8001   # for server
  uv run uvicorn app.main:app --reload --port 8000   # for router
  ```

- Run tests with:

  ```bash
  uv run pytest
  ```

Inside Docker, you can either:

- Use `uv` directly in the container, **or**
- Use `uv export` to generate a `requirements.txt` and use `pip`. Using `uv` inside the container is preferred if you’re comfortable with it.

---

## 7. Server Service — Requirements & Skeleton

### 7.1. Behavior

**Endpoint:** `POST /process`
**Input JSON:**

```json
{ "text": "hello there" }
```

**Output JSON:**

```json
{
  "original": "hello there",
  "reply": "I received your message: 'hello there' and here is a random number: 4829"
}
```

The random number can be any integer; it should change per call.

### 7.2. Starter Skeleton: `server/app/main.py`

```python
from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="Server Backend")


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    original: str
    reply: str


@app.post("/process", response_model=MessageOut)
def process_message(payload: MessageIn) -> MessageOut:
    """
    Receives a text message and returns:
    "I received your message: '<TEXT>' and here is a random number: <RANDOM>"
    """
    rnd = random.randint(1000, 9999)
    reply_text = (
        f"I received your message: '{payload.text}' and here is a random number: {rnd}"
    )
    return MessageOut(original=payload.text, reply=reply_text)
```

### 7.3. Tests for Server

File: `server/tests/test_server.py`

Use FastAPI’s `TestClient` (from `fastapi.testclient` or `httpx.AsyncClient`) to test:

- Status code is `200`.
- `reply` starts with `"I received your message: '...'"`.
- `original` echoes the input.

Example skeleton:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_process_message_basic():
    resp = client.post("/process", json={"text": "test message"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["original"] == "test message"
    assert "I received your message: 'test message'" in data["reply"]
```

You can add more tests (e.g., invalid payloads).

---

## 8. Router Service — Requirements & Skeleton

### 8.1. Behavior

**Responsibilities:**

1. **Webhook verification (GET `/webhook`)**

   - Meta calls this when you set up the callback URL.
   - If `hub.mode == 'subscribe'` and `hub.verify_token` matches your verify token, echo back `hub.challenge`.

2. **Webhook receiver (POST `/webhook`)**

   - Parse WhatsApp Cloud API incoming message.
   - Extract:

     - Message **text**.
     - Sender **ID** (`from`).

   - Call Server: `POST {SERVER_BASE_URL}/process` with `{"text": <text>}`.
   - Get `reply` from Server’s response.
   - Use PyWA to **send the reply back** to the same user.

### 8.2. Environment Variables

Use `.env` (and `.env.example`) at the project root:

```env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

SERVER_BASE_URL=http://server:8001  # inside docker-compose network
```

In dev (without Docker), you can use `SERVER_BASE_URL=http://localhost:8001`.

### 8.3. Starter Skeleton: `router/app/main.py`

```python
import os
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from pywa import WhatsApp  # See docs: https://pywa.readthedocs.io/

load_dotenv()

app = FastAPI(title="WhatsApp Router Service")

# --- Env variables ---

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv ("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:8001")

# --- Initialize WhatsApp client (PyWA) ---
# Refer to PyWA "Get Started" docs to confirm parameters:
# https://pywa.readthedocs.io/en/latest/content/getting-started.html

wa = WhatsApp(
    phone_id=WHATSAPP_PHONE_NUMBER_ID,
    token=WHATSAPP_ACCESS_TOKEN,
    verify_token=WHATSAPP_WEBHOOK_VERIFY_TOKEN,
)


class ServerMessageIn(BaseModel):
    text: str


# --- Helper: call Server backend ---

async def call_server_backend(text: str) -> str:
    """
    Call the server /process endpoint and return the 'reply' field.
    """
    url = f"{SERVER_BASE_URL.rstrip('/')}/process"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"text": text}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["reply"]


# --- WhatsApp Webhook Verification (GET) ---

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str,
):
    """
    Meta will call this GET endpoint when you configure the webhook.
    You must echo back 'hub_challenge' if 'hub_verify_token' matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


# --- WhatsApp Webhook Receiver (POST) ---

@app.post("/webhook")
async def whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """
    Receives a webhook from WhatsApp, extracts the incoming message, calls the Server,
    and sends a reply back via WhatsApp (PyWA).
    """
    body = await request.json()

    # 1) Extract text and sender id from WhatsApp Cloud API payload.
    #    Typical structure (simplified, add checks!):
    #
    #    entry -> changes -> value -> messages[0]
    #
    #    text = msg["text"]["body"]
    #    from_wa_id = msg["from"]
    #
    # See official docs or use the Postman collection to inspect payloads.

    try:
        value = body["entry"][0]["changes"][0]["value"]
        msg = value["messages"][0]
        text = msg["text"]["body"]
        from_wa_id = msg["from"]
    except (KeyError, IndexError, TypeError):
        # Ignore non-message webhooks for simplicity
        return {"status": "ignored"}

    # 2) Call server backend
    reply_text = await call_server_backend(text)

    # 3) Send reply back via WhatsApp using PyWA
    #    Adjust to the exact method name in the version of PyWA you're using.
    wa.send_message(to=from_wa_id, text=reply_text)

    return {"status": "ok"}
```

> 🔎 **Important:** Confirm the `WhatsApp` initialization and `send_message` API against the PyWA version you install; signatures may evolve. See:
> [https://pywa.readthedocs.io/en/latest/content/getting-started.html](https://pywa.readthedocs.io/en/latest/content/getting-started.html)

### 8.4. Tests for Router

File: `router/tests/test_router.py`

You **don’t** need to hit the real WhatsApp API in tests. Instead:

- Use FastAPI’s `TestClient` or `httpx.AsyncClient`.
- Mock **external calls**:

  - `call_server_backend` (or `httpx.AsyncClient.post`)
  - `wa.send_message`

Example pattern (using monkeypatch):

```python
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_webhook_ignores_invalid_payload():
    resp = client.post("/webhook", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
```

For a “happy path” test:

- Build a minimal fake WhatsApp webhook payload.
- Patch `call_server_backend` to return a known string.
- Patch `wa.send_message` to record that it was called with expected arguments.

We’re interested in:

- You understand how to **test FastAPI routes**.
- You know how to **mock external dependencies**.

---

## 9. Docker & docker-compose

### 9.1. Dockerfiles

#### `server/Dockerfile` (example)

```dockerfile
FROM python:3.12-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY app ./app

# Install dependencies (using uv)
RUN uv sync --frozen

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### `router/Dockerfile` (example)

```dockerfile
FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> You can refine these Dockerfiles (e.g. multi-stage, non-root user) if you like, but keep them simple and working.

### 9.2. docker-compose.yml

At repo root:

```yaml
services:
  server:
    build: ./server
    container_name: wa_server
    ports:
      - "8001:8001"

  router:
    build: ./router
    container_name: wa_router
    ports:
      - "8000:8000"
    environment:
      WHATSAPP_PHONE_NUMBER_ID: ${WHATSAPP_PHONE_NUMBER_ID}
      WHATSAPP_ACCESS_TOKEN: ${WHATSAPP_ACCESS_TOKEN}
      WHATSAPP_WEBHOOK_VERIFY_TOKEN: ${WHATSAPP_WEBHOOK_VERIFY_TOKEN}
      SERVER_BASE_URL: "http://server:8001"
```

Use a `.env` file at root so `docker-compose` picks up the WhatsApp variables.

---

## 10. Makefile (Single Main Command)

Example `Makefile`:

```makefile
.PHONY: up down test

up:
    # Build and start all services
    docker compose build
    docker compose up -d

down:
    docker compose down

test:
    # Run tests for both services using uv inside the containers or locally
    cd server && uv run pytest
    cd router && uv run pytest
```

We will primarily use:

```bash
make up
```

to build and start everything.

---

## 11. Exposing Router via ngrok

To let WhatsApp Cloud API call your Router:

1. Install **ngrok**: [https://ngrok.com/](https://ngrok.com/)

2. Run:

   ```bash
   ngrok http 8000
   ```

3. You’ll get an HTTPS URL like `https://abcd1234.ngrok.io`.

4. In the Meta Developer dashboard → WhatsApp settings:

   - Set the webhook callback URL to:
     `https://abcd1234.ngrok.io/webhook`
   - Set the verify token to your `WHATSAPP_WEBHOOK_VERIFY_TOKEN`.

5. Meta will:

   - Call `GET /webhook` to verify.
   - Then send `POST /webhook` for each incoming message.

---

## 12. How to Manually Test End-to-end

1. **Start services**:

   ```bash
   make up
   ```

2. **Start ngrok**:

   ```bash
   ngrok http 8000
   ```

3. Configure the **Webhook** in the Meta WhatsApp dashboard (callback URL + verify token).

4. From your phone, send a WhatsApp message (e.g. `"hello there"`) to the **test business number**.

5. Expected:

   - The Router receives the webhook.
   - Router extracts `text = "hello there"` and sender ID.
   - Router calls `Server /process`.
   - Server returns `"I received your message: 'hello there' and here is a random number: XXXX"`.
   - Router sends this reply back via PyWA.
   - You see the reply on your phone.

---

## 13. What to Submit

A **GitHub repository** with:

- `router/` and `server/` each as uv-managed Python projects (with `pyproject.toml`).
- Proper FastAPI apps and tests (`router/tests`, `server/tests`).
- `Dockerfile` for each service.
- `docker-compose.yml`.
- `Makefile` with at least the `up` target (plus `down`, `test` if possible).
- `.env.example` with all required env vars (no secrets).
- `README.md` explaining:

  - How to set up Meta WhatsApp Cloud API (short summary).
  - How to configure `.env`.
  - How to run: `make up`.
  - How to run tests: `make test` or equivalent.
  - Any assumptions, limitations, and things you would improve with more time.

---

## 14. How We’ll Assess

We’ll focus on:

1. **Integration & correctness**

   - Router ↔ Server flow works as described.
   - WhatsApp webhook verification logic is correct.
   - Payload parsing is robust enough for the “happy path”.

2. **Use of uv & FastAPI best practices**

   - `pyproject.toml` and dependencies managed via uv.
   - Reasonable project layout (`app/`, `tests/`, etc.).

3. **Automated tests**

   - Tests exist for both services.
   - Router tests mock external calls appropriately.
   - Tests are runnable via `uv run pytest` or via a `make test` target.

4. **Containerization & orchestration**

   - Dockerfiles are sane and build.
   - `docker-compose up` brings up a working system.
   - The Makefile glues it together with a simple interface.

5. **Clarity of documentation**

   - We can follow `README.md` (and `.env.example`) to get it running without guesswork.

---

## 15. Final Notes

- You may use AI assistants and documentation, but **please ensure you understand the code you submit**. Once we are sure of the above 5 assessmnet pointers, there will be an viva round based on the code you submit and choices you made.
- You don’t need to overly optimize; focus on:

  - Clean, readable code.
  - Good separation of concerns (Router vs Server).
  - Solid tests for key behaviors.

- It’s okay if you don’t implement every “nice-to-have” – just be explicit in your README about what you did and what you’d do next.

Good luck 🚀
