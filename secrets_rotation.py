#!/usr/bin/env python3
"""
secrets_rotation.py
Rotates AWS Secrets Manager secrets and updates Kubernetes secrets automatically.
Usage: python secrets_rotation.py --secret-name my/db/password --namespace production
"""

import argparse
import base64
import json
import secrets
import string
import subprocess
import boto3
from datetime import datetime


def generate_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def rotate_secret(secret_name: str) -> str:
    """Rotate secret in AWS Secrets Manager and return new value."""
    client = boto3.client("secretsmanager")

    current = json.loads(client.get_secret_value(SecretId=secret_name)["SecretString"])

    new_password = generate_password()
    current["password"] = new_password
    current["rotated_at"] = datetime.utcnow().isoformat()

    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(current)
    )
    print(f"✅ Rotated secret: {secret_name}")
    return new_password


def update_k8s_secret(secret_name: str, namespace: str, key: str, value: str):
    """Patch Kubernetes secret with new value."""
    encoded = base64.b64encode(value.encode()).decode()
    patch = json.dumps({"data": {key: encoded}})
    result = subprocess.run(
        ["kubectl", "patch", "secret", secret_name,
         "-n", namespace, "--patch", patch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl patch failed: {result.stderr}")
    print(f"✅ Updated Kubernetes secret: {secret_name} in {namespace}")


def restart_deployment(deployment: str, namespace: str):
    """Rolling restart to pick up new secret."""
    subprocess.run(
        ["kubectl", "rollout", "restart", f"deployment/{deployment}", "-n", namespace],
        check=True
    )
    subprocess.run(
        ["kubectl", "rollout", "status", f"deployment/{deployment}",
         "-n", namespace, "--timeout=5m"],
        check=True
    )
    print(f"✅ Deployment {deployment} restarted and healthy")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-name",  required=True)
    parser.add_argument("--k8s-secret",   required=True)
    parser.add_argument("--k8s-key",      default="db-password")
    parser.add_argument("--namespace",    required=True)
    parser.add_argument("--deployment",   required=True)
    args = parser.parse_args()

    new_value = rotate_secret(args.secret_name)
    update_k8s_secret(args.k8s_secret, args.namespace, args.k8s_key, new_value)
    restart_deployment(args.deployment, args.namespace)
    print("\n✅ Secret rotation complete — zero downtime")


if __name__ == "__main__":
    main()
