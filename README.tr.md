# Azure Dashboard

Bu proje, Azure DevOps projelerinizin metriklerini ve durumunu görsel olarak takip edebileceğiniz modern bir dashboard uygulamasıdır.

## Özellikler
- Azure DevOps projeleri, pipeline'lar, repository'ler ve release'ler hakkında özet bilgiler
- Kullanıcı dostu ve modern arayüz
- Hızlı kurulum ve kolay yapılandırma

## Kurulum

1. **Projeyi klonlayın:**

```bash
git clone <repo-url>
cd AzureDashboard
```

2. **Gerekli ortam değişkenlerini ayarlayın:**

`.env.example` dosyasını kopyalayıp `.env` olarak adlandırın ve kendi Azure DevOps bilgilerinizle doldurun:

```bash
cp .env.example .env
```

`.env` dosyası örneği:
```
AZURE_DEVOPS_ORG_URL= # Örn: https://dev.azure.com/<org-adiniz>
AZURE_DEVOPS_PAT=     # Azure DevOps Personal Access Token
```

3. **Docker Compose ile uygulamayı başlatın:**

```bash
docker-compose up --build
```

Tüm servisler otomatik olarak ayağa kalkacaktır. Uygulamaya tarayıcınızdan erişebilirsiniz.

## Lisans
Bu proje MIT lisansı ile lisanslanmıştır.
