# Technology Stack

This document outlines the technologies and libraries used in the Automation & Web Scraping Platform MVP.

## Core Infrastructure

The platform is designed to be cloud-agnostic and container-native.

- **Docker & Docker Compose**: Orchestration of all services. No local installation required beyond Docker.
- **Python 3.11**: Main programming language for all back-end logic.

## Back-End Services

### Frameworks & Libraries
- **FastAPI**: Used for both `App Console` and `Core Orchestrator` APIs. Provides automatic OpenAPI documentation.
- **SQLAlchemy (Async)**: ORM for interacting with PostgreSQL.
- **Pydantic**: Data validation and settings management (`pydantic-settings`).
- **AioPika**: Asynchronous RabbitMQ client for publishing and consuming messages.
- **Motor / AsyncIOMotor**: Asynchronous MongoDB driver.
- **Google Client Library**: `google-api-python-client` for interacting with Gmail API.
- **Cryptography**: Using `Fernet` (symmetric encryption) for securing stored API tokens.

### Web Scraping / Browser Automation
- **Selenium WebDriver**: Browser automation interface.
- **Selenium Standalone Chrome**: Official Docker image providing a headless Chrome instance manageable via Remote WebDriver.

### Frontend Dashboard
- **React 19**: UI Library for building the interactive dashboard.
- **TypeScript**: Strictly typed codebase for reliability and maintainability.
- **Vite**: Build tool and development server for fast HMR.
- **Tailwind CSS 4**: Utility-first CSS framework for styling.
- **Axios**: HTTP client for communicating with the App Console API.
- **React Router v7**: For client-side routing.

## Data Storage

- **MongoDB (6-jammy)**:
  - **Primary Database**: Stores all application data including Workspaces, Jobs, Runs, and scraped payloads.
  - Flexible schema allows for storing varied scraping results (HTML/JSON dumps).
- **Redis (7-alpine)**:
  - Used for ephemeral state: Distributed Locks (future use), Rate Limiting, and **OTP Synchronization** (passing codes between Inbox Worker and Scraper Worker).

## Message Broker

- **RabbitMQ (3-management)**:
  - Decouples the API from the execution workers.
  - Exchanges:
    - `jobs`: Direct exchange for routing tasks.
  - Queues:
    - `scrape.default`: Main scraping tasks.
    - `otp.request`: OTP challenge requests.
    - DLQs (Dead Letter Queues): Configured for failed messages processing.
