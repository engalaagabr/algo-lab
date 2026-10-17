# GitHub Actions to Azure CI/CD

The workflow in `.github/workflows/ci-cd.yml` checks pull requests targeting `dev` or `main`. On every push to `main` (including a pull request merge), it runs the same checks, builds versioned API and frontend container images, pushes them to Azure Container Registry (ACR), and updates the existing Azure Container Apps. Images are tagged with the full Git commit SHA so each deployment can be traced to its source commit.

The workflow deploys application code to existing Azure resources. It does not create or change infrastructure. The Azure Container Apps and registry must be provisioned once using the manual infrastructure guide before the first deployment.

## One-time Azure setup

Use Microsoft Entra workload identity federation (OIDC). This lets GitHub Actions request short-lived Azure tokens without storing a client secret. Create a dedicated Microsoft Entra application/service principal for GitHub Actions, then add a federated credential with:

- Organization: `engalaagabr`
- Repository: `AlgoLab`
- Entity type: Branch
- Branch: `main`
- Audience: `api://AzureADTokenExchange`

The resulting subject must be exactly `repo:engalaagabr/AlgoLab:ref:refs/heads/main`. The repository is public, so keep the federated subject restricted to this repository and branch. Do not add `id-token: write` to the checks job.

Grant the service principal only these roles:

- `AcrPush` on the ACR resource.
- `Container Apps Contributor` on each of the API and web Container App resources.

Do not grant subscription-wide `Contributor` or `Owner` for this pipeline. The current scaffold resource names are `cralgolabdevcdbf`, `ca-algolab-api-dev-cdbf`, `ca-algolab-web-dev-cdbf`, and `rg-algolab-dev-cdbf`; use the actual names if the resources were provisioned with different values. Azure role assignment changes may take a few minutes to propagate.

## One-time GitHub setup

In the repository, open **Settings → Secrets and variables → Actions**.

Add these repository secrets:

| Secret | Value |
| --- | --- |
| `AZURE_CLIENT_ID` | Client/application ID of the Entra identity configured above |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Subscription containing the ACR and Container Apps |

Add these repository variables:

| Variable | Current scaffold value |
| --- | --- |
| `AZURE_ACR_NAME` | `cralgolabdevcdbf` |
| `AZURE_RESOURCE_GROUP` | `rg-algolab-dev-cdbf` |
| `AZURE_API_CONTAINER_APP` | `ca-algolab-api-dev-cdbf` |
| `AZURE_WEB_CONTAINER_APP` | `ca-algolab-web-dev-cdbf` |

Use the same target environment consistently. The values above point at the currently planned demo resources; changing them does not provision a separate production environment.

## Require CI before merging

In **Settings → Rules → Rulesets**, create or update a branch ruleset for `main` and require the **Test and build** check before merging. This keeps a failed test/build from being merged and prevents the deploy job from running. Apply an equivalent rule to `dev` if you also want every PR there to pass CI first.

## Run and verify

1. Provision the Azure resources and deploy the initial working images using [the manual Azure guide](../infra/DEPLOY-MANUALLY.md).
2. Push this workflow and documentation to GitHub.
3. Confirm the GitHub repository settings and Azure federated credential match the values above.
4. Merge a tested pull request into `main`. The **CI/CD** workflow runs backend lint/tests and frontend type-check/lint/tests/build before it can deploy.
5. In GitHub, open **Actions → CI/CD** and confirm the `Test and build` and `Deploy to Azure Container Apps` jobs pass. Then open the web app URL and check `/health` and `/api/v1/algorithms`.

If a deployment fails, the old Container Apps revision remains available according to the app's revision mode. Check the Actions log, ACR image tags, and Container Apps revisions before retrying. Each successful commit remains addressable by its SHA image tag.

## Trigger summary

| Event | Checks | Azure deployment |
| --- | --- | --- |
| Pull request to `dev` or `main` | Yes | No |
| Push/merge to `main` | Yes | Yes, after checks pass |
| Push to other branches | No | No |
