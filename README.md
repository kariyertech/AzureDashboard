# 📊 Azure DevOps Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![Azure DevOps](https://img.shields.io/badge/Azure%20DevOps-Compatible-0078d4.svg)](https://azure.microsoft.com/en-us/services/devops/)
[![React](https://img.shields.io/badge/React-Frontend-61dafb.svg)](https://reactjs.org/)

**Azure DevOps Dashboard**, Azure DevOps projelerinizin metriklerini ve durumlarını görsel olarak takip etmenizi sağlayan modern ve kullanıcı dostu bir dashboard uygulamasıdır.

![Azure DevOps Dashboard Screenshot](docs/screenshot.png)

## ✨ Özellikler

- 📈 **Comprehensive Metrics**: Projeler, pipeline'lar, repository'ler ve release'lerin detaylı özet bilgileri
- 🎨 **Modern Arayüz**: Kullanıcı dostu ve responsive tasarım
- ⚡ **Real-time Data**: Azure DevOps API'si ile anlık veri synchronizasyonu
- 📊 **Visual Analytics**: Grafik ve chartlar ile veri görselleştirme
- 🔄 **Multi-Project Support**: Birden fazla Azure DevOps projesini tek arayüzden yönetim
- 🚀 **Quick Setup**: Docker Compose ile kolay kurulum
- 🔒 **Secure**: Personal Access Token ile güvenli API erişimi

## 🛠️ Teknolojiler

**Frontend:**
- React.js / TypeScript
- Modern CSS3 / SCSS
- Chart.js / D3.js (görselleştirme için)
- Responsive Grid Layout

**Backend:**
- Node.js / Express.js
- Azure DevOps REST API Integration

**Infrastructure:**
- Docker & Docker Compose

## 📋 Gereksinimler

- Docker ve Docker Compose
- Azure DevOps Organization erişimi
- Azure DevOps Personal Access Token (PAT)
- Modern web browser

## 🚀 Hızlı Başlangıç

### 1. Projeyi İndirin

```bash
git clone https://github.com/[username]/AzureDashboard.git
cd AzureDashboard
```

### 2. Environment Konfigürasyonu

`.env.example` dosyasını `.env` olarak kopyalayın ve kendi Azure DevOps bilgilerinizi girin:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:

```env
# Azure DevOps Configuration
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization
AZURE_DEVOPS_PAT=your-personal-access-token

# Application Configuration
PORT=3000
API_PORT=5000
NODE_ENV=production

### 3. Azure DevOps Personal Access Token Oluşturma

1. Azure DevOps'a giriş yapın
2. **User Settings** > **Personal Access Tokens** bölümüne gidin
3. **New Token** oluşturun
4. Aşağıdaki izinleri verin:
   - **Build**: Read
   - **Code**: Read
   - **Project and Team**: Read
   - **Release**: Read
   - **Work Items**: Read

### 4. Uygulamayı Başlatın

```bash
# Development için
docker-compose up --build

# Production için
docker-compose -f docker-compose.yml up --build -d
```

### 5. Dashboard'a Erişin

Uygulama başarıyla başladıktan sonra:

- **Dashboard**: http://localhost:3000
- **API Endpoint**: http://localhost:5000

## 📖 Kullanım Kılavuzu

### Dashboard Ana Ekranı

**Üst Metrikleri:**
- **Toplam Projeler**: Azure DevOps organization'ınızdaki toplam proje sayısı
- **Build Pipelines**: Aktif build pipeline sayısı
- **Release Pipelines**: Aktif release pipeline sayısı
- **Toplam Commits**: Son 7 gündeki commit sayısı

**Deployment Analitikleri:**
- **Aylık Ortam Bazlı Deployment**: Environment'lara göre deployment frekansı
- **Deployment Frequency**: Günlük deployment sayıları
- **Success Rate Analytics**: Pipeline başarı oranları

**Proje Metrikleri:**
- **En Aktif Kullanıcılar**: Commit ve activity bazında sıralama
- **Release Başarı Oranı**: Son deployment'ların başarı yüzdesi
- **Build Sayısı**: Proje bazında build istatistikleri

### Proje Seçimi ve Filtreleme

1. **Select a Project** dropdown'ından istediğiniz projeyi seçin
2. Seçilen projeye özel metrikleri görüntüleyin
3. Zaman aralığı filtrelerini kullanarak historical data'ya erişin

### Real-time Updates

Dashboard otomatik olarak şu aralıklarla güncellenir:
- **Pipeline Status**: 30 saniye
- **Commit Data**: 5 dakika
- **Release Information**: 10 dakika

## 🔧 Gelişmiş Konfigürasyon

## 🔍 Troubleshooting

**❌ 401 Unauthorized Error:**
```bash
# PAT token'ınızı kontrol edin
curl -u ":your-pat-token" https://dev.azure.com/your-org/_apis/projects
```

**❌ Docker Memory Issues:**
```bash
# Docker memory limitini artırın
docker-compose up --memory=2g
```

## 📄 Lisans

Bu proje [MIT License](LICENSE) altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.
