param location string
param tags object

resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: 'cralgolabdevcdbf'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
  tags: tags
}

output loginServer string = registry.properties.loginServer
output registryId string = registry.id
