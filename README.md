# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# FarmTech na era da cloud computing

## 👨‍🎓 Integrantes: 
- <a href="https://www.linkedin.com/in/arthur-alentejo">Arthur Guimarães Alentejo</a>
- <a href="https://www.linkedin.com/in/michaelrodriguess">Michael Rodrigues</a>
- <a href="https://www.linkedin.com/in/nathalia-vasconcelos-18a390292/">Nathalia Vasconcelos</a> 

## 👩‍🏫 Professores:
### Tutor(a) 
- <a href="https://www.linkedin.com/company/inova-fusca">Lucas Gomes Moreira</a>
### Coordenador(a)
- <a href="https://www.linkedin.com/company/inova-fusca">Andre Godoi</a>

## 📜 Descrição

 🤖 Banco de Dados e Machine Learning

O projeto implementa uma solução de Manutenção Preditiva para equipamentos industriais utilizando Machine Learning e arquitetura serverless na AWS. A solução monitora sensores de vibração e temperatura de máquinas para prever falhas potenciais.

### Arquitetura do Projeto

A arquitetura adota um padrão robusto de **Injestão de Streaming** para dados brutos e **Processamento em Lote (Batch)** para engenharia de features:

1. **Fluxo de Dados**:
   - Coleta de dados de sensores (temperatura e vibração) via IoT Core
   - Processamento em tempo real com AWS Lambda
   - Armazenamento em Data Lake (S3)

2. **Pipeline de ML**:
   - Processamento em lote para feature engineering
   - Treinamento de modelo preditivo com Amazon SageMaker
   - Deploy do modelo em produção

3. **Monitoramento**:
   - Dashboard em tempo real com Streamlit
   - Alertas para anomalias detectadas

### Como Executar o Projeto

1. **Pré-requisitos**:
   - Conta AWS configurada
   - AWS CLI instalado e configurado
   - Python 3.8+ e pip

2. **Configuração Inicial**:
   ```bash
   # Clonar o repositório
   git clone https://github.com/Fiap-RJ/Enterprise-Challenge-Spint-4-Reply.git
   
   cd Enterprise-Challenge-Spint-4-Reply
   
   # Criar e ativar ambiente virtual
   python -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   
   # Instalar dependências
   pip install -r requirements.txt
   ```

3. **Implantação da Infraestrutura**:
   ```bash
   cd infrastructure
   cdk deploy
   ```

4. **Executando o Dashboard**:
   ```bash
   cd src/dashboard
   streamlit run app.py
   ```

## 🎥 Vídeo de Apresentação

Assista ao vídeo de 5 minutos que explica o projeto em detalhes:

**[Link para o vídeo no YouTube](#)**

## � Estrutura de pastas

- `.github/`: Configurações do GitHub Actions para CI/CD
- `assets/`: Imagens e recursos visuais do projeto
- `document/`: Documentação detalhada do projeto
- `infrastructure/`: Código CDK para provisionamento da infraestrutura
- `src/`: Código-fonte do projeto
  - `data/`: Scripts para geração e processamento de dados
  - `ml/`: Pipeline de machine learning
  - `dashboard/`: Aplicação Streamlit para visualização
  - `lambda/`: Funções AWS Lambda
- `tests/`: Testes automatizados

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
