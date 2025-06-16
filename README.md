# Azure Dashboard

This project is a modern dashboard application that allows you to visually track the metrics and status of your Azure DevOps projects.

## Features
- Summary information about Azure DevOps projects, pipelines, repositories, and releases
- User-friendly and modern interface
- Quick setup and easy configuration

## Installation

1. **Clone the project:**

```bash
git clone <repo-url>
cd AzureDashboard
```

2. **Set up required environment variables:**

Copy the `.env.example` file as `.env` and fill in your own Azure DevOps information:

```bash
cp .env.example .env
```

Example `.env` file:
```
AZURE_DEVOPS_ORG_URL= # e.g. https://dev.azure.com/<your-org>
AZURE_DEVOPS_PAT=     # Azure DevOps Personal Access Token
```

3. **Start the application with Docker Compose:**

```bash
docker-compose up --build
```

All services will start automatically. You can access the application from your browser.

## License
This project is licensed under the MIT License.
