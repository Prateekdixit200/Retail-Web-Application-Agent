# 🛒 Retail Web Application Agent

> An AI-powered shopping assistant built using the **Google Agent Development Kit (ADK)**, showcasing secure AI engineering, modular agent architecture, automated testing, and cloud-native deployment.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4?logo=google)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Ready-4285F4?logo=googlecloud)
![Terraform](https://img.shields.io/badge/Terraform-IaC-844FBA?logo=terraform)
![Pytest](https://img.shields.io/badge/Tested%20with-Pytest-success)
![License](https://img.shields.io/badge/License-Apache%202.0-orange)

---

## 📖 Overview

Retail Web Application Agent is an intelligent AI shopping assistant developed with the **Google Agent Development Kit (ADK)**. It demonstrates how to build production-ready AI agents using a secure, modular, and scalable architecture.

## ✨ Features

- 🤖 AI-powered shopping assistant
- 🧠 Natural language product recommendations
- 🏗️ Modular agent architecture
- 🔒 Secure prompt and runtime design
- 🧪 Automated unit and integration testing
- ☁️ Google Cloud deployment support
- 🚀 CI/CD-ready project structure
- 📦 Infrastructure as Code using Terraform

---

## 🏛️ Project Architecture

```text
                    User
                     │
                     ▼
              React Frontend
                     │
                     ▼
        Google ADK Shopping Agent
                     │
     ┌───────────────┼────────────────┐
     ▼               ▼                ▼
 Agent Logic     Runtime Layer     Utilities
                     │
                     ▼
              Google Cloud Services
                     │
                     ▼
               Deployment Pipeline
```

---

## 📂 Project Structure

```text
shopping-assistant/
├── agents/
├── app/
│   ├── agent.py
│   ├── agent_runtime_app.py
│   └── app_utils.py
├── deployment/
│   └── terraform/
├── tests/
├── GEMINI.md
├── README.md
├── pyproject.toml
├── uv.lock
└── deployment_metadata.json
```

---

## 🚀 Tech Stack

| Category | Technology |
|-----------|------------|
| Language | Python 3.12 |
| AI Framework | Google ADK |
| Frontend | React |
| Package Manager | uv |
| Testing | Pytest |
| Cloud Platform | Google Cloud Platform |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |

---

## ⚙️ Installation

```bash
git clone https://github.com/Prateekdixit200/Retail-Web-Application-Agent.git
cd Retail-Web-Application-Agent/shopping-assistant
```

Install dependencies:

```bash
agents-cli install
```

or

```bash
uv sync
```

Run locally:

```bash
agents-cli playground
```

---

## 🧪 Testing

```bash
uv run pytest
```

Unit tests:

```bash
uv run pytest tests/unit
```

Integration tests:

```bash
uv run pytest tests/integration
```

---

## ☁️ Deployment

```bash
gcloud config set project YOUR_PROJECT_ID
agents-cli deploy
```

Infrastructure:

```bash
agents-cli infra cicd
```

---

## 🔒 Security

This project emphasizes secure AI engineering through:

- Prompt injection awareness
- Modular runtime isolation
- Automated testing
- Secure deployment workflows
- Infrastructure as Code
- CI/CD validation

---

## 📚 Useful Commands

| Command | Description |
|----------|-------------|
| `agents-cli install` | Install dependencies |
| `agents-cli playground` | Start development server |
| `agents-cli lint` | Lint project |
| `agents-cli eval` | Evaluate agent |
| `uv run pytest` | Run tests |
| `agents-cli deploy` | Deploy application |

---

## 🗺️ Roadmap

- [ ] Multi-agent collaboration
- [ ] Vector database integration
- [ ] Retrieval-Augmented Generation (RAG)
- [ ] User authentication
- [ ] Shopping cart
- [ ] Payment gateway integration
- [ ] Persistent memory
- [ ] Docker support
- [ ] Kubernetes deployment

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a Pull Request.

---

## 📄 License

Licensed under the **Apache License 2.0**.

See the `LICENSE` file or visit:
https://www.apache.org/licenses/LICENSE-2.0

---

## 👨‍💻 Author

### Prateek Dixit

**AI Engineer • Software Developer • Data Analyst**

- GitHub: https://github.com/Prateekdixit200
- LinkedIn: https://www.linkedin.com/in/prateek-dixit-17a9b21ba/

---

## ⭐ Support

If you found this project useful:

- ⭐ Star this repository
- 🍴 Fork the project
- 🐞 Report bugs
- 💡 Suggest enhancements
- 🤝 Contribute

---

<p align="center">
<b>Building secure, scalable, and production-ready AI agents with Google ADK.</b>
</p>
