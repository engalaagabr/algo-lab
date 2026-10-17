# دليل نشر AlgoLab على Azure

الدليل ده بيشرح الرحلة من الكود لحد رابط الموقع، وإزاي نخلي النشر تلقائي وآمن. هو مبني على ملفات المشروع الحالية في `infra/` و`.github/workflows/ci-cd.yml`.

## الحالة الحالية

- الموقع والـ API منشوران على Azure Container Apps في UAE North.
- رابط الموقع الحالي: <https://ca-algolab-web-dev-cdbf.redsmoke-2fae7249.uaenorth.azurecontainerapps.io>
- رابط فحص الـ API: <https://ca-algolab-web-dev-cdbf.redsmoke-2fae7249.uaenorth.azurecontainerapps.io/health>
- الـ API داخلي، والموقع يمرر له الطلبات عن طريق Nginx على نفس الرابط.
- موارد Azure الحالية كلها باسم `dev`. الـ workflow الحالي ينشر إلى موارد `dev` عند وصول commit إلى `main`؛ **ده لا يعني إن عندنا production منفصل**.
- مافيش دومين مخصص مربوط بالتطبيق حتى الآن.

قبل تشغيل CI/CD على GitHub، راجع إعدادات المستودع وتأكد إنك موافق إن كل push إلى `main` ينشر تلقائيًا إلى تطبيق `dev` الحالي.

## يعني إيه CI/CD؟

- **CI — Continuous Integration:** مع كل Pull Request، GitHub يشغّل فحوصات الكود والبناء. لو فحص فشل، نصلحه قبل الدمج.
- **CD — Continuous Delivery/Deployment:** بعد دمج التغيير، GitHub يبني صور Docker، يرفعها إلى Azure Container Registry (ACR)، ثم يحدّث Azure Container Apps.
- **OIDC:** تسجيل دخول GitHub إلى Azure بهوية مؤقتة من غير تخزين كلمة مرور أو Client Secret في GitHub.
- **Revision:** نسخة من التطبيق داخل Container Apps. التطبيق عندنا يستخدم Single revision mode؛ Azure يحتفظ بالنسخة القديمة لحد ما الجديدة تبقى جاهزة، وبعدها يحول الترافيك لها.

## شكل النشر في المشروع

```text
Pull Request
  └─ CI: فحوصات Python وTypeScript وLint واختبارات وبناء الواجهة

دمج إلى main
  └─ CD: GitHub OIDC → ACR (بناء ورفع صور SHA) → API Container App → Web Container App
       └─ نفس النطاق العام: واجهة Nginx → API داخلي عبر HTTPS
```

الـ API لا يحتاج Ingress عامًا. صورة الـ API تُسحب إلى Container Apps بهوية Managed Identity عليها `AcrPull`، بينما هوية GitHub Actions تستخدم `AcrPush` لرفع الصور.

## 1. المتطلبات

تحتاج:

1. حساب Azure واشتراكًا نشطًا، وصلاحيات لإنشاء Resource Groups وAzure Container Registry وContainer Apps وRole Assignments.
2. Azure CLI وDocker للتجهيز الأولي اليدوي.
3. صلاحية Admin على مستودع GitHub لإعداد Actions secrets/variables وBranch protection.
4. دومين تملكه إذا أردت رابطًا مثل `algolab.example.com`.

الموارد المعرفة حاليًا في Bicep موجودة في [infra/main.bicep](../infra/main.bicep). خطوات التجهيز اليدوي الكاملة موجودة أيضًا في [دليل النشر اليدوي](../infra/DEPLOY-MANUALLY.md).

## 2. تجهيز Azure أول مرة

لو موارد `dev` الحالية موجودة وتعمل، تخطَّ خطوة إنشاء الموارد وانتقل إلى إعداد GitHub. لو تبدأ في اشتراك جديد:

1. سجّل الدخول واختر الاشتراك الصحيح:

   ```bash
   az login
   az account set --subscription a36d754c-33ac-46fe-be22-c63b93ce16e1
   az account show --output table
   ```

2. خذ Object ID لحساب Azure الذي ينفذ التهيئة:

   ```bash
   export DEPLOYER_OBJECT_ID="$(az ad signed-in-user show --query id --output tsv)"
   ```

3. اعمل مراجعة للتغييرات ثم أنشئ الموارد الأساسية. المرحلة الأولى تنشئ Resource Group وACR وLog Analytics وContainer Apps Environment والـ API والـ Web بصور placeholder. Ingress الـ API يظل داخليًا.

   ```bash
   az deployment sub what-if \
     --location uaenorth \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json deployerObjectId="$DEPLOYER_OBJECT_ID"

   az deployment sub create \
     --name algolab-phase-1 \
     --location uaenorth \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json deployerObjectId="$DEPLOYER_OBJECT_ID"
   ```

4. بعد انتشار صلاحيات ACR، ابنِ صورتي التطبيق وارفعهما. استخدم commit SHA كوسم للصورة حتى تعرف أي كود شغّال:

   ```bash
   export IMAGE_TAG="$(git rev-parse --short HEAD)"

   az acr build --registry cralgolabdevcdbf \
     --image "algolab-api:$IMAGE_TAG" \
     --file backend/Dockerfile backend/

   az acr build --registry cralgolabdevcdbf \
     --image "algolab-web:$IMAGE_TAG" \
     --file frontend/Dockerfile.azure .
   ```

5. حدّث Bicep بصور التطبيق الحقيقية:

   ```bash
   az deployment sub create \
     --name algolab-phase-2 \
     --location uaenorth \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json \
       deployerObjectId="$DEPLOYER_OBJECT_ID" \
       apiContainerImage="cralgolabdevcdbf.azurecr.io/algolab-api:$IMAGE_TAG" \
       webContainerImage="cralgolabdevcdbf.azurecr.io/algolab-web:$IMAGE_TAG"
   ```

6. استخرج الرابط وتأكد من فحص الصحة وقائمة الخوارزميات:

   ```bash
   export WEB_URL="$(az deployment sub show --name algolab-phase-2 \
     --query properties.outputs.webUrl.value --output tsv)"

   curl -i "$WEB_URL/health"
   curl -i "$WEB_URL/api/v1/algorithms"
   ```

المتوقع `200 OK` وJSON. لا تجعل Ingress الـ API عامًا لمجرد أن الواجهة تحتاجه؛ الـ Nginx proxy هو مسار الوصول العام.

## 3. إعداد GitHub Actions → Azure باستخدام OIDC

الـ workflow موجود في [.github/workflows/ci-cd.yml](../.github/workflows/ci-cd.yml). قبل أول تشغيل تلقائي، اربط GitHub بهوية Azure:

1. في Microsoft Entra، أنشئ App Registration مخصصة لنشر GitHub Actions، ثم أنشئ لها Service Principal.
2. أضف Federated credential من نوع GitHub Actions. للمستودع والفرع الحاليين اجعل القيم:

   | الحقل | القيمة |
   | --- | --- |
   | Organization | `engalaagabr` |
   | Repository | `AlgoLab` |
   | Entity | Branch |
   | Branch | `main` |
   | Audience | `api://AzureADTokenExchange` |
   | Subject المتوقع | `repo:engalaagabr/AlgoLab:ref:refs/heads/main` |

   لو اسم المالك أو المستودع مختلف على GitHub، استخدم الاسم الفعلي في إعداد Federation.

3. امنح Service Principal صلاحيات محدودة على الموارد الحالية:

   - `AcrPush` على مورد ACR فقط.
   - `Container Apps Contributor` على كل Container App سيحدّثه الـ workflow.

   لا تعطِ هوية النشر `Owner` أو `Contributor` على الاشتراك لمجرد تشغيل التطبيق. مستخدم Azure الذي يجهز الموارد أول مرة يحتاج صلاحيات إدارة منفصلة لإضافة Role Assignments.

4. في GitHub افتح **Settings → Secrets and variables → Actions**. أضف Repository secrets:

   | Secret | القيمة |
   | --- | --- |
   | `AZURE_CLIENT_ID` | Client ID لتطبيق Entra |
   | `AZURE_TENANT_ID` | Tenant ID |
   | `AZURE_SUBSCRIPTION_ID` | Subscription ID |

   وأضف Repository variables:

   | Variable | قيمة موارد dev الحالية |
   | --- | --- |
   | `AZURE_ACR_NAME` | `cralgolabdevcdbf` |
   | `AZURE_RESOURCE_GROUP` | `rg-algolab-dev-cdbf` |
   | `AZURE_API_CONTAINER_APP` | `ca-algolab-api-dev-cdbf` |
   | `AZURE_WEB_CONTAINER_APP` | `ca-algolab-web-dev-cdbf` |

   قيم Client/Tenant/Subscription هي معرفات وليست كلمات مرور. الـ workflow لا يحتاج Client Secret لأن تسجيل الدخول يتم عبر OIDC.

5. في **Settings → Rules → Rulesets**، احمِ `main` واشترط نجاح check اسمه **Test and build** قبل الدمج. اسمح بالدمج من خلال Pull Request فقط.

## 4. ماذا يحدث بعد إعداد CI/CD؟

1. افتح Pull Request إلى `dev` أو `main`.
2. GitHub يشغّل `ruff` و`pytest` للـ API، ثم type-check وlint وtests وbuild للواجهة.
3. لو أي خطوة فشلت، لا تدمج التغيير.
4. بعد الدمج إلى `main`، workflow الحالي يسجل الدخول عبر OIDC، ويبني صورتين بوسم commit SHA، ويرفعهما إلى ACR.
5. يحدّث API Container App أولًا ثم Web Container App.
6. راقب **GitHub → Actions → CI/CD**، ثم تحقق من revisions والصحة والرابط العام.

أوامر التحقق:

```bash
az containerapp revision list \
  --name ca-algolab-api-dev-cdbf \
  --resource-group rg-algolab-dev-cdbf \
  --output table

az containerapp revision list \
  --name ca-algolab-web-dev-cdbf \
  --resource-group rg-algolab-dev-cdbf \
  --output table

curl -fsS https://ca-algolab-web-dev-cdbf.redsmoke-2fae7249.uaenorth.azurecontainerapps.io/health
curl -fsS https://ca-algolab-web-dev-cdbf.redsmoke-2fae7249.uaenorth.azurecontainerapps.io/api/v1/algorithms
```

لو deployment فشل، افحص Logs وRevision health قبل إعادة المحاولة. في Single revision mode يظل الإصدار الحالي مستقبِلًا للترافيك حتى يجهز الإصدار الجديد. بعد النشر، يمكن إعادة صورة commit سابقة لتكوين revision رجوع.

## 5. ربط دومين قصير بالموقع

الرابط الافتراضي يتكون من اسم التطبيق وDNS suffix يولّده Azure. لتغيير شكله، استخدم دومين تملكه، مثل `algolab.example.com`، بدل محاولة تعديل suffix التلقائي. Azure Container Apps يطلب DNS record وشهادة TLS لكل دومين مخصص. [تفاصيل DNS والشهادات](https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-certificates).

1. اشترِ دومينًا أو استخدم دومينًا تملكه بالفعل.
2. من **Azure Portal → Container App للواجهة → Custom domains** أضف `algolab.your-domain.com` واختر شهادة مُدارة إذا كانت متاحة لهذا الإعداد.
3. انسخ القيم التي يعرضها Azure إلى DNS لدى مزود الدومين. غالبًا ستحتاج `CNAME` يشير إلى FQDN الحالي للواجهة و`TXT` باسم `asuid.algolab` لإثبات الملكية. استخدم القيم الدقيقة التي يعرضها Portal.
4. بعد انتشار DNS والتحقق، أكمل ربط الدومين وانتظر حالة **Secured**.
5. تحقق من الرابطين:

   ```bash
   curl -i https://algolab.your-domain.com/health
   curl -i https://algolab.your-domain.com/api/v1/algorithms
   ```

دومين قصير يقلل طول الرابط من غير إعادة تسمية التطبيق. لا تغيّر إعدادات DNS قبل تجهيز التحقق والشهادة. [إعداد DNS suffix مخصص للبيئة](https://learn.microsoft.com/en-us/azure/container-apps/environment-custom-dns-suffix) خيار مختلف ويحتاج wildcard certificate.

## 6. الانتقال من dev إلى production

**الـ workflow الحالي لا ينشر production.** هو ينشر إلى موارد `dev` المسماة في GitHub variables، حتى لو كان الفرع `main`. لا تغيّر هذه القيم إلى موارد prod قبل عزل البيئتين.

قبل إطلاق production:

1. جهّز مجموعة موارد وContainer Apps مستقلة للإنتاج. افصل بيانات الإعدادات والهوية والصلاحيات عن `dev`، وراجع limits والنسخ الاحتياطي والمراقبة والتكلفة.
2. اجعل أسماء الموارد في Bicep parameters بدل تثبيتها على `*-dev-cdbf`. الملف الحالي يثبت أسماء Resource Group وACR وEnvironment والتطبيقات؛ لذلك لا تستخدمه لإنشاء production كما هو.
3. انشر نسخة أولى من الـ API والواجهة إلى موارد prod، وتأكد من أن `API_UPSTREAM` للواجهة يشير إلى API الداخلي في **بيئة prod نفسها**.
4. اربط دومين الإنتاج بالتطبيق الجديد وتحقق من TLS و`/health` و`/api/v1/algorithms` قبل تحويل المستخدمين إليه.
5. أضف GitHub Environment باسم `production`، وقيّد الفروع التي يمكنها النشر، وفعّل Required reviewers. بيئة GitHub تقدر توقف deploy job لحين الموافقة وتفصل أسرار/متغيرات الإنتاج عن dev. [توثيق GitHub Environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments).
6. عدّل الـ workflow ليستخدم Environment وموارد prod صراحةً بعد نجاح CI. اربط OIDC بهوية نشر خاصة بالإنتاج ومقيدة بفرع أو بيئة الإنتاج.
7. جرّب الإصدار على dev أولًا، ثم ادمج إلى مسار النشر المحمي، وافق على نشر production، وراجع revision والصحة والـ logs بعد التحويل.
8. جهّز إجراء rollback: أعد deploy لوسم image SHA لآخر إصدار سليم، أو استخدم revisions/traffic management إذا قررت تفعيل Multiple revision mode. [مراجعة revisions وtraffic](https://learn.microsoft.com/en-us/azure/container-apps/revisions).

لا تعتبر التطبيق Production-ready بمجرد نجاح بناء الصور. لازم يكون هناك موارد prod منفصلة، إعداد موافقات، دومين وشهادة، فحوصات بعد النشر، ومراقبة وقرار واضح للـ rollback.

## مراجع المشروع

- [الـ workflow الحالي](../.github/workflows/ci-cd.yml)
- [الـ Bicep الحالي](../infra/main.bicep)
- [النشر اليدوي الحالي](../infra/DEPLOY-MANUALLY.md)
- [إعداد OIDC بين GitHub وAzure](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust?pivots=identity-wif-app-reg-github-actions)
- [Azure Login Action وOIDC](https://github.com/Azure/login#login-with-openid-connect-oidc-recommended)
- [GitHub Environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)
- [Azure Container Apps revisions](https://learn.microsoft.com/en-us/azure/container-apps/revisions)
- [سحب الصور من ACR بهوية Managed Identity](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull)
