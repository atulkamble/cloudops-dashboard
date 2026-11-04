# CloudOps Workspace

A responsive cloud operations dashboard with an interactive task list, health check, Flask API, and persistent MySQL storage. Runs locally with Docker Compose and includes AWS CloudFormation and GitHub Actions files for an ECS Fargate deployment.

## Architecture

- **Frontend:** Nginx serves the responsive dashboard and proxies `/api/*` requests to the backend.
- **Backend:** Flask + Gunicorn exposes health and task endpoints.
- **Data:** MySQL is persisted in a named Docker volume locally.
- **AWS:** CloudFormation creates a VPC, public subnets, ECR repositories, ECS Fargate service, CloudWatch logs, and an application load balancer.

## Run locally

```bash
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). Stop with `Ctrl+C`; remove containers with `docker compose down`. To also remove the MySQL database and saved tasks, run `docker compose down -v`.

The Compose file supplies development-only MySQL credentials by default. Override `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD` in your environment or a local `.env` file for your setup; do not use the defaults in production.

Connect to MySQL and list tasks:

```bash
docker compose exec mysql sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
```

At the MySQL prompt:

```sql
SHOW TABLES;
SELECT id, title, done FROM tasks ORDER BY id;
```

Alternatively, run a query without opening the interactive client:

```bash
docker compose exec mysql sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT id, title, done FROM tasks ORDER BY id;"'
```

Useful endpoints: `GET /api/health`, `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/{id}`, `DELETE /api/tasks/{id}`.

## Deploy to ECS

The ECS template in `infra/ecs.yml` has not been converted to MySQL. The deployment steps below require an ECS task definition configured with a reachable external MySQL instance and credentials before they will work with this backend.

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

The sample ECS service uses a single Fargate task. For production, use a managed database such as RDS/Aurora, put tasks in private subnets behind the ALB, configure HTTPS with ACM, and add autoscaling/backups. The demo ALB currently serves HTTP.
