param appName string
param appPort int
param externalIngress bool
param containerImage string
param registryServer string
param pullIdentityResourceId string
param environmentId string
param apiUpstream string
param location string
param tags object

var placeholderImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
var isPlaceholder = containerImage == placeholderImage
var effectivePort = isPlaceholder ? 80 : appPort

resource app 'Microsoft.App/containerApps@2026-07-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: externalIngress
        targetPort: effectivePort
        transport: 'http'
        allowInsecure: false
      }
      registries: isPlaceholder ? [] : [
        {
          server: registryServer
          identity: pullIdentityResourceId
        }
      ]
      secrets: []
    }
    template: {
      scale: {
        minReplicas: 0
        maxReplicas: 2
      }
      containers: [
        {
          name: appName
          image: containerImage
          resources: {
            #disable-next-line BCP036
            cpu: '0.25'
            memory: '0.5Gi'
          }
          probes: isPlaceholder ? [] : [
            {
              type: 'Readiness'
              httpGet: {
                path: appPort == 8000 ? '/health' : '/'
                port: appPort
                scheme: 'HTTP'
              }
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                path: appPort == 8000 ? '/health' : '/'
                port: appPort
                scheme: 'HTTP'
              }
              periodSeconds: 30
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
          env: concat(
            [
              {
                name: 'PORT'
                value: string(effectivePort)
              }
            ],
            empty(apiUpstream) ? [] : [
              {
                name: 'API_UPSTREAM'
                value: apiUpstream
              }
            ],
            appPort == 8000 ? [
              {
                name: 'ALGOLAB_CORS_ORIGINS'
                value: ''
              }
            ] : []
          )
        }
      ]
    }
  }
  tags: tags
}

output ingressFqdn string = app.properties.configuration.ingress.fqdn
