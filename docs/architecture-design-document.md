ProfitX AWS Serverless Stock Scanner ADD



\- Overview



Purpose: Design, build, deploy, and document a production-grade, fully AWS-native serverless stock scanner for ProfitX.



Goals:



\- Enhanced scalability, able to handle spikes in scan requests without performance degradation

\- Low latency, return scan results within an acceptable window

\- Maintainability, scanning logic should be modular so new filters and indicators can be added without rearchitecting

\- Security, protects any user data as well as contain API keys for market data providers



Scope:



\- Included:

&#x20; - market ingestion

&#x20; - Deterministic scanning logic

&#x20; - Authenticated user access via Cognito

&#x20; - Scheduled and on-demand scans

&#x20; - Frontend dashboard hosted on S3 + CloudFront

&#x20; - Full IaC via Terraform + CI/CD via GitHub Actions

\- Not included:

&#x20; - Trade execution

&#x20; - Portfolio management

&#x20; - Backtesting

&#x20; - Real-time streaming (WebSocket)

&#x20; - AI summaries (stretch goal, not core)



\- Requirements



Functional Requirements "what does it do?" :



\- Filter by gap %, volume, RVOL, float

\- Store scan results with timestamp

\- Allow authenticated users to retrieve results

\- Be deployable in dev and prod environments

\- Have cost awareness documented



Non-Functional Requirements "how well does it do it?" :



\- No hardcoded secrets (Secrets Manager)

\- Least-privilege IAM policies

\- Full logging via CloudWatch

\- No EC2 - serverless only

\- Cost-optimized (pay-per-invocation)



\- High-Level Architecture



\- Flow:

&#x20; - API Gateway → Lambda → DynamoDB

\- EventBridge for scheduled scans

\- Cognito for auth

\- S3 + CloudFront for frontend

\- Secrets Manager for API keys

\- CloudWatch for logging

\- Terraform for IaC

\- GitHub Actions for CI/CD



\- System Components



\- API Gateway

&#x20; - Serves as the entry point for all client requests

&#x20; - Routes HTTP requests to the appropriate Lambda function

&#x20; - Handles request validation and throttling

&#x20; - Why?: Fully managed, scales automatically, integrates natively with Lambda and Cognito

\- AWS Lambda

&#x20; - Executes the core scanning logic

&#x20; - Separate functions for: triggering scans, processing symbols, returning results

&#x20; - Why?: No idle cost, scales per request, perfect for event-driven workloads

\- Amazon DynamoDB

&#x20; - Stores scan results with timestamps

&#x20; - Stores user scan configurations

&#x20; - Why?: Serverless, no provisioning, fast single-digit millisecond reads, scales automatically - vs RDS which requires a running instance

\- Amazon EventBridge

&#x20; - Triggers scheduled scans on a defined cron schedule (e.g., market open/close)

&#x20; - Why?: Native AWS scheduler, integrates directly with Lambda, no server needed

\- Amazon Cognito

&#x20; - Handles user authentication and authorization

&#x20; - Issues JWT tokens validated by API Gateway before requests reach Lambda

&#x20; - Why?: Fully managed auth, no custom auth server needed

\- S3 + CloudFront

&#x20; - S3 hosts the static frontend dashboard files

&#x20; - CloudFront serves as the CDN layer for low-latency global delivery

&#x20; - Why?: Cheap, scalable static hosting with built-in caching and HTTPS

\- AWS Secrets Manager

&#x20; - Stores market data API keys securely

&#x20; - Lambda retrieves secrets at runtime, never hardcoded

&#x20; - Why?: Prevents credential exposure in code or environment variables

\- CloudWatch

&#x20; - Captures Lambda logs, errors, and execution metrics

&#x20; - Alerts on failures or performance degradation

&#x20; - Why?: Native AWS observability, zero setup for Lambda integration

\- IAM

&#x20; - Controls permissions for every service-to-service interaction

&#x20; - Each Lambda function gets its own least-privilege role

&#x20; - Why?: Security boundary - no function can access resources it doesn't need

\- Terraform

&#x20; - Defines all infrastructure as code

&#x20; - Manages dev and prod environments separately

&#x20; - Why?: Repeatable, version-controlled deployments - no console-click infrastructure

\- GitHub Actions

&#x20; - CI/CD pipeline that runs tests and deploys via Terraform on push

&#x20; - Why?: Automates deployment, enforces standards, integrates with your GitHub repo

\- External Market Data API

&#x20; - Third-party provider supplying price, volume, float, and RVOL data

&#x20; - System depends on this as its data source



\- Data Design



\- Database: DynamoDB

&#x20; - Why DB over RDS?: DynamoDB was chosen over RDS because it is fully serverless, requires no idle instance, scales automatically, and fits the key-based lookup patterns of this system.



&#x20; 5.1. Data Entries



\- Scan Result:



| Field           | Type   | Description                                           |

| --------------- | ------ | ----------------------------------------------------- |

| P(rimary) K(ey) | String | SCAN#\&lt;scanID\&gt;                                   |

| ---             | ---    | ---                                                   |

| S(ort) K(ey)    | String | SYMBOL#\&lt;ticker\&gt;                                 |

| ---             | ---    | ---                                                   |

| ticker          | String | Stock symbol (e.g. AAPL)                              |

| ---             | ---    | ---                                                   |

| scanID          | String | ID of the parent scan job                             |

| ---             | ---    | ---                                                   |

| timestamp       | String | ISO 8601 datetime of scan execution                   |

| ---             | ---    | ---                                                   |

| price           | Number | Stock Price at time of scan                           |

| ---             | ---    | ---                                                   |

| volume          | Number | Volume at the time of scan                            |

| ---             | ---    | ---                                                   |

| rvol            | Number | Relative Volume                                       |

| ---             | ---    | ---                                                   |

| float           | Number | Share float                                           |

| ---             | ---    | ---                                                   |

| gapPercent      | Number | Gap percentage                                        |

| ---             | ---    | ---                                                   |

| ttl             | Number | Epoch timestamp - record auto-expires after this date |

| ---             | ---    | ---                                                   |



\- Scan Job:



| Field       | Type   | Description                             |

| ----------- | ------ | --------------------------------------- |

| PK          | String | JOB#\&lt;jobId\&gt;                       |

| ---         | ---    | ---                                     |

| SK          | String | METADATA                                |

| ---         | ---    | ---                                     |

| jobID       | String | Unique scan job identifier              |

| ---         | ---    | ---                                     |

| triggeredBy | String | "scheduled" or "user"                   |

| ---         | ---    | ---                                     |

| status      | String | pending/running/complete/<br><br>failed |

| ---         | ---    | ---                                     |

| criteria    | Map    | Filter values used in this scan         |

| ---         | ---    | ---                                     |

| startTime   | String | ISO 8601 start timestamp                |

| ---         | ---    | ---                                     |

| endTime     | String | ISO 8601 end timestamp                  |

| ---         | ---    | ---                                     |

| resultCount | Number | Number of symbols that matched          |

| ---         | ---    | ---                                     |



\- User Scan Configuration:



| Field      | Type   | Description                                 |

| ---------- | ------ | ------------------------------------------- |

| PK         | String | USER#\&lt;userId\&gt;                         |

| ---        | ---    | ---                                         |

| SK         | String | CONFIG#\&lt;configId\&gt;                     |

| ---        | ---    | ---                                         |

| userId     | String | Cognito user ID                             |

| ---        | ---    | ---                                         |

| configName | String | User-defined name for this preset           |

| ---        | ---    | ---                                         |

| filters    | Map    | minGapPercent, minVolume, maxFloat, minRVOL |

| ---        | ---    | ---                                         |

| createdAt  | String | ISO 8601 creation timestamp                 |

| ---        | ---    | ---                                         |

| lastRunAt  | String | ISO 8601 timestamp of last execution        |

| ---        | ---    | ---                                         |



\- Access Patterns:



| Access Pattern                   | Key Condition                                               |

| -------------------------------- | ----------------------------------------------------------- |

| Get all results for a scan       | PK = SCAN#\&lt;scanId\&gt;                                    |

| ---                              | ---                                                         |

| Get one symbol within a scan     | PK = SCAN#\&lt;scanId\&gt;,<br><br>SK = SYMBOL#\&lt;ticker\&gt; |

| ---                              | ---                                                         |

| Get scan job metadata            | PK = JOB#\&lt;jobId\&gt;,<br><br>SK = METADATA                |

| ---                              | ---                                                         |

| Get all saved configs for a user | PK = USER#\&lt;userId\&gt;,<br><br>SK begins\_with CONFIG#     |

| ---                              | ---                                                         |

| Get most recent scan results     | GSI on timestamp, sorted descending                         |

| ---                              | ---                                                         |



\- Data Flow:



Market Data API (external)



↓



Lambda - Scan Worker (fetches + evaluates symbols)



↓



DynamoDB - writes scan results + updates scan job status



↓



Lambda - Results handler (reads from DynamoDB on request)



↓



API Gateway → Frontend Dashboard



\- API Design



\- Authentication

&#x20; - All API requests must include a valid JWT token in the Authorization header, issued by Amazon Cognito upon successful user login.

&#x20; - Authorization: Bearer \&lt;cognito\_jwt\_token\&gt;

\- Base URL

&#x20; - Where stage is either dev or prod depending on the deployment environment.

&#x20; - https://\&lt;api-gateway-id\&gt;.execute-api.\&lt;region\&gt;.\[amazonaws.com/](http://amazonaws.com/)\&lt;stage\&gt;

\- Endpoints

&#x20; - \*\*Trigger a Manual Scan\*\*:

&#x20; - Triggers an on-demand stock scan using the provided filter criteria. Creates a new scan job and returns the job ID. Results are written to DynamoDB asynchronously.

&#x20; - POST /scans

&#x20; - JSON ex:

&#x20;   - Request Body:



{



"filters": {



"minGapPercent": 2.5,



"minVolume": 1000000,



"maxFloat": 50000000,



"minRVOL": 2.0



}



}



\- - - Response:



{



"jobId": "abc123",



"status": "pending",



"startTime": "2024-03-15T09:30:00Z"



}



\- - \*\*Get Recent Scan Jobs\*\*:

&#x20;   - Returns a list of recent scan job records for the authenticated user, sorted by most recent first.

&#x20;   - GET /scans

&#x20;   - JSON ex:

&#x20;     - Response:



{



"jobs": \\\[



{



"jobId": "abc123",



"status": "complete",



"triggeredBy": "user",



"startTime": "2024-03-15T09:30:00Z",



"endTime": "2024-03-15T09:30:04Z",



"resultCount": 12



}



\\]



}



\- - \*\*Get Results for a specific scan\*\*:

&#x20;   - Returns all stock symbols that matched the filters for a given scan job.

&#x20;   - Path Parameter:



| Parameter | Type   | Description                       |

| --------- | ------ | --------------------------------- |

| scanID    | String | The ID of the scan job to retrive |

| ---       | ---    | ---                               |



\- - GET /scans/{scanId} - JSON ex:



Response:



{



"scanId": "abc123",



"timestamp": "2024-03-15T09:30:00Z",



"results": \\\[



{



"ticker": "TSLA",



"price": 185.42,



"volume": 4200000,



"rvol": 3.2,



"float": 3180000000,



"gapPercent": 4.1



}



\\]



}



\- - \*\*Get latest scan results:\*\*

&#x20;   - Returns the results of the most recently completed scan. Uses the DynamoDB GSI on timestamp to retrieve the latest record.

&#x20;   - GET /scans/latest

&#x20;     - JSON ex:



Response:



{



"scanId": "abc123",



"timestamp": "2024-03-15T09:30:00Z",



"results": \\\[...\\]



}



\- - Save a user scan configuration:

&#x20;   - Saves a named scan filter preset for the authenticated user.

&#x20;   - POST /configs

&#x20;     - JSON ex:



Request body:



{



"configName": "Morning Gapper Setup",



"filters": {



"minGapPercent": 3.0,



"minVolume": 500000,



"maxFloat": 20000000,



"minRVOL": 1.5



}



}



Response:



{



"configId": "cfg456",



"configName": "Morning Gapper Setup",



"createdAt": "2024-03-15T08:00:00Z"



}



\- - \*\*Get all saved configurations:\*\*

&#x20;   - Returns all saved scan configurations for the authenticated user.

&#x20;   - GET /configs

&#x20;     - JSON ex:



Response:



{



"configs": \\\[



{



"configId": "cfg456",



"configName": "Morning Gapper Setup", "filters": {



"minGapPercent": 3.0,



"minVolume": 500000,



"maxFloat": 20000000,



"minRVOL": 1.5



},



"createdAt": "2024-03-15T08:00:00Z",



"lastRunAt": "2024-03-15T09:30:00Z"



}



\\]



}



\- - \*\*Delete a saved configuration:\*\*

&#x20;   - Deletes a saved scan configuration by ID.

&#x20;   - DELETE /configs/{configId}

&#x20;   - Path Parameter



| Parameter | Type   | Description                           |

| --------- | ------ | ------------------------------------- |

| configID  | string | The ID of the configuration to delete |

| ---       | ---    | ---                                   |



\- - - JSON ex:



Response:



{



"message": "Configuration deleted successfully." }



\- - \*\*Error Handling:\*\*

&#x20;   - All endpoints return a consistent error response format:

&#x20;     - JSON ex:



{



"error": {



"code": "ERROR\_CODE",



"message": "Human readable description of what went wrong."



}



}



\- - - Standard Error Codes:



| HTTP Status | Code           | Meaning                                         |

| ----------- | -------------- | ----------------------------------------------- |

| 400         | BAD\_REQUEST    | Missing or invalid request parameters           |

| ---         | ---            | ---                                             |

| 401         | UNAUTHORIZED   | Missing or invalid Cognito JWT token            |

| ---         | ---            | ---                                             |

| 403         | FORBIDDEN      | User does not have permission for this resource |

| ---         | ---            | ---                                             |

| 404         | NOT\_FOUND      | The requested scan or config does not exist     |

| ---         | ---            | ---                                             |

| 500         | INTERNAL\_ERROR | Unexpected server error - logged to CloudWatch  |

| ---         | ---            | ---                                             |



\- System Flow



\- Scheduled Scan Flow - This flow runs automatically on a defined schedule using EventBridge. No user action is required:



\- EventBridge triggers Lambda Scan Orchestrator on a cron schedule (e.g. weekdays at 9:30 AM EST - market open)

\- Scan Orchestrator reads default scan criteria and generates a list of stock symbols to evaluate

\- Orchestrator creates a new Scan Job record in DynamoDB with status = "pending"

\- Orchestrator fans out - invokes multiple Lambda Scanner Worker functions in parallel, each responsible for a batch of symbols

\- Each Scanner Worker:



a. Fetches market data from the external Market Data API



b. Evaluates each symbol against the filter criteria (gap %, volume, RVOL, float)



c. Writes matching symbols as Scan Result records to DynamoDB



\- Once all workers complete, Scan Job status is updated to "complete" with an endTime and resultCount

\- Results are now available for retrieval via the API



\- Manual Scan Flow - This flow is triggered by an authenticated user from the frontend dashboard:



\- User submits scan criteria from the frontend dashboard

\- Frontend sends POST /scans request to API Gateway with filter parameters in the request body

\- API Gateway validates the Cognito JWT token

\- If token is invalid - request is rejected with 401 Unauthorized If token is valid - request is forwarded to Lambda

\- Lambda Scan Orchestrator receives the request, creates a new Scan Job record in DynamoDB with status = "pending", and returns 202 Accepted with the jobId to the frontend

\- Orchestrator fans out - invokes Lambda Scanner Worker functions in parallel for each batch of symbols

\- Each Scanner Worker:



a. Fetches market data from the external Market Data API



b. Evaluates each symbol against the submitted filter criteria



c. Writes matching symbols as Scan Result records to DynamoDB



\- Scan Job status is updated to "complete"

\- Frontend polls GET /scans/{scanId} until status = "complete" then displays results to the user



\- Results Retrieval flow - This flow is triggered when a user requests to view scan results from the dashboard:



\- User opens the dashboard or requests a specific scan

\- Frontend sends GET /scans/latest or GET /scans/{scanId} to API Gateway with a valid Cognito JWT token

\- API Gateway validates the token and forwards the request to the Results Lambda function

\- Results Lambda queries DynamoDB:



\\- For latest results: queries GSI on timestamp descending



\\- For specific scan: queries PK = SCAN#\&lt;scanId\&gt;



\- DynamoDB returns matching records

\- Lambda formats the response and returns it to API Gateway

\- API Gateway returns the response to the frontend

\- Frontend renders the list of matching stock symbols and their data to the user



\- Authentication flow - This flow describes how a user logs in and obtains access to the API:



\- User enters credentials on the frontend login screen

\- Frontend sends credentials to Amazon Cognito

\- Cognito validates the credentials against the user pool

\- If invalid - Cognito returns an authentication error



If valid - Cognito issues a JWT access token



\- Frontend stores the JWT token and includes it in the Authorization header of every subsequent API request

\- API Gateway validates the token on each request before allowing it to reach Lambda

\- Token expires after a defined period - user is prompted to log in again



\- Error Flow - This flow describes what happens when something goes wrong during a scan.



\- A Scanner Worker Lambda encounters an error



(e.g. market data API is unavailable, timeout, bad response)



\- Lambda logs the full error details to CloudWatch

\- The failed invocation is retried automatically up to the configured retry limit

\- If all retries fail:



\\- The Scan Job status is updated to "failed" in DynamoDB



\\- The error is logged to CloudWatch with the jobId for debugging



\- The frontend receives a failed status on the next poll and displays an appropriate error message to the user



8\\. Scalability \& Performance



\- AWS Lambda:



Lambda scales automatically by creating new function instances in response to incoming requests. Each invocation runs in its own isolated environment. There is no server to provision or manage.



\- - Concurrent executions scale up automatically as demand increases

&#x20;   - The Scan Orchestrator fans out work to multiple Scanner Worker functions running in parallel, allowing the system to process large symbol lists significantly faster than sequential processing

&#x20;   - Lambda scales back down to zero when there are no invocations, meaning there is no cost during idle periods such as nights, weekends, and market holidays

\- API Gateway:



API Gateway scales automatically with no configuration required. It handles thousands of concurrent requests without any manual scaling intervention.



\- - Throttling limits are configured to protect downstream Lambda functions from being overwhelmed

&#x20;   - Request and response caching can be enabled at the API Gateway level for frequently requested data such as the latest scan results, reducing Lambda invocations and latency

\- Amazon DynamoDB



DynamoDB is a fully serverless database that scales horizontally without downtime.



\- - On-demand capacity mode is used so the table scales read and write throughput automatically based on actual traffic

&#x20;   - No capacity planning is required - DynamoDB handles traffic spikes such as market open surges without intervention

&#x20;   - The single-table design minimizes the number of read and write operations required per scan result

&#x20;   - TTL is used to automatically expire old scan results, keeping the table lean and read performance consistent over time

\- Amazon EventBridge



EventBridge is fully managed and has no scaling considerations. It reliably triggers Lambda on the configured schedule regardless of system load.



\- S3 and CloudFront



The frontend dashboard is served as a static site from S3 via CloudFront.



\- - CloudFront caches assets at edge locations globally, meaning frontend load times are not affected by backend load

&#x20;   - S3 static hosting scales automatically with no configuration required

&#x20;   - Frontend performance is entirely decoupled from backend scan performance

\- Cold Starts



A cold start occurs when Lambda has not been invoked recently and AWS needs to initialize a new execution environment before running the function. This adds latency to the first invocation after an idle period.



Impact on ProfitX\*\*:\*\*



\- - Scheduled scans trigger at market open after a period of inactivity overnight, making them susceptible to cold starts

&#x20;   - API-facing Lambda functions may experience cold starts if a user is the first to make a request after an idle period



Mitigation strategies:



\- - Keep Lambda deployment packages small to reduce initialization time

&#x20;   - Avoid heavy imports and expensive operations outside the handler function

&#x20;   - Use provisioned concurrency on API-facing Lambda functions if cold start latency becomes a measurable problem in production

&#x20;   - Scheduled scans have a wider acceptable completion window, making cold starts less critical for that flow

\- Scalability Limits and Considerations:



| Consideration                  | Detail                                                                                                                                                              |

| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| Lambda concurrency limit       | AWS accounts have a default concurrent execution limit of 1,000 per region. This is sufficient for ProfitX at current scale but should be monitored as usage grows. |

| ---                            | ---                                                                                                                                                                 |

| DynamoDB on-demand limits      | On-demand mode handles sudden traffic spikes well but has a default throughput limit that can be raised via AWS support if needed.                                  |

| ---                            | ---                                                                                                                                                                 |

| Market data API rate limits    | The external data provider enforces rate limits per API key. Batch sizes and worker counts must be tuned to stay within those limits.                               |

| ---                            | ---                                                                                                                                                                 |

| EventBridge schedule precision | EventBridge cron schedules are accurate to the minute. Sub-minute scheduling is not supported and is not required for ProfitX.                                      |

| ---                            | ---                                                                                                                                                                 |



9\\. Security



\- Authentication \& Authorization



Amazon cognito - All user authentication is handled by Amazon Cognito. ProfitX does not implement a custom authentication system.



\- Users authenticate through the Cognito User Pool and receive a JWT access token upon successful login

\- The JWT token expires after a defined period, after which the user must reauthenticate

\- Cognito handles password hashing, token signing, token expiry, and brute force protection natively

\- User identity and credentials are never stored in DynamoDB or Lambda



API Gateway Authorization - Every API endpoint is protected by a Cognito Authorizer attached to API Gateway.



\- API Gateway validates the JWT token on every inbound request before it reaches Lambda

\- Requests with missing, expired, or tampered tokens are rejected with 401 Unauthorized at the gateway level

\- Lambda functions never receive unauthenticated requests and do not perform authentication logic themselves

\- This ensures that no compute cost is incurred from unauthenticated or malicious requests



IAM Least Privilege - Every AWS service interaction is governed by IAM roles and policies. ProfitX follows the principle of least privilege - every component is granted only the permissions it needs and nothing more.



\- Lambda IAM Roles - Each Lambda function has its own dedicated IAM role. No two functions share a role.

&#x20; - No Lambda function has administrator access

&#x20; - No Lambda function has permissions to IAM, S3 buckets outside its scope, or any service it does not directly interact with

&#x20; - IAM policies are defined in Terraform and version controlled in GitHub



| Lambda Function   | Permissions Granted                                         |

| ----------------- | ----------------------------------------------------------- |

| Scan Orchestrator | Invoke Lambda, Write to DynamoDB, Read from Secrets Manager |

| ---               | ---                                                         |

| Scanner Worker    | Read from Secrets Manager, Write to DynamoDB                |

| ---               | ---                                                         |

| Results Handler   | Read from DynamoDB                                          |

| ---               | ---                                                         |

| Config Handler    | Read and Write to DynamoDB                                  |

| ---               | ---                                                         |



\- Why separate roles?

&#x20; - If a single Lambda function is compromised, the blast radius is limited to only the permissions granted to that specific role. A compromised Scanner Worker cannot read user configurations or invoke other Lambda functions because it does not have those permissions.



Secrets Management - No secrets, API keys, or credentials are ever hardcoded in code or stored in environment variables in plain text.



\- The market data provider API key is stored in AWS Secrets Manager

\- Lambda functions retrieve the secret at runtime using the Secrets Manager SDK

\- Secrets Manager automatically encrypts stored secrets using AWS KMS

\- Access to Secrets Manager is controlled by IAM - only the Lambda functions that need the API key have permission to retrieve it

\- Secret values never appear in CloudWatch logs, GitHub repositories, or DynamoDB records



Infrastructure Security



\- No hardcoded credentials in Terraform

&#x20; - All Terraform configuration files are stored in GitHub. No secrets, account IDs, or sensitive values are hardcoded in Terraform files. Sensitive values are passed in at deploy time via environment variables or retrieved from Secrets Manager.

\- S3 Bucket Security - The S3 bucket used for frontend hosting is configured as follows:

&#x20; - Public access is blocked at the bucket level except for the specific CloudFront distribution serving the frontend

&#x20; - Direct S3 URL access is disabled - all traffic must go through CloudFront

&#x20; - Bucket versioning is enabled to allow recovery from accidental overwrites

\- CloudFront Security

&#x20; - HTTPS is enforced on all CloudFront distributions - HTTP requests are redirected to HTTPS

&#x20; - The frontend is never served over an unencrypted connection

\- DynamoDB Security

&#x20; - All data stored in DynamoDB is encrypted at rest using AWS-managed KMS keys by default

&#x20; - DynamoDB is not publicly accessible - it is only accessible by Lambda functions with the appropriate IAM role

&#x20; - There is no direct database connection string - all access goes through the AWS SDK with IAM authentication



Logging and Auditability



\- All Lambda function invocations, errors, and outputs are logged to Amazon CloudWatch Logs automatically

\- CloudWatch logs provide a full audit trail of every scan execution, API request, and system error

\- No sensitive data such as JWT tokens, API keys, or user credentials is written to CloudWatch logs

\- Log retention policies are configured to control storage cost while maintaining an adequate audit window



CI/CD Pipeline Security



\- GitHub Actions is used for all deployments - no manual console deployments are permitted

\- AWS credentials used by GitHub Actions are stored as GitHub Secrets and are never exposed in pipeline logs

\- Terraform plans are reviewed before apply to prevent unintended infrastructure changes

\- Branch protection rules are enforced on the main branch to prevent direct pushes without review



Threat Model Summary



| Threat                                  | Mitigation                                                 |

| --------------------------------------- | ---------------------------------------------------------- |

| Unauthenticated API access              | Cognito JWT validation enforced at API Gateway             |

| ---                                     | ---                                                        |

| Stolen API key for market data provider | Key stored in Secrets Manager, never in code               |

| ---                                     | ---                                                        |

| Overprivileged Lambda function          | Separate least-privilege IAM role per function             |

| ---                                     | ---                                                        |

| Hardcoded secrets in GitHub             | No secrets in code - enforced by standards and Terraform   |

| ---                                     | ---                                                        |

| Direct database access                  | DynamoDB only accessible via IAM-authenticated Lambda      |

| ---                                     | ---                                                        |

| Unencrypted data at rest                | DynamoDB and S3 encrypted by default with KMS              |

| ---                                     | ---                                                        |

| Unencrypted data in transit             | HTTPS enforced on all CloudFront and API Gateway endpoints |

| ---                                     | ---                                                        |

| Accidental infrastructure change        | All infra defined in Terraform, reviewed before deploy     |

| ---                                     | ---                                                        |



10\\. Trade Offs



| Decision                  | Chosen                     | Alternative considered       | Why Chosen                                                                                    | What was accepted                                                    |

| ------------------------- | -------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |

| Compute                   | AWS Lambda (serverless)    | EC2 / traditional server     | Zero idle cost, auto-scaling, no server management                                            | Cold starts on first invocation after idle period                    |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Database                  | Amazon DynamoDB            | Amazon RDS PostgreSQL        | Fully serverless, no idle instance cost, scales automatically, fits key-based access patterns | Access patterns must be defined upfront - no flexible ad hoc queries |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Table design              | Single-table DynamoDB      | Multi-table DynamoDB         | Fewer read operations, lower cost, better performance for related data                        | Higher upfront design complexity                                     |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Scan execution            | Asynchronous with polling  | Synchronous request-response | Eliminates API Gateway 29 second timeout risk, enables Lambda fan-out and parallel execution  | Frontend must implement polling logic - results are not instant      |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| API style                 | REST via API Gateway       | GraphQL                      | Simple, well understood, natively supported by API Gateway, no additional tooling required    | Fixed response shapes - may return more data than strictly needed    |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Infrastructure deployment | Terraform (IaC)            | AWS Console                  | Repeatable, version controlled, dev and prod parity, full audit trail in GitHub               | Steeper learning curve, slower for small one-off changes             |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Authentication            | Amazon Cognito             | Custom auth system           | Fully managed, handles token signing, expiry, and brute force protection natively             | Less control over custom auth flows                                  |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Secret storage            | AWS Secrets Manager        | Environment variables        | Secrets encrypted at rest, access controlled by IAM, never exposed in code or logs            | Small additional latency on Lambda cold start to retrieve secret     |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| Frontend hosting          | S3 + CloudFront            | EC2 hosted frontend          | Zero server cost, global CDN, scales automatically, fully decoupled from backend              | Limited to static assets - no server side rendering                  |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

| CI/CD                     | GitHub Actions + Terraform | Manual deployments           | Automated, repeatable, no console-click deployments, changes reviewed before apply            | Requires pipeline configuration and maintenance                      |

| ---                       | ---                        | ---                          | ---                                                                                           | ---                                                                  |

