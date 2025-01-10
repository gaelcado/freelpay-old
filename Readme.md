# Freelpay Application

A full-stack application for freelancers to manage invoices and get paid instantly. Built with Next.js, FastAPI, and Supabase.

## 🏗️ Architecture

- **Frontend**: Next.js with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: Supabase
- **Deployment**: DigitalOcean App Platform

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.9+
- Supabase account
- DigitalOcean account (for deployment)

### Environment Variables

#### Frontend (.env)

- `NEXT_PUBLIC_API_URL`= http://localhost:8000 or https://freelpay.com/api
- `NEXT_PUBLIC_SUPABASE_URL`= your_supabase_url
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`= your_supabase_anon_key

#### Backend (.env)

- `JWT_SECRET_KEY` = your_jwt_secret_key
- `OPENAI_API_KEY` = your_openai_api_key
- `MONGODB_DB_NAME` = your_mongodb_database_name
- `MONGO_URI` = your_mongodb_uri
- `SUPABASE_DB_NAME` = your_supabase_database_name
- `SUPABASE_URL` = your_supabase_url
- `SUPABASE_ANON_KEY` = your_supabase_anon_key
- `SUPABASE_SERVICE_KEY` = your_supabase_service_key
- `SUPABASE_POSTGRES_URI` = your_supabase_postgres_uri
- `FRONTEND_URL` = http://localhost:3000 or https://freelpay.com
- `SIREN_API_KEY` = your_siren_api_key
- `APP_URL` = http://localhost:8000 or https://freelpay.com/api
- `PENNYLANE_API_KEY` = your_pennylane_api_key
- `PANDADOC_API_KEY` = your_pandadoc_api_key

### Running Locally with Docker

1. Clone the repository:

```bash
git clone https://github.com/IllanKnf/freelpay-nextjs.git
cd freelpay-nextjs
```

2. Create a `.env` file in the `frontend` and `backend` directories with the necessary environment variables.

3. Start the application using Docker Compose:

```bash
docker compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Running Without Docker

#### Frontend

1. Navigate to the `frontend` directory:

```bash
cd frontend
``` 

2. Install dependencies:

```bash
npm install
```

3. Start the frontend development server:

```bash
npm run dev
```

#### Backend

1. Navigate to the `backend` directory:

```bash
cd backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the backend server:

```bash
uvicorn main:app --reload
```


## 🌐 Deployment to DigitalOcean

The application is configured to deploy to DigitalOcean App Platform using the `app.yaml` configuration file.

1. Install the DigitalOcean CLI:

```bash
brew install doctl
```

2. Authenticate with DigitalOcean:

```bash
doctl auth init
```

3. Create a new app:

```bash
doctl apps create --spec app.yaml
```

### Environment Variables on DigitalOcean

Check if the following environment variables are well set in your DigitalOcean App Platform dashboard:

- `MONGO_URI`
- `MONGODB_DB_NAME`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- `FRONTEND_URL`
- `SUPABASE_DB_NAME`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_POSTGRES_URI`
- `SIREN_API_KEY`
- `PENNYLANE_API_KEY`
- `PANDADOC_API_KEY`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## 📦 Database Setup

This project uses Supabase as the database. To set up your database:

1. Create a new project on [Supabase](https://supabase.com)
2. Copy your project URL and anon key
3. Update your environment variables with the Supabase credentials
