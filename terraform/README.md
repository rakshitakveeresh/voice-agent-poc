# Azure infrastructure draft

**Status: TODO — planning only.** This directory documents a proposed Terraform
layout based on [`../Architecture/Voice_Agent_Architecture.drawio`](../Architecture/Voice_Agent_Architecture.drawio).
It does not contain deployable Terraform resources yet.

The proposed topology is an Azure deployment in Germany West Central:

- A virtual network with separate subnets for Container Apps infrastructure,
  the application gateway, and private endpoints.
- A private-frontend Application Gateway/WAF as the browser entry point for
  clients already connected to the private network.
- An internal, VNet-integrated Azure Container Apps environment for the Voice
  Agent POC application.
- Private connectivity only to Azure OpenAI, Azure Container Registry, Key
  Vault, and PostgreSQL Flexible Server; disable their public network access.
- Application Insights and Log Analytics for application and platform
  monitoring.
- No public IPs or internet-facing application endpoints. Users must access
  the application from the private network, such as through an existing VPN or
  ExpressRoute connection.
- n8n is external to this repository and is intentionally not provisioned.

## Planned components

| Directory | Planned responsibility |
| --- | --- |
| [`network/`](./network/README.md) | Virtual network, subnets, network security groups, private DNS zones, and links. |
| [`application-gateway/`](./application-gateway/README.md) | Private HTTPS entry point and WAF forwarding traffic to the app. |
| [`container-apps/`](./container-apps/README.md) | Internal Container Apps environment and Voice Agent POC application. |
| [`container-registry/`](./container-registry/README.md) | Private Azure Container Registry for the application image. |
| [`azure-openai/`](./azure-openai/README.md) | Azure OpenAI resource, model deployments, and private endpoint. |
| [`key-vault/`](./key-vault/README.md) | Secrets and managed-identity access policies/roles. |
| [`postgresql/`](./postgresql/README.md) | Private PostgreSQL Flexible Server and database configuration. |
| [`monitoring/`](./monitoring/README.md) | Log Analytics, Application Insights, and alerting. |

## TODO before deployment

- [ ] Confirm Azure subscription, tenant, naming rules, region availability,
  quotas, and budget. Azure OpenAI models and capacity must be checked for the
  target subscription and region.
- [ ] Choose the Terraform state backend and secure it; do not commit state,
  plan files, credentials, or populated `*.tfvars` files.
- [ ] Implement each component as a Terraform module and define its inputs and
  outputs.
- [ ] Confirm subnet sizing, NSG rules, private DNS requirements, and routing
  before creating networking.
- [ ] Decide the private DNS name and TLS certificate process for the private
  Application Gateway frontend, and how clients connect to the VNet.
- [ ] Decide the PostgreSQL SKU, version, backup/retention policy, schema
  ownership, and how the application receives its connection secret.
- [ ] Define Azure OpenAI model names, versions, deployment types, quotas, and
  the app's endpoint/authentication integration.
- [ ] Build and publish the app image to ACR; grant the Container App managed
  identity least-privilege image-pull access.
- [ ] Configure the draft [GitHub Actions workflow](../.github/workflows/terraform.yml):
  set repository variables for Azure OIDC and the pre-created remote state
  backend, configure the `azure-terraform-apply` environment with required
  reviewers, and set up Azure federated credentials/RBAC. The workflow currently
  skips Terraform actions until a root `.tf` configuration exists.
- [ ] Add pull-request plan review after deciding how to safely publish plans;
  plans can contain sensitive values and should only be available to authorized
  reviewers.
- [ ] Test deployment and teardown in a non-production subscription, including
  private connectivity and Application Gateway health probes.

## Draft workflow prerequisites

Before a plan or apply can run:

1. Add Terraform root configuration in this directory, including an
   `azurerm` backend block and pinned provider requirements.
2. Create the Azure Storage account, resource group, and blob container for
   remote state out of band. The workflow does not bootstrap its own backend.
3. Configure these GitHub repository **Actions variables**:
   `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`,
   `TF_STATE_RESOURCE_GROUP`, `TF_STATE_STORAGE_ACCOUNT`,
   `TF_STATE_CONTAINER`, and `TF_STATE_KEY`.
4. Configure Azure federated credentials and least-privilege RBAC for the
   workflow identity. The plan job on `main` uses the federated subject
   `repo:rakshitakveeresh/voice-agent-poc:ref:refs/heads/main`; the apply job
   uses `repo:rakshitakveeresh/voice-agent-poc:environment:azure-terraform-apply`.
   Grant the identity access to the state blob container and only the Azure
   resource scopes needed by the Terraform configuration.
5. Add required reviewers to the `azure-terraform-apply` environment before
   using the apply option. Environment approval is the gate before changes are
   applied.

The workflow runs formatting and validation on pull requests. After Terraform
root files are added, use **Actions → Terraform draft → Run workflow** on
`main`, selecting `plan` to create a plan or `apply` to request an approved
deployment. Apply creates a fresh plan after environment approval and applies
that exact plan. Until root `.tf` files are present, the workflow reports a
warning and skips Terraform operations.

## Cost and security notes

Application Gateway/WAF, Container Apps, Azure OpenAI, PostgreSQL, ACR, private
endpoints, and monitoring can incur ongoing charges. Estimate cost and approve
the design before provisioning. Keep every application, data, and PaaS endpoint
private-only, with no public IPs or public network access. Use managed
identities and Key Vault rather than storing credentials in Terraform
variables or GitHub files.
