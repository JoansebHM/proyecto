# infra/ecr/backend.hcl
bucket       = "tfstate-proyecto-joansebhm"
key          = "ecr/terraform.tfstate"
region       = "us-east-1"
use_lockfile = true
