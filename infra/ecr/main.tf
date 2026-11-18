# infra/ecr/main.tf
# Repositorios ECR donde el pipeline publica las imágenes Docker (backend y frontend).
# Se gestionan aparte de la infraestructura de cada ambiente: son compartidos por staging y production.
terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # El bucket se pasa en "terraform init -backend-config=backend.hcl"
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "lista-de-mercado"
      ManagedBy = "Terraform"
    }
  }
}

resource "aws_ecr_repository" "app" {
  for_each = toset(var.repositories)

  name = "${var.project_name}-${each.key}"

  # Mutable: la etiqueta "latest" se reemplaza en cada publicación (el SHA no cambia nunca).
  image_tag_mutability = "MUTABLE"

  # Permite destruir el repositorio aunque tenga imágenes (necesario para "terraform destroy" en el lab).
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Conserva solo las imágenes más recientes para no acumular almacenamiento.
# El rollback necesita imágenes de SHAs anteriores, por eso el límite es amplio.
resource "aws_ecr_lifecycle_policy" "app" {
  for_each = aws_ecr_repository.app

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Conservar las ${var.max_images} imágenes más recientes"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_images
        }
        action = { type = "expire" }
      }
    ]
  })
}
