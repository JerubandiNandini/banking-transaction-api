# Banking Transaction API

An enterprise-grade FastAPI application for managing banking transactions (deposits, withdrawals, transfers), deployed with Azure DevOps, Docker, and Azure Web App. The project includes advanced features tailored for the banking sector, such as OAuth 2.0 with Azure AD, Azure Key Vault for encryption, Redis caching, Kafka for event-driven processing, ELK Stack for logging, and Prometheus/Grafana for monitoring.

## Banking Context

This project addresses key banking requirements:
- Compliance: Audit trails, transaction rollback, and mocked Azure Sentinel integration for GDPR/PCI-DSS compliance.
- Security: OAuth 2.0 with Azure AD, Azure Key Vault for secrets, and encrypted account data.
- Scalability: Redis caching for account balances, async PostgreSQL queries with `asyncpg`, and Kafka for event-driven transactions.
- Performance: Database indexing, table partitioning, and load testing with Locust.
- Monitoring: ELK Stack for logs, Prometheus/Grafana for metrics, and Kibana for transaction analytics.

## Folder Structure

The project is organized as follows:

```
/banking-transaction-api
├── /app
│   ├── main.py              # FastAPI application with Prometheus metrics
│   ├── models.py            # Pydantic models for request/response validation
│   ├── database.py          # Async PostgreSQL setup with indexing and partitioning
│   ├── auth.py              # OAuth 2.0 with Azure AD integration
│   ├── logging_config.py    # ELK Stack and mocked Azure Sentinel logging
│   ├── kafka_producer.py    # Kafka producer for transaction events
│   ├── kafka_consumer.py    # Kafka consumer for async event processing
│   ├── encryption.py        # Data encryption with Azure Key Vault
│   ├── init_db.py           # Database initialization script
├── /tests
│   ├── BankingAPI.postman_collection.json  # Postman collection for API testing
│   ├── BankingAPI.postman_environment.json # Postman environment with variables
│   ├── load_test.py         # Locust script for load testing
├── /monitoring
│   ├── prometheus.yml       # Prometheus configuration for metrics scraping
│   ├── grafana_dashboard.json # Grafana dashboard for transaction metrics
│   ├── kibana_dashboard.ndjson # Kibana dashboard for log analytics
├── Dockerfile               # Docker configuration for FastAPI app
├── docker-compose.yml       # Local dev setup with PostgreSQL, Redis, Kafka, ELK
├── requirements.txt         # Python dependencies
├── azure-pipelines.yml      # Azure DevOps pipeline for CI/CD
├── logstash.conf            # Logstash configuration for ELK Stack
├── .env.example             # Example environment variables
├── README.md                # Project setup and execution guide
```

## Setup Instructions

### 1. Prerequisites

- Azure Account: Required for Azure Web App, Azure Container Registry (ACR), Azure Key Vault, and Azure Active Directory (AD).
- Azure DevOps: For CI/CD pipeline.
- Docker and Docker Compose: For local development and running services (PostgreSQL, Redis, Kafka, ELK).
- Python 3.9: For running scripts and tests locally.
- Node.js: For running Postman tests with Newman.
- Tools: `psql` (optional for database verification), `curl` (for monitoring checks).

### 2. Azure AD Setup

To enable OAuth 2.0 authentication:
1. Register an Application:
   - Go to Azure Portal > Azure Active Directory > App registrations > New registration.
   - Set Name (e.g., "BankingAPI"), select "Web" platform, and set Redirect URI (e.g., `http://localhost:8000/docs/oauth2-redirect`).
   - Note the **Application (client) ID** and **Directory (tenant) ID**.
   - Create a client secret: App registrations > Your app > Certificates & secrets > New client secret.
   - Grant API permissions (e.g., `User.Read`).
2. Generate Tokens:
   - Use Postman to request a token:
     - Endpoint: `https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/oauth2/v2.0/token`
     - Grant Type: Client Credentials
     - Client ID: `{AZURE_AD_CLIENT_ID}`
     - Client Secret: Your secret
     - Scope: `{AZURE_AD_CLIENT_ID}/.default`
   - Save the access token as `admin_token` or `customer_token` in `tests/BankingAPI.postman_environment.json`.
   - Set `CUSTOMER_TOKEN` in `.env` for Locust tests.
3. Local Testing Fallback:
   - If Azure AD setup is unavailable, use a mock JWT for local testing:
     - Generate a JWT with `SECRET_KEY` (e.g., `your-secret-key`) using a tool like `jwt.io`.
     - Example payload: `{"sub": "user1", "preferred_username": "user@domain.com", "aud": "your-client-id"}`.
     - Use this token in Postman (`customer_token`) and `.env` (`CUSTOMER_TOKEN`).

### 3. Environment Setup

1. Copy Environment File:
   ```bash
   cp .env.example .env
   ```
2. Update `.env`:
   - Set `JWT_SECRET_KEY` (e.g., a secure random string).
   - Set `AZURE_AD_TENANT_ID` and `AZURE_AD_CLIENT_ID` from Azure AD.
   - Set `KEY_VAULT_URL` (e.g., `https://your-vault.vault.azure.net/`).
   - Set `SENTINEL_ENDPOINT` and `SENTINEL_TOKEN` (use mocks for local dev: `https://mock-sentinel-api.azure.com/log`, `mock-token`).
   - Set `CUSTOMER_TOKEN` for Locust tests (Azure AD token or mock JWT).
   - Example `.env`:
     ```
     JWT_SECRET_KEY=your-secret-key
     AZURE_AD_TENANT_ID=your-tenant-id
     AZURE_AD_CLIENT_ID=your-client-id
     KEY_VAULT_URL=https://your-vault.vault.azure.net/
     SENTINEL_ENDPOINT=https://mock-sentinel-api.azure.com/log
     SENTINEL_TOKEN=mock-token
     CUSTOMER_TOKEN=your-customer-token
     ```

### 4. Dependency Installation

Install Python and Node.js dependencies:
```bash
pip install -r requirements.txt
npm install -g newman
```

### 5. Database Setup

1. Start PostgreSQL:
   ```bash
   docker-compose up -d postgres
   ```
2. Initialize Database:
   ```bash
   python app/init_db.py
   ```
   - This creates `accounts` and `transactions` tables with partitions and indexes.
   - Verify with `psql`:
     ```bash
     docker exec -it <postgres-container> psql -U user -d banking_db -c "\dt"
     ```

### 6. Run Locally

1. Start All Services:
   ```bash
   docker-compose up --build -d
   ```
   - This starts FastAPI, PostgreSQL, Redis, Kafka, Zookeeper, Elasticsearch, Logstash, and Kibana.
   - Check service status:
     ```bash
     docker ps
     ```
2. Access API:
   - Open `http://localhost:8000/docs` for the Swagger UI with endpoints `/accounts`, `/transactions`, `/metrics`.

### 7. Run Kafka Consumer

Run the Kafka consumer to process transaction events (e.g., for fraud detection):
```bash
python app/kafka_consumer.py
```
- Logs will show consumed events and flag suspicious transactions (amount > 10,000).

### 8. Monitoring

1. ELK Stack:
   - Access Kibana at `http://localhost:5601`.
   - View transaction logs and analytics in the "Banking Transactions" dashboard.
2. Prometheus:
   - Access at `http://localhost:9090`.
   - Query `transactions_total` for transaction metrics.
3. Grafana:
   - Access at `http://localhost:3000` (default login: admin/admin).
   - Import `monitoring/grafana_dashboard.json` to view transaction rate graphs.

### 9. Testing

1. Postman Tests:
   - Update `tests/BankingAPI.postman_environment.json` with valid `admin_token` and `customer_token`.
   - Run tests:
     ```bash
     newman run tests/BankingAPI.postman_collection.json --environment tests/BankingAPI.postman_environment.json
     ```
   - Expected: 2 tests pass (create account, create transaction).
2. Locust Load Tests:
   - Ensure `CUSTOMER_TOKEN` is set in `.env`.
   - Run:
     ```bash
     pip install locust
     locust -f tests/load_test.py
     ```
   - Access Locust UI at `http://localhost:8089` and simulate 100 users.

### 10. Azure DevOps Deployment

1. Create Pipeline:
   - Import `azure-pipelines.yml` into Azure DevOps.
   - Configure service connections for Azure Subscription, ACR, and Web App.
2. Set Pipeline Variables:
   - Add `JWT_SECRET_KEY`, `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, `KEY_VAULT_URL`, `SENTINEL_ENDPOINT`, `SENTINEL_TOKEN`, `CUSTOMER_TOKEN` in the pipeline settings.
3. Run Pipeline:
   - Builds Docker image, runs Postman/Locust tests, and deploys to Azure Web App.

## Expected Output

- API: Swagger UI at `http://localhost:8000/docs` with endpoints:
  - `POST /accounts`: Create accounts (admin only).
  - `POST /transactions`: Create transactions (deposit, withdrawal, transfer).
  - `GET /transactions`: List transactions.
  - `GET /metrics`: Prometheus metrics.
- Database: Tables `accounts` and `transactions` with partitions (`accounts_low`, `accounts_high`) and indexes.
- Kafka: Consumer logs show transaction events (e.g., `Consumed transaction event`) and flag suspicious transactions.
- Logs: Kibana displays logs (e.g., "Transaction processed", "Account created").
- Metrics: Prometheus shows `transactions_total` metrics; Grafana displays transaction rates.
- Tests:
  - Postman: 2 tests pass.
  - Locust: Simulates 100 users with no errors.

## Troubleshooting and Additional Notes

### Potential Errors and Fixes

1. Connection Errors:
   - Issue: App fails to connect to PostgreSQL (`postgres:5432`), Redis (`redis:6379`), or Kafka (`kafka:9092`).
   - Fix:
     - Verify Docker services are running:
       ```bash
       docker ps
       ```
     - Check logs for errors:
       ```bash
       docker logs <container>
       ```
     - Ensure `docker-compose.yml` health checks pass (e.g., `pg_isready`, `redis-cli ping`).
   - Example: If PostgreSQL fails, restart:
     ```bash
     docker-compose restart postgres
     ```

2. Token Errors:
   - Issue: `401 Unauthorized` in Postman or Locust due to invalid Azure AD tokens.
   - Fix:
     - Regenerate tokens using Postman (see Azure AD Setup).
     - Use a mock JWT for local testing (see Azure AD Setup > Local Testing Fallback).
     - Update `CUSTOMER_TOKEN` in `.env` and `tests/BankingAPI.postman_environment.json`.

3. Dependency Errors:
   - Issue: `ModuleNotFoundError` or missing packages.
   - Fix:
     - Reinstall dependencies:
       ```bash
       pip install -r requirements.txt
       ```
     - Ensure Python 3.9 is used (as per `Dockerfile`).

4. Database Initialization Failure:
   - Issue: `python app/init_db.py` fails with connection or schema errors.
   - Fix:
     - Ensure PostgreSQL is running (`docker-compose up -d postgres`).
     - Check `DATABASE_URL` in `app/database.py` matches PostgreSQL credentials (`user:password@postgres:5432/banking_db`).
     - Rerun:
       ```bash
       python app/init_db.py
       ```

5. Kafka Consumer Errors:
   - Issue: `kafka_consumer.py` fails to connect or consume events.
   - Fix:
     - Ensure Kafka and Zookeeper are running:
       ```bash
       docker-compose up -d kafka zookeeper
       ```
     - Check consumer logs:
       ```bash
       python app/kafka_consumer.py
       ```

### Local Testing Without Azure Services

- If Azure AD, Key Vault, or Sentinel are unavailable:
  - Azure AD: Use a mock JWT (see Azure AD Setup > Local Testing Fallback).
  - Key Vault: `app/encryption.py` falls back to a generated key if Key Vault fails.
  - Sentinel: `app/logging_config.py` uses a mock endpoint (`https://mock-sentinel-api.azure.com/log`) and logs errors locally.
- The app runs fully locally with `docker-compose`, relying on mock configurations in `.env`.

### Additional Tips

- Verify Services: Use `curl` to check service availability:
  ```bash
  curl http://localhost:9200  # Elasticsearch
  curl http://localhost:5601  # Kibana
  curl http://localhost:9090  # Prometheus
  ```
- Debugging: Check Docker logs for service issues:
  ```bash
  docker logs banking-transaction-api-app-1
  ```
- Mock JWT Example:
  - Generate at `jwt.io` with:
    - Header: `{"alg": "HS256", "typ": "JWT"}`
    - Payload: `{"sub": "user1", "preferred_username": "user@domain.com", "aud": "your-client-id"}`
    - Secret: `your-secret-key` (from `.env`).
  - Use in Postman or `.env` for testing.

## Enhancements Implemented

- Security: OAuth 2.0 with Azure AD, Azure Key Vault for secrets, and encryption of sensitive data.
- Scalability: Redis caching for account balances, async PostgreSQL queries with `asyncpg`, Kafka for event-driven processing.
- Compliance: Transaction rollback for transfers, audit logging, and mocked Azure Sentinel integration.
- Performance: Database indexing, table partitioning, and load testing with Locust.
- Monitoring: ELK Stack for logs, Prometheus/Grafana for metrics, Kibana for transaction analytics.
- CI/CD**: Azure DevOps pipeline with Docker, Newman tests, and deployment to Azure Web App.