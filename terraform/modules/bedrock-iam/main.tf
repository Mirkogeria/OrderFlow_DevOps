resource "aws_iam_role_policy" "bedrock_invoke" {
  name   = "${var.project_name}-${var.environment}-bedrock-invoke-policy"
  role   = var.irsa_role_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/*"
      }
    ]
  })
}