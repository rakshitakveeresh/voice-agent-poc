# Container Apps (TODO)

Draft component for an internal, VNet-integrated Container Apps environment
and the Voice Agent POC app. Configure ingress, scaling, health checks,
environment variables, and managed identity here.

The image should be built and published to the planned private ACR by a future
CI/CD workflow. Do not put application secrets in Terraform state; retrieve
them from Key Vault at runtime.
