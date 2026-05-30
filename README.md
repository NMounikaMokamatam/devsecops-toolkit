# devsecops-toolkit

Security patterns built into the pipeline — not bolted on afterward.

## Contents

### `secrets_rotation.py`
Rotates AWS Secrets Manager secrets and automatically patches Kubernetes secrets + triggers a rolling restart. Zero downtime.
```bash
python secrets_rotation.py \
  --secret-name prod/db/password \
  --k8s-secret app-secrets \
  --namespace production \
  --deployment my-app
```

## Pipeline Integration
Drop IaC scanning into any CI pipeline:
```yaml
# GitLab CI
scan:iac:
  image: bridgecrew/checkov:3.1.0
  script:
    - checkov -d . --config-file .checkov.yaml --output junitxml > report.xml
  artifacts:
    reports:
      junit: report.xml
```

## Security Principles
- Secrets never in code or environment variables — always AWS Secrets Manager
- IaC scanned before every deploy — hard gate, not advisory
- All containers run as non-root
- Network policies enforce least-privilege pod communication
- Automatic secret rotation with zero-downtime Kubernetes rollout
