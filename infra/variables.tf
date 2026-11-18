# infra/variables.tf
variable "aws_region" {
  description = "Región de AWS donde se despliegan los recursos"
  type        = string
  default     = "us-east-1"
}

variable "environment_name" {
  description = "Nombre del ambiente (staging o production)"
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment_name)
    error_message = "environment_name debe ser \"staging\" o \"production\"."
  }
}

variable "project_name" {
  description = "Prefijo de los repositorios ECR (el mismo de infra/ecr)"
  type        = string
  default     = "proyecto"
}

variable "image_tag" {
  description = "Etiqueta de las imágenes a desplegar (en el pipeline es el SHA del commit). La app la expone en /api/health"
  type        = string
}
