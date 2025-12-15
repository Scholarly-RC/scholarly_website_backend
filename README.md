# Scholarly Website Backend

A Django REST API backend for a scholarly website featuring a RAG (Retrieval Augmented Generation) chatbot powered by OpenAI and Pinecone, along with contact form email functionality.

## Features

- 🤖 **RAG Chatbot**: Query scholarly data using OpenAI and Pinecone vector database
- 📧 **Contact Form**: Async email sending using Django Q
- 🔄 **Task Queue**: Background job processing with Django Q2 and Redis
- 🚀 **Production Ready**: Configured for Railway deployment with uv
- 🔒 **CORS Support**: Configured for frontend integration
- 📦 **Modern Tooling**: Uses uv for fast dependency management

## Tech Stack

- **Framework**: Django 5.1.6
- **API**: Django REST Framework
- **Task Queue**: Django Q2 with Redis
- **Vector Database**: Pinecone
- **AI/LLM**: OpenAI (DSPy)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis
- **Package Manager**: uv
- **Server**: Gunicorn
- **Static Files**: WhiteNoise

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Redis (for task queue and caching)
- PostgreSQL (for production)
- Pinecone account and API key
- OpenAI API key

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd scholarly_website_backend
```

### 2. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Database (PostgreSQL for production)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=your_db_name
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_HOST=localhost
# DB_PORT=5432

# Redis/Broker URL
BROKER_URL=redis://localhost:6379/0

# Email Configuration (Brevo/SendGrid)
DEFAULT_FROM_EMAIL=noreply@example.com
EMAIL_HOST_USER=your_email_user
EMAIL_HOST_PASSWORD=your_email_password

# Frontend URL
FRONTEND_URL=http://localhost:3000
LOGO_URL=https://your-logo-url.com/logo.png

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
PINECONE_ENVIRONMENT=us-east-1

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_LLM_MODEL=openai/gpt-5-nano
```

### 5. Run migrations

```bash
uv run python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
uv run python manage.py createsuperuser
```

### 7. Collect static files

```bash
uv run python manage.py collectstatic
```

## Running the Application

### Development Server

```bash
uv run python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Running with Task Queue

For full functionality, you need to run the Django Q cluster:

```bash
# Terminal 1: Django server
uv run python manage.py runserver

# Terminal 2: Django Q cluster
uv run python manage.py qcluster
```

### Using Docker Compose

```bash
docker-compose up
```

## API Endpoints

### Chatbot Query

Query the scholarly data using the RAG chatbot.

**Endpoint**: `POST /api/chatbot/`

**Request Body**:
```json
{
  "question": "What is the main topic of the research?"
}
```

**Response**:
```json
{
  "answer": "The generated answer based on the scholarly data...",
  "sources": ["source chunk 1", "source chunk 2"]
}
```

### Contact Us Email

Send a contact form email asynchronously.

**Endpoint**: `POST /api/contact-us-email/`

**Request Body**:
```json
{
  "email": "user@example.com",
  "subject": "Inquiry about research",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "message": "Email successfully processed."
}
```

## Deployment on Railway

This project is configured for deployment on Railway using uv.

### Prerequisites

1. Railway account
2. Railway CLI (optional, can use web interface)
3. All environment variables set in Railway dashboard

### Deployment Steps

1. **Connect Repository**: Link your GitHub repository to Railway

2. **Set Environment Variables**: Add all required environment variables in the Railway dashboard:
   - `SECRET_KEY`
   - `DEBUG=False`
   - Database credentials
   - `BROKER_URL` (Redis connection string)
   - Email credentials
   - Pinecone and OpenAI API keys
   - Frontend URL and logo URL

3. **Add Services** (if needed):
   - PostgreSQL database
   - Redis instance

4. **Deploy**: Railway will automatically:
   - Detect `pyproject.toml` and `uv.lock`
   - Use `nixpacks.toml` for build configuration
   - Run migrations and start the server using `Procfile`

### Configuration Files

- **`nixpacks.toml`**: Configures Railway to use uv and Python 3.11
- **`Procfile`**: Defines the web process command
- **`runtime.txt`**: Specifies Python version (3.11)

## Project Structure

```
scholarly_website_backend/
├── api/                    # Main API application
│   ├── rag/               # RAG chatbot implementation
│   ├── tasks.py           # Async tasks (email sending)
│   ├── views.py           # API views
│   └── urls.py            # URL routing
├── scholarly_website_backend/  # Django project settings
│   ├── settings.py        # Django configuration
│   └── urls.py            # Root URL configuration
├── static/                # Static files
├── templates/             # Django templates
├── pyproject.toml         # Project dependencies (uv)
├── uv.lock                # Locked dependencies
├── nixpacks.toml          # Railway build configuration
├── Procfile               # Railway process file
└── .env                   # Environment variables (not in git)
```

## Development

### Code Formatting

This project uses `black` and `isort` for code formatting:

```bash
# Format code
uv run black .
uv run isort .
```

### Running Tests

```bash
uv run python manage.py test
```

### Database Migrations

```bash
# Create migrations
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (True/False) | Yes |
| `DB_ENGINE` | Database engine | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | Database user | If using PostgreSQL |
| `DB_PASSWORD` | Database password | If using PostgreSQL |
| `DB_HOST` | Database host | If using PostgreSQL |
| `DB_PORT` | Database port | If using PostgreSQL |
| `BROKER_URL` | Redis connection URL | Yes |
| `DEFAULT_FROM_EMAIL` | Default sender email | Yes |
| `EMAIL_HOST_USER` | Email service username | Yes |
| `EMAIL_HOST_PASSWORD` | Email service password | Yes |
| `FRONTEND_URL` | Frontend application URL | Yes |
| `LOGO_URL` | Logo image URL | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | Yes |
| `PINECONE_ENVIRONMENT` | Pinecone environment | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_LLM_MODEL` | OpenAI model identifier | Yes |

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

