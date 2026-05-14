# ============================================================
# ECR Repository — uno per ogni microservizio
# ============================================================
resource "aws_ecr_repository" "services" {
  for_each = toset(var.services)

  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.tags, {
    Name        = "${var.project_name}/${each.key}"
    Environment = var.environment
    Project     = var.project_name
    Service     = each.key
  })
}

# ============================================================
# Lifecycle policy — mantieni solo gli ultimi N image per repo
# ============================================================
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Mantieni solo le ultime ${var.image_retention_count} immagini"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.image_retention_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}