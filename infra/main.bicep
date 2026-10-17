targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

param sessionId string
param deployedBy string
param createdAt string
param deployerObjectId string

param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param apiContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param webContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var effectiveApiImage = apiContainerImage == 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' ? containerImage : apiContainerImage
var effectiveWebImage = webContainerImage == 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' ? containerImage : webContainerImage

var tags = {
  'app-onboard-skill': 'true'
  'app-onboard-session-id': sessionId
  'created-at': createdAt
  environment: environmentName
  'deployed-by': deployedBy
}

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'rg-algolab-dev-cdbf'
  location: location
  tags: tags
}

module logAnalytics './modules/log-analytics.bicep' = {
  name: 'logAnalytics'
  scope: rg
  params: {
    location: location
    tags: tags
  }
}

module registry './modules/container-registry.bicep' = {
  name: 'containerRegistry'
  scope: rg
  params: {
    location: location
    tags: tags
  }
}

module pullIdentity './modules/pull-identity.bicep' = {
  name: 'pullIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
  }
}

module containerEnvironment './modules/container-apps-environment.bicep' = {
  name: 'containerAppsEnvironment'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsWorkspaceName: 'log-algolab-dev-cdbf'
  }
  dependsOn: [logAnalytics]
}

module api './modules/container-app.bicep' = {
  name: 'apiContainerApp'
  scope: rg
  params: {
    appName: 'ca-algolab-api-dev-cdbf'
    appPort: 8000
    externalIngress: false
    containerImage: effectiveApiImage
    registryServer: registry.outputs.loginServer
    pullIdentityResourceId: pullIdentity.outputs.identityResourceId
    environmentId: containerEnvironment.outputs.environmentId
    apiUpstream: ''
    location: location
    tags: tags
  }
}

module web './modules/container-app.bicep' = {
  name: 'webContainerApp'
  scope: rg
  params: {
    appName: 'ca-algolab-web-dev-cdbf'
    appPort: 80
    externalIngress: true
    containerImage: effectiveWebImage
    registryServer: registry.outputs.loginServer
    pullIdentityResourceId: pullIdentity.outputs.identityResourceId
    environmentId: containerEnvironment.outputs.environmentId
    apiUpstream: 'http://${api.outputs.ingressFqdn}'
    location: location
    tags: tags
  }
}

module roleAssignments './modules/role-assignments.bicep' = {
  name: 'roleAssignments'
  scope: rg
  params: {
    registryName: 'cralgolabdevcdbf'
    pullIdentityPrincipalId: pullIdentity.outputs.principalId
    deployerObjectId: deployerObjectId
  }
  dependsOn: [registry]
}

output resourceGroupName string = rg.name
output registryLoginServer string = registry.outputs.loginServer
output apiIngressFqdn string = api.outputs.ingressFqdn
output webUrl string = 'https://${web.outputs.ingressFqdn}'
