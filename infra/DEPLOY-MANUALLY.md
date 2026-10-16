# Manual Azure deployment

This deployment is intentionally prepared for you to run manually. It creates the resource group, registry, Log Analytics workspace, user-assigned registry pull identity, Container Apps environment, two Container Apps, and the registry `AcrPull` role assignment. The API ingress is internal; the web app has external HTTPS ingress. Both apps scale from zero to at most two replicas.

## Before deployment

1. Sign in with Azure CLI, select the intended subscription, and confirm you have permission to create a resource group and role assignments in UAE North. The subscription's Basic ACR quota could not be checked; confirm it is available before continuing.

   ```bash
   az login
   az account set --subscription a36d754c-33ac-46fe-be22-c63b93ce16e1
   ```

   Confirm the Basic Container Registry quota is available in the subscription's Azure quota view; its quota endpoint did not return data during planning.

2. Preview and deploy the infrastructure. The deployer object ID is passed as a local CLI override and is not written into the checked-in parameters file. The deployment grants the deployer `AcrPush` on this registry and grants the Container Apps identity `AcrPull`.

   ```bash
   export DEPLOYER_OBJECT_ID="$(az ad signed-in-user show --query id -o tsv)"
   az deployment sub what-if --location uaenorth --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json deployerObjectId="$DEPLOYER_OBJECT_ID"
   az deployment sub create --name algolab-phase-1 --location uaenorth \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json deployerObjectId="$DEPLOYER_OBJECT_ID"
   ```

   Phase 1 creates the Azure resources with public placeholder images; API ingress remains private.

3. Once the role assignments have propagated, build both images in ACR. Use a unique tag so later redeploys are reproducible.

   ```bash
   export IMAGE_TAG="$(git rev-parse --short HEAD)"
   az acr build --registry cralgolabdevcdbf --image "algolab-api:$IMAGE_TAG" \
     --file Dockerfile backend/
   az acr build --registry cralgolabdevcdbf --image "algolab-web:$IMAGE_TAG" \
     --file frontend/Dockerfile.azure .
   ```

4. Redeploy the same template with the real image tags. This creates revisions that pull from ACR using managed identity.

   ```bash
   az deployment sub create --name algolab-phase-2 --location uaenorth \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json \
       deployerObjectId="$DEPLOYER_OBJECT_ID" \
       apiContainerImage="cralgolabdevcdbf.azurecr.io/algolab-api:$IMAGE_TAG" \
       webContainerImage="cralgolabdevcdbf.azurecr.io/algolab-web:$IMAGE_TAG"
   ```

5. Read the public URL and verify the site and API through the same-origin proxy. The API is intentionally not directly public.

   ```bash
   az deployment sub show --name algolab-phase-2 \
     --query properties.outputs.webUrl.value -o tsv
   curl -fsS "$(az deployment sub show --name algolab-phase-2 --query properties.outputs.webUrl.value -o tsv)/health"
   curl -fsS "$(az deployment sub show --name algolab-phase-2 --query properties.outputs.webUrl.value -o tsv)/api/v1/algorithms"
   ```

## Review notes

- Do not commit a real deployer's object ID if the parameters file is shared publicly; pass it via a local parameters override instead.
- The backend `ALGOLAB_CORS_ORIGINS` is empty because browser calls use the same-origin Nginx proxy. `.env.example` contains only local host port settings and optional CORS; the host ports are not deployed.
- The frontend proxy uses Container Apps environment internal DNS (`ca-algolab-api-dev-cdbf`) and is injected at Nginx startup from `API_UPSTREAM`.
- Nginx rate-limits `/api/` requests per client IP. The deployment also caps replicas at two; review limits before broad public sharing.
- ACR is Basic at about USD $5/month in the plan estimate. Container Apps and logs can incur charges beyond applicable included grants.
