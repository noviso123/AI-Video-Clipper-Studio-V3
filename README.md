# AI Video Clipper iOS

**App Flutter 100% Native para iPhone 16E**

## 🚀 Estrutura do Projeto

```
AI-Video-Clipper-Studio-V3/
├── lib/                        # Código Flutter
│   ├── main.dart               # Entry point
│   ├── backend/                # Lógica de negócio
│   │   ├── core/               # Configurações
│   │   ├── models/             # Data models
│   │   ├── services/           # Services
│   │   └── utils/              # Helpers
│   └── frontend/               # Interface
│       ├── screens/            # Telas
│       ├── widgets/            # Componentes
│       └── theme/              # Estilos
├── ios/                        # Config iOS nativa
├── assets/                     # Recursos
├── .test_output/              # 🗑️ Logs temporários
│   ├── logs/
│   └── reports/
├── pubspec.yaml               # Dependências
├── codemagic.yaml            # CI/CD
└── .github/workflows/        # GitHub Actions
```

## ⚡ Início Rápido

```bash
# Instalar dependências
flutter pub get

# Analisar código
flutter analyze

# Build iOS
flutter build ios --release
```

## 📖 Documentação

- [INSTALL_GUIDE.md](INSTALL_GUIDE.md) - Como instalar Flutter e build
- [SHARE_EXTENSION_GUIDE.md](SHARE_EXTENSION_GUIDE.md) - Publicação nativa iOS

## 🏗️ Arquitetura

- **Backend** (`lib/backend/`): Lógica de negócio, sem UI
- **Frontend** (`lib/frontend/`): Apenas interface
- **Separação clara**: Backend pode ser reutilizado

## 📦 Build Remoto

**Codemagic**: Push → Build automático → Download .ipa  
**GitHub Actions**: Push main → Build → Download artefato

## 📄 Licença

Projeto privado
