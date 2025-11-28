# WhatsApp Router System

A microservices-based WhatsApp messaging system built with FastAPI, PyWA, and Docker. This project demonstrates clean architecture, proper testing, and containerized deployment.

## 🏗️ Architecture

The system consists of two microservices:

1. **Router Service** (Port 8000)

   - Receives WhatsApp Cloud API webhooks
   - Validates webhook requests
   - Extracts message data
   - Forwards messages to Server service
   - Sends replies back via PyWA

2. **Server Service** (Port 8001)
   - Processes incoming messages
   - Generates formatted responses with random numbers
   - Returns processed messages to Router

```
WhatsApp User → Meta Cloud API → Router Service → Server Service
                                      ↓
                                   Router ← Server
                                      ↓
WhatsApp User ← Meta Cloud API ← Router
```

## 📋 Prerequisites

- **Python 3.10+**
- **Docker & Docker Compose**
- **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **ngrok** - For exposing local webhook ([download](https://ngrok.com/download))
- **Meta Developer Account** - For WhatsApp Cloud API access

## 🚀 Quick Start

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd whatsapp-router

# Copy environment file
cp .env.example .env

# Edit .env with your WhatsApp credentials
nano .env  # or use your preferred editor
```

### 3. Configure WhatsApp Cloud API

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new App or use existing one
3. Add WhatsApp product
4. Navigate to **WhatsApp → API Setup**
5. Note down:
   - Phone Number ID
   - Access Token (temporary or permanent)
6. Choose a Webhook Verify Token (any string you want)
7. Add your phone number as a test recipient
8. Update `.env` with these values

### 4. Start Services

```bash
# Build and start all services
make up

# Check if services are running
make status

# View logs
make logs
```

### 5. Expose Router with ngrok

```bash
# In a new terminal
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abcd1234.ngrok.io`)

### 6. Configure Webhook in Meta Console

1. Go to **WhatsApp → Configuration** in Meta Developer Console
2. Click **Edit** on Webhook
3. Set Callback URL: `https://abcd1234.ngrok.io/webhook`
4. Set Verify Token: (same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in `.env`)
5. Subscribe to **messages** webhook field
6. Click **Verify and Save**

### 7. Test End-to-End

1. Send a WhatsApp message to your test number
2. Example: "Hello there"
3. You should receive: "I received your message: 'Hello there' and here is a random number: 4829"

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Run Service-Specific Tests

```bash
# Server tests only
make test-server

# Router tests only
make test-router
```

### Run Tests in Docker

```bash
make test-server-docker
make test-router-docker
```

### Test Coverage

```bash
cd server
uv run pytest --cov=app --cov-report=html

cd ../router
uv run pytest --cov=app --cov-report=html
```

## 📁 Project Structure

```
.
├── router/                      # Router microservice
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py             # FastAPI app + PyWA integration
│   ├── tests/
│   │   └── test_router.py      # Router tests
│   ├── Dockerfile
│   └── pyproject.toml          # Router dependencies
│
├── server/                      # Server microservice
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py             # Message processing logic
│   ├── tests/
│   │   └── test_server.py      # Server tests
│   ├── Dockerfile
│   └── pyproject.toml          # Server dependencies
│
├── docker-compose.yml           # Service orchestration
├── Makefile                     # Build and run commands
├── .env.example                 # Environment template
└── README.md                    # This file
```

## 🛠️ Available Commands

```bash
make help           # Show all available commands
make up             # Build and start services
make down           # Stop services
make restart        # Restart all services
make logs           # View all logs
make logs-router    # View router logs only
make logs-server    # View server logs only
make test           # Run all tests
make test-server    # Run server tests
make test-router    # Run router tests
make status         # Show service status
make clean          # Clean up containers and images
make check-env      # Verify environment variables
make ngrok          # Show ngrok setup instructions
```

## 🔧 Development

### Local Development (Without Docker)

#### Server Service

```bash
cd server

# Install dependencies
uv sync

# Run server
uv run uvicorn app.main:app --reload --port 8001

# Run tests
uv run pytest -v
```

#### Router Service

```bash
cd router

# Install dependencies
uv sync

# Update .env with local server URL
# SERVER_BASE_URL=http://localhost:8001

# Run router
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest -v
```

### Adding Dependencies

```bash
# For server
cd server
uv add <package-name>

# For router
cd router
uv add <package-name>
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
make logs

# Verify environment variables
make check-env

# Rebuild containers
make down
make up
```

### Webhook Verification Fails

1. Ensure ngrok is running and URL is updated in Meta Console
2. Verify `WHATSAPP_WEBHOOK_VERIFY_TOKEN` matches in both `.env` and Meta Console
3. Check router logs: `make logs-router`

### Messages Not Being Received

1. Check if webhook is subscribed to "messages" field in Meta Console
2. Verify phone number is added as test recipient
3. Check router logs for incoming webhooks
4. Verify server is responding: `curl http://localhost:8001/health`

### Tests Failing

```bash
# Ensure dependencies are installed
cd server && uv sync
cd ../router && uv sync

# Run with verbose output
uv run pytest -vv

# Check specific test
uv run pytest tests/test_router.py::TestWebhookReceiver -v
```

## 📊 API Endpoints

### Router Service (Port 8000)

- `GET /health` - Health check
- `GET /webhook` - Webhook verification (called by Meta)
- `POST /webhook` - Receive WhatsApp messages

### Server Service (Port 8001)

- `GET /health` - Health check
- `POST /process` - Process message and generate reply

## 🔒 Environment Variables

| Variable                        | Description                            | Example               |
| ------------------------------- | -------------------------------------- | --------------------- |
| `WHATSAPP_PHONE_NUMBER_ID`      | Your WhatsApp Business Phone Number ID | `123456789012345`     |
| `WHATSAPP_ACCESS_TOKEN`         | WhatsApp API Access Token              | `EAAxxxx...`          |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Custom verification token              | `my_secure_token_123` |
| `SERVER_BASE_URL`               | Internal server URL                    | `http://server:8001`  |

## 🚧 Known Limitations

1. **Temporary Access Token**: The temporary token from Meta expires. For production, create a permanent system user token.
2. **Text Messages Only**: Currently only handles text messages. Images, videos, and other media types are ignored.
3. **No Message Queue**: Messages are processed synchronously. For high volume, consider adding a queue (Redis, RabbitMQ).
4. **No Database**: Message history is not stored. Add a database for persistence.
5. **Basic Error Handling**: Production systems should have more robust error handling and retry logic.

## 🔮 Future Improvements

- [ ] Add database for message persistence
- [ ] Implement message queue for better scaling
- [ ] Support media messages (images, videos, documents)
- [ ] Add rate limiting
- [ ] Implement conversation context tracking
- [ ] Add monitoring and metrics (Prometheus/Grafana)
- [ ] Add CI/CD pipeline
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Add authentication for internal API calls
- [ ] Implement message templates

## 📝 License

This project is created as a take-home assignment and is provided as-is for evaluation purposes.

## 🤝 Contributing

This is an assignment project, but suggestions and feedback are welcome!

## 📧 Contact

For questions about this implementation, please reach out during the interview process.
