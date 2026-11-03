# Cost Breakdown

**Status: estimates.** After a week or two of running, replace the "Estimated" column with real numbers from Billing > Cost Explorer (group by service).

## Assumptions

- 1 scheduled scan per weekday (about 22 per month) plus about 100 manual scans per month
- 40 symbols per scan, roughly 10 matches per scan
- 1 to 5 users
- us-east-1, one environment running (dev + prod together roughly doubles the fixed items)

## Monthly estimate (per environment)

| Service | Usage | Estimated cost | Notes |
|---|---|---|---|
| Lambda | ~120 invocations, ~2 s each, 256 MB | $0.00 | Well under the always-free 1M requests and 400k GB-seconds |
| API Gateway (HTTP API) | ~500 requests | ~$0.00 | $1 per million requests after free usage |
| DynamoDB (on-demand) | ~1,500 writes, ~500 reads, < 1 MB | ~$0.00 | Pay per request; storage far below 25 GB free |
| Cognito | 1 to 5 users | $0.00 | Free for first 10,000 monthly active users |
| S3 + CloudFront | 2 tiny files, a few hundred requests | $0.00 | Within CloudFront's always-free allowance |
| EventBridge Scheduler | ~22 invocations | $0.00 | 14M invocations/month free |
| CloudWatch | A few MB of logs, 3 alarms | ~$0.00 to $0.30 | Alarms beyond the free 10 cost about $0.10 each. Logs expire after 14 days |
| Secrets Manager | 1 secret | **$0.40** | The main fixed cost. No always-free tier |
| AWS Budgets | 1 budget | $0.00 | First 2 budgets are free |
| **Total** | | **about $0.50 to $1.00** | About $1 to $2 with dev and prod both deployed |

## What changes at scale

| Users / scans | What grows | Rough effect |
|---|---|---|
| 100 users, 1,000 scans/month | Lambda, API Gateway, DynamoDB requests | Still a few dollars; likely still inside free tiers for Lambda |
| 10,000 users | API Gateway, DynamoDB reads, CloudFront | Tens of dollars. Add caching of `/scans/latest`, since it changes at most a few times a day |
| Large symbol list (1,000+) | Scan duration | Move to async fan-out (orchestrator + parallel workers). Lambda cost stays small; the market data API plan becomes the real cost |

## Cost controls in place

- On-demand DynamoDB and Lambda mean nothing is billed while idle
- Log retention is 14 days
- API Gateway throttling (10 req/s, burst 20) limits runaway usage
- DynamoDB TTL deletes scan data after 30 days
- AWS Budget alert at 80% of $5/month (set `alert_email` in the tfvars)
- Deliberately avoided: NAT Gateway, WAF, provisioned concurrency, customer-managed KMS keys, RDS

## Not in the AWS bill

The market data API (the mock provider is free; a real plan is the main real-world cost) and the optional custom domain (about $12/year).
