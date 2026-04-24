# Campus Buzz - Campus Event Submission & Review System

A hybrid cloud system for campus event submission and review, combining **Docker containers** and **Alibaba Cloud Serverless Functions (FC 3.0)**.

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Docker Containers                           │
│                                                                    │
│     [Presentation] ──→ [Workflow] ──→ [Data Service + SQLite]      │
│        :5000            :5001              :5002                   │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTP Trigger
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                Alibaba Cloud FC 3.0 (Serverless)                   │
│                                                                    │
│  [Submission Event FN] ──→ [Processing FN] ──→ [Result Update FN]  │
│      (event trigger)       (Rule judgment)      (Result feedback)  │
│                                                                    │
│                  ──→ Data Service (via public URL)                 │
└────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Type | Port | Description |
|-----------|------|------|-------------|
| Presentation Service | Docker Container | 5000 | Web UI + API reverse proxy |
| Workflow Service | Docker Container | 5001 | Receives submissions, triggers FC functions |
| Data Service | Docker Container | 5002 | SQLite CRUD for submission records |
| Submission Event Function | Alibaba Cloud FC | — | Event trigger: fetches record & invokes Processing |
| Processing Function | Alibaba Cloud FC | — | Applies 5 validation rules, classifies & prioritizes |
| Result Update Function | Alibaba Cloud FC | — | Writes processing results back to Data Service |

### Processing Rules (Priority Order)

1. **Required fields check** → Missing field → `INCOMPLETE`
2. **Date format** → Must be `YYYY-MM-DD` → `NEEDS REVISION`
3. **Description length** → Min 40 chars → `NEEDS REVISION`
4. **Keyword classification** → `OPPORTUNITY > ACADEMIC > SOCIAL > GENERAL`
5. **Priority assignment** → `HIGH > MEDIUM > NORMAL`

## Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) (for Serverless Devs CLI)
- [Alibaba Cloud Account](https://www.aliyun.com/) with FC service enabled
- [ngrok](https://ngrok.com/) (or similar) for exposing Data Service to the internet

## Quick Start

### Step 1: Install Serverless Devs & Configure Credentials

```bash
# Install Serverless Devs CLI
npm install -g @serverless-devs/s

# Configure Alibaba Cloud credentials
s config add
# Enter your AccountID, AccessKeyID, AccessKeySecret when prompted
```

### Step 2: Install Python Dependencies for FC Functions

FC Custom Runtime requires all dependencies packaged with the code:

```bash
# Submission Event Function
cd serverless/submission-event-function
pip install -t . -r requirements.txt
cd ../..

# Processing Function
cd serverless/processing-function
pip install -t . -r requirements.txt
cd ../..

# Result Update Function
cd serverless/result-update-function
pip install -t . -r requirements.txt
cd ../..
```

### Step 3: Deploy FC Functions (First Round)

```bash
# Set Data Service public URL (use ngrok or similar)
# For first deployment, PROCESSING_FN_URL and RESULT_UPDATE_FN_URL can be placeholders
export DATA_SERVICE_URL="https://your-ngrok-url.ngrok.io"
export PROCESSING_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"
export RESULT_UPDATE_FN_URL="https://placeholder.cn-beijing.fc.aliyuncs.com"

# Deploy all functions
s deploy --all
```

**Record the HTTP trigger URLs from the output!** They look like:
```
submission-event-function: https://xxxxx.cn-beijing.fc.aliyuncs.com
processing-function:       https://yyyyy.cn-beijing.fc.aliyuncs.com
result-update-function:    https://zzzzz.cn-beijing.fc.aliyuncs.com
```

### Step 4: Redeploy FC Functions with Correct URLs

```bash
# Set correct URLs from Step 3
export DATA_SERVICE_URL="https://your-ngrok-url.ngrok.io"
export PROCESSING_FN_URL="https://yyyyy.cn-beijing.fc.aliyuncs.com"
export RESULT_UPDATE_FN_URL="https://zzzzz.cn-beijing.fc.aliyuncs.com"

# Redeploy
s deploy --all
```

### Step 5: Expose Data Service to the Internet

FC functions need to call your local Data Service. Use ngrok:

```bash
# In a separate terminal
ngrok http 5002
```

Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and update:
- The `DATA_SERVICE_URL` environment variable in FC functions (redeploy if needed)
- The `DATA_SERVICE_URL` in your `.env` file

### Step 6: Configure & Start Container Services

```bash
# Copy and edit environment config
cp .env.example .env
# Edit .env and fill in the FC function URLs

# Start all container services
docker-compose up --build
```

### Step 7: Verify

1. Open http://localhost:5000 in your browser
2. Submit a campus event
3. Check the Alibaba Cloud FC console for function invocation logs
4. Verify the record status updates in the UI

## Testing

```bash
# Run the end-to-end test script
python scripts/test_e2e.py
```

## Project Structure

```
Cloud-Project/
├── docker-compose.yml              # Container orchestration (3 services)
├── s.yaml                          # Alibaba Cloud FC deployment config
├── .env.example                    # Environment variable template
├── presentation-service/           # Container: Web UI + API proxy
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── workflow-service/               # Container: Workflow orchestration
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── data-service/                   # Container: Data persistence (SQLite)
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── serverless/                     # Alibaba Cloud FC Functions
│   ├── submission-event-function/  #   Event trigger
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── processing-function/        #   Rule engine
│   │   ├── app.py
│   │   └── requirements.txt
│   └── result-update-function/     #   Result writer
│       ├── app.py
│       └── requirements.txt
├── scripts/
│   ├── deploy-fc.sh                # FC deployment helper script
│   └── test_e2e.py                 # End-to-end test
└── README.md
```
