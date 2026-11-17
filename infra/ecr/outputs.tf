# infra/ecr/outputs.tf
output "repository_urls" {
  description = "URL de cada repositorio (sin etiqueta), por componente"
  value       = { for nombre, repo in aws_ecr_repository.app : nombre => repo.repository_url }
}
