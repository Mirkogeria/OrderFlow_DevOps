#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-dev}
AWS_REGION="eu-central-1"
AWS_PROFILE="lab"
PROJECT_NAME="orderflow"

# Cleanup function
cleanup() {
  echo -e "${YELLOW}Cleaning up environment: ${ENVIRONMENT}...${NC}"
  
  # Remove Helm releases
  echo "  → Removing Helm releases..."
  helm uninstall order-service -n orderflow 2>/dev/null || true
  helm uninstall inventory-service -n orderflow 2>/dev/null || true
  helm uninstall notification-service -n orderflow 2>/dev/null || true
  helm uninstall ingestion-service -n orderflow 2>/dev/null || true
  helm uninstall genai-service -n orderflow 2>/dev/null || true
  helm uninstall prometheus -n monitoring 2>/dev/null || true
  helm uninstall qdrant -n orderflow 2>/dev/null || true
  
  # Remove namespaces
  echo "  → Removing namespaces..."
  kubectl delete namespace orderflow 2>/dev/null || true
  kubectl delete namespace monitoring 2>/dev/null || true
  
  # Destroy Terraform
  echo "  → Destroying Terraform infrastructure..."
  cd terraform/environments/${ENVIRONMENT}
  terraform destroy -auto-approve
  cd ../../..
  
  echo -e "${GREEN}✓ Cleanup complete${NC}"
  exit 0
}

# Deploy function
deploy() {
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}OrderFlow DevOps — Automated Deployment${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
  echo -e "Region: ${YELLOW}${AWS_REGION}${NC}"
  echo ""

  # 1. Validate prerequisites
  echo -e "${YELLOW}[1/7] Validating prerequisites...${NC}"
  command -v terraform >/dev/null 2>&1 || { echo -e "${RED}terraform not found${NC}"; exit 1; }
  command -v helm >/dev/null 2>&1 || { echo -e "${RED}helm not found${NC}"; exit 1; }
  command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl not found${NC}"; exit 1; }
  command -v aws >/dev/null 2>&1 || { echo -e "${RED}aws-cli not found${NC}"; exit 1; }
  echo -e "${GREEN}✓ All prerequisites found${NC}\n"

  # 2. Get DB password
  echo -e "${YELLOW}[2/7] Requesting database password...${NC}"
  read -sp "Enter RDS password (min 8 chars): " DB_PASSWORD
  echo ""
  if [ ${#DB_PASSWORD} -lt 8 ]; then
    echo -e "${RED}Password must be at least 8 characters${NC}"
    exit 1
  fi
  export TF_VAR_db_password="$DB_PASSWORD"
  echo -e "${GREEN}✓ Password set${NC}\n"

  # 3. Deploy infrastructure with Terraform
  echo -e "${YELLOW}[3/7] Deploying infrastructure with Terraform...${NC}"
  cd terraform/environments/${ENVIRONMENT}
  terraform init
  terraform validate
  terraform plan -out=tfplan
  terraform apply tfplan
  TF_OUTPUTS=$(terraform output -json)
  echo -e "${GREEN}✓ Infrastructure deployed${NC}\n"

  # Extract outputs
  EKS_CLUSTER_NAME=$(echo $TF_OUTPUTS | jq -r '.eks_cluster_name.value')
  RDS_HOST=$(echo $TF_OUTPUTS | jq -r '.rds_endpoint.value' | cut -d: -f1)
  S3_BUCKET=$(echo $TF_OUTPUTS | jq -r '.s3_documents_bucket.value')
  INGESTION_ROLE=$(echo $TF_OUTPUTS | jq -r '.ingestion_irsa_role_arn.value')
  GENAI_ROLE=$(echo $TF_OUTPUTS | jq -r '.genai_irsa_role_arn.value')
  ECR_REGISTRY=$(echo $TF_OUTPUTS | jq -r '.ecr_repositories.value | to_entries[0].value' | cut -d/ -f1)

  cd ../../..

  # 4. Configure kubectl
  echo -e "${YELLOW}[4/7] Configuring kubectl...${NC}"
  aws eks update-kubeconfig \
    --region ${AWS_REGION} \
    --name ${EKS_CLUSTER_NAME} \
    --profile ${AWS_PROFILE}
  kubectl cluster-info
  echo -e "${GREEN}✓ kubectl configured${NC}\n"

  # 5. Deploy namespaces and monitoring
  echo -e "${YELLOW}[5/7] Deploying namespaces and monitoring...${NC}"
  kubectl apply -f k8s/namespaces/${ENVIRONMENT}.yaml

  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    -f k8s/monitoring/prometheus-values.yaml \
    -n monitoring \
    --create-namespace \
    --wait

  helm repo add qdrant https://qdrant.github.io/qdrant-helm
  helm repo update
  helm upgrade --install qdrant qdrant/qdrant \
    -f k8s/qdrant/qdrant-values.yaml \
    -n orderflow \
    --wait

  echo -e "${GREEN}✓ Monitoring and Qdrant deployed${NC}\n"

  # 6. Create secrets
  echo -e "${YELLOW}[6/7] Creating Kubernetes secrets...${NC}"
  kubectl create secret generic orderflow-secrets \
    -n orderflow \
    --from-literal=db_host=${RDS_HOST} \
    --from-literal=db_password=${DB_PASSWORD} \
    --from-literal=qdrant_host=qdrant.orderflow.svc.cluster.local \
    --dry-run=client -o yaml | kubectl apply -f -

  echo -e "${GREEN}✓ Secrets created${NC}\n"

  # 7. Deploy microservices with Helm
  echo -e "${YELLOW}[7/7] Deploying microservices with Helm...${NC}"

  SERVICES=("order-service" "inventory-service" "notification-service")
  for service in "${SERVICES[@]}"; do
    echo "  → Deploying ${service}..."
    helm upgrade --install ${service} ./helm/${service} \
      -f ./helm/${service}/values-${ENVIRONMENT}.yaml \
      -n orderflow \
      --set image.repository=${ECR_REGISTRY}/orderflow/${service} \
      --wait
  done

  echo "  → Deploying ingestion-service..."
  helm upgrade --install ingestion-service ./helm/ingestion-service \
    -f ./helm/ingestion-service/values-${ENVIRONMENT}.yaml \
    -n orderflow \
    --set image.repository=${ECR_REGISTRY}/orderflow/ingestion-service \
    --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=${INGESTION_ROLE} \
    --wait

  echo "  → Deploying genai-service..."
  helm upgrade --install genai-service ./helm/genai-service \
    -f ./helm/genai-service/values-${ENVIRONMENT}.yaml \
    -n orderflow \
    --set image.repository=${ECR_REGISTRY}/orderflow/genai-service \
    --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=${GENAI_ROLE} \
    --wait

  echo -e "${GREEN}✓ All microservices deployed${NC}\n"

  # Summary
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}Deployment Complete!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo -e "Cluster: ${YELLOW}${EKS_CLUSTER_NAME}${NC}"
  echo -e "Region: ${YELLOW}${AWS_REGION}${NC}"
  echo -e "RDS Host: ${YELLOW}${RDS_HOST}${NC}"
  echo -e "S3 Bucket: ${YELLOW}${S3_BUCKET}${NC}"
  echo -e "ECR Registry: ${YELLOW}${ECR_REGISTRY}${NC}"
  echo ""
  echo -e "${YELLOW}Useful commands:${NC}"
  echo "  Check pods:     kubectl get pods -n orderflow"
  echo "  View logs:      kubectl logs -n orderflow -l app=order-service -f"
  echo "  Port-forward:   kubectl port-forward -n orderflow svc/order-service 8000:80"
  echo "  Grafana:        kubectl port-forward -n monitoring svc/grafana 3000:3000"
  echo "  Cleanup:        bash deploy.sh cleanup ${ENVIRONMENT}"
  echo ""
}

# Main logic
if [ "$ENVIRONMENT" = "cleanup" ]; then
  ENVIRONMENT=${2:-dev}
  cleanup
else
  deploy
fi