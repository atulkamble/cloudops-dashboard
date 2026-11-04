# CloudOps Workspace

A responsive cloud operations dashboard with an interactive task list, health check, Flask API, and persistent SQLite storage. Runs locally with Docker Compose and includes AWS CloudFormation and GitHub Actions files for an ECS Fargate deployment.

## Architecture

- **Frontend:** Nginx serves the responsive dashboard and proxies `/api/*` requests to the backend.
- **Backend:** Flask + Gunicorn exposes health and task endpoints.
- **Data:** SQLite is persisted in a named Docker volume locally. On ECS the demo uses task ephemeral storage.
- **AWS:** CloudFormation creates a VPC, public subnets, ECR repositories, ECS Fargate service, CloudWatch logs, and an application load balancer.

## Run locally

```bash
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). Stop with `Ctrl+C`; remove containers with `docker compose down`. To also remove saved tasks, run `docker compose down -v`.

Useful endpoints: `GET /api/health`, `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/{id}`, `DELETE /api/tasks/{id}`.

## Deploy to ECS

1. Create an AWS IAM role for GitHub Actions using GitHub OIDC. Restrict its trust policy to your GitHub owner/repository and `refs/heads/main`. Grant only the permissions needed to push to the two ECR repos and update/describe the ECS service.
2. Configure repository variable `AWS_REGION` and secret `AWS_DEPLOY_ROLE_ARN` in GitHub.
3. In the AWS account and region you selected, create the infrastructure stack:

   ```bash
   aws cloudformation deploy \\
     --template-file infra/ecs.yml \\
     --stack-name cloudops-dashboard \\
     --capabilities CAPABILITY_IAM \\
     --parameter-overrides ProjectName=cloudops-dashboard
   ```

4. Push this project to the repository's `main` branch. The workflow builds and pushes both images to ECR and forces a new ECS deployment.
5. Find the public URL with:

   ```bash
   aws cloudformation describe-stacks --stack-name cloudops-dashboard \\
     --query "Stacks[0].Outputs[?OutputKey=='DashboardUrl'].OutputValue" --output text
   ```

The sample ECS service uses a single Fargate task and ephemeral storage. For durable multi-task production use, replace SQLite with RDS/Aurora or DynamoDB, put tasks in private subnets behind the ALB, configure HTTPS with ACM, and add autoscaling/backups. The demo ALB currently serves HTTP.
