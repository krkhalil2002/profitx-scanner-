# ProfitX AWS Serverless Stock Scanner

A production-grade, fully AWS-native serverless stock scanner built for ProfitX. The system pulls market data from an external API, applies deterministic scanning rules, and exposes results to authenticated users via a REST API and frontend dashboard.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Architecture Overview

ProfitX is built entirely on AWS serverless infrastructure — no EC2, no idle servers, no manual scaling. Scans run on a schedule at market open or on demand from the dashboard. Results are stored in DynamoDB and served through API Gateway to a static frontend hosted on S3 and CloudFront.

**Core AWS Services:**
- **API Gateway** — REST API entry point
- **AWS Lambda** — scan orchestration, worker execution, results retrieval
- **Amazon DynamoDB** — scan results, job tracking, user configurations
- **Amazon EventBridge** — scheduled scan triggers
- **Amazon Cognito** — user authentication and JWT authorization
- **S3 + CloudFront** — static frontend hosting and CDN
- **AWS Secrets Manager** — secure API key storage
- **Amazon CloudWatch** — logging and observability
- **IAM** — least-privilege roles per Lambda function
- **Terraform** — all infrastructure as code
- **GitHub Actions** — CI/CD pipeline

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## How It Works

**Scheduled Scan**
EventBridge triggers the Scan Orchestrator Lambda at market open. The orchestrator fans out work to multiple Scanner Worker Lambdas running in parallel, each evaluating a batch of symbols against the filter criteria. Matching symbols are written to DynamoDB.

**Manual Scan**
An authenticated user submits filter criteria from the dashboard. The API returns a job ID immediately. The frontend polls for results until the scan completes.

**Scan Filters**
- Gap %
- Volume
- Relative Volume (RVOL)
- Float

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Project Structure
Project structure:
profitx-scanner/
├── .github/workflows/          # GitHub Actions CI/CD pipelines
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/           # API call functions
├── backend/
│   ├── functions/
│   │   ├── scan-orchestrator/
│   │   ├── scanner-worker/
│   │   ├── results-handler/
│   │   └── config-handler/
│   ├── layers/common/          # Shared Lambda utilities
│   └── tests/
├── infrastructure/
│   ├── modules/                # Terraform modules per AWS service
│   │   ├── lambda/
│   │   ├── api-gateway/
│   │   ├── dynamodb/
│   │   ├── cognito/
│   │   ├── eventbridge/
│   │   ├── s3-cloudfront/
│   │   ├── iam/
│   │   └── cloudwatch/
│   └── environments/
│       ├── dev/
│       └── prod/
└── docs/
    ├── architecture-design-document.md
    ├── architecture-diagram.png
    └── cost-breakdown.md
---------------------------------------------------------------------------------------------------------------------------------------


## Deploying the Project

### Prerequisites
- AWS CLI configured with appropriate credentials
- Terraform installed
- Node.js installed (for frontend)
- Python 3.x installed (for Lambda functions)

### Deploy to Dev

```bash
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply
```

### Deploy to Prod

```bash
cd infrastructure/environments/prod
terraform init
terraform plan
terraform apply
```

### Deploy Frontend

```bash
cd frontend
npm install
npm run build
aws s3 sync ./build s3://<your-s3-bucket-name> --delete
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## CI/CD

All deployments are automated via GitHub Actions. No manual console deployments are permitted.

- Pushes to the `dev` branch trigger the dev deployment pipeline
- Merges to `main` trigger the prod deployment pipeline
- Terraform plan is reviewed before apply on every run
- AWS credentials are stored as GitHub Secrets and never exposed in logs

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## Security

- All API endpoints are protected by Cognito JWT authentication enforced at API Gateway
- Each Lambda function has its own least-privilege IAM role
- Market data API keys are stored in AWS Secrets Manager — never hardcoded
- All data in DynamoDB is encrypted at rest using AWS KMS
- HTTPS is enforced on all CloudFront and API Gateway endpoints
- No secrets are stored in code or Terraform files
- Full audit trail of all invocations and errors in CloudWatch

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | /scans | Trigger a manual scan |
| GET | /scans | Get recent scan jobs |
| GET | /scans/{scanId} | Get results for a specific scan |
| GET | /scans/latest | Get the most recent scan results |
| POST | /configs | Save a scan configuration |
| GET | /configs | Get all saved configurations |
| DELETE | /configs/{configId} | Delete a saved configuration |

All requests require a valid Cognito JWT token in the Authorization header.

For full API documentation including request and response formats see the [Architecture Design Document](docs/architecture-design-document.md).

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## Trade-offs

**Compute — AWS Lambda over EC2**
Lambda was chosen over a traditional server because ProfitX has long idle periods overnight, on weekends, and on market holidays. A server running 24/7 with no work to do is wasted cost. Lambda runs only when invoked and scales automatically to handle market open surges. The trade-off accepted is cold starts — the first invocation after an idle period takes slightly longer to execute.

**Database — DynamoDB over RDS PostgreSQL**
DynamoDB was chosen because it is fully serverless and has no idle instance cost, which aligns with the overall serverless cost model of the system. The data access patterns in ProfitX are simple and key-based — look up results by scan ID, configs by user ID, latest results by timestamp — and DynamoDB handles those patterns extremely well. The trade-off accepted is that access patterns must be defined upfront. Unlike SQL there is no flexible ad hoc querying.

**Table Design — Single-table over Multi-table**
All data entities are stored in one DynamoDB table rather than separate tables per entity. This reduces the number of read operations needed to retrieve related data, lowers cost, and improves performance. The trade-off accepted is higher upfront design complexity — the key structure requires more careful planning than a simple multi-table approach.

**Scan Execution — Asynchronous over Synchronous**
Scans execute asynchronously. The API returns a job ID immediately and the frontend polls for results rather than waiting. This eliminates the risk of hitting API Gateway's 29 second timeout limit on long scans and enables the Lambda fan-out pattern where multiple workers run in parallel. The trade-off accepted is that the frontend must implement polling logic and results are not returned instantly.

**API Style — REST over GraphQL**
REST was chosen because the data requirements of the ProfitX frontend are simple and consistent. REST maps cleanly to the operations in the system and is natively supported by API Gateway without additional tooling or infrastructure. The trade-off accepted is fixed response shapes — REST may return slightly more data than the frontend strictly needs in some cases.

**Infrastructure — Terraform over AWS Console**
All infrastructure is defined as code in Terraform rather than clicked through the AWS console. This ensures dev and prod environments are identical, all changes are version controlled in GitHub, and the entire system can be recreated reliably. The trade-off accepted is a steeper learning curve and slower setup for small one-off changes.

**Authentication — Cognito over Custom Auth**
Cognito was chosen because it handles everything natively — password hashing, token signing, token expiry, and brute force protection — with no custom code required. The trade-off accepted is less control over custom authentication flows if unique requirements arise in the future.

**Secret Storage — Secrets Manager over Environment Variables**
Market data API keys are stored in AWS Secrets Manager rather than Lambda environment variables. Secrets Manager encrypts stored values at rest, controls access through IAM, and ensures keys never appear in code or logs. The trade-off accepted is a small amount of added latency on Lambda cold starts when the secret is retrieved at runtime.

**Frontend Hosting — S3 + CloudFront over EC2**
The frontend is hosted as a static site on S3 and served globally through CloudFront rather than running on a server. This eliminates server cost entirely, provides global CDN performance, and fully decouples frontend availability from backend load. The trade-off accepted is that the frontend is limited to static assets — there is no server side rendering.

**CI/CD — GitHub Actions + Terraform over Manual Deployments**
All deployments are automated through GitHub Actions running Terraform. No manual console deployments are permitted. This ensures every change is repeatable, reviewed before it applies, and leaves a full audit trail in GitHub. The trade-off accepted is that the pipeline requires initial setup and ongoing maintenance.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## Documentation

Full architecture design document including goals, scope, data design, system flows, scalability, security, and trade-offs is available at:

[docs/architecture-design-document.md](docs/architecture-design-document.md)

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


## Cost Awareness

ProfitX is designed to minimize cost through serverless architecture. There is no cost during idle periods — nights, weekends, and market holidays.


## Scanning Logic

### Overview
The scanner evaluates a list of stock symbols against a set of deterministic filter criteria. Any symbol that meets all conditions is written to DynamoDB as a scan result.

### Filter Criteria
| Filter | Threshold | Reason |
|--------|-----------|--------|
| Gap % | > 4% | Filters out noise, captures meaningful price movement |
| Volume | > 500,000 | Ensures sufficient liquidity |
| RVOL | > 2.0 | Confirms unusual interest relative to average activity |
| Float | < 50,000,000 | Lower float stocks produce larger moves on high volume |

### Evaluation Logic
Each Scanner Worker Lambda receives a batch of symbols and for each symbol:
1. Fetches market data from the external API
2. Evaluates the symbol against all four filters
3. If all conditions are met — writes a Scan Result record to DynamoDB
4. If any condition fails — symbol is skipped

### Design Decisions
- **Deterministic rules over ML** — rules are transparent, explainable, and consistent
- **Thresholds chosen based on standard morning gapper criteria** — commonly used by momentum day traders to identify stocks in play at market open
- **Asynchronous execution** — avoids API Gateway's 29-second timeout and enables parallel processing across multiple workers

CI/CD — GitHub Actions + Terraform over Manual Deployments
All deployments are automated through GitHub Actions running Terraform. No manual console deployments are permitted. This ensures every change is repeatable, reviewed before it applies, and leaves a full audit trail in GitHub. The trade-off accepted is that the pipeline requires initial setup and ongoing maintenance.


