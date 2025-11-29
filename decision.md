# 🧠 Design Decisions

### 1. Single Dockerfile for App + Tests  
Keeping everything in one Dockerfile reduces early-stage complexity.  
A multi-stage build will be added once the project stabilizes and image optimization becomes necessary.

### 2. Minimal Modularization Initially  
Most logic sits inside `main.py` to allow fast iteration.  
As the codebase expands, logic will be moved into dedicated modules (services, routers, configs).

### 3. Trusted Internal API Contracts  
The internal backend is assumed to return well-structured payloads.  
Extra validation will be introduced only if inconsistencies arise.

### 4. Lightweight Microservice Boundaries  
Both router and backend services are intentionally small and stateless, making horizontal scaling simple.


### 5. Simplicity Over Abstraction (for now)  
Avoided early abstractions (CQRS, events, etc.).  
The current scope benefits from keeping the code straightforward for maintainability.

---

# 🔮 Future Improvements

### 1. Introduce Multi-Stage Docker Builds  
Separate builder, test, and runtime layers to reduce final image size and improve security.

### 2. Improve App Modularization  
Move toward a structure like:  
`/routers`, `/services`, `/schemas`, `/core`, `/utils`.

### 3. Add Persistence Layer  
Store incoming/outgoing messages for analytics, auditing, and reliability.

### 4. Queue-Based Message Processing  
Use Redis or RabbitMQ to decouple WhatsApp webhook handling from backend processing.

### 5. Advanced Monitoring & Alerts  
Add Prometheus, Grafana, structured logging, and alerting for production readiness.

### 6. Enhanced Message Support  
Extend beyond text to support images, documents, templates, buttons, and advanced WhatsApp interactions.