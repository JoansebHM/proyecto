# infra/backend.hcl
# Un workspace por ambiente (staging y production): cada uno guarda su propio estado en este bucket.
bucket       = "tfstate-proyecto-joansebhm"
key          = "infra/terraform.tfstate"
region       = "us-east-1"
use_lockfile = true
