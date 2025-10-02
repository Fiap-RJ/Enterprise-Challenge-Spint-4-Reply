# Instalação e Execução do Dashboard de Manutenção Preditiva

## Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. **Clone o repositório** (se ainda não foi feito):
   ```bash
   git clone <url-do-repositorio>
   cd Enterprise_Challenge-Sprint_4
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## Execução

1. **Navegue para o diretório src**:
   ```bash
   cd src
   ```

2. **Execute o aplicativo Streamlit**:
   ```bash
   streamlit run app.py
   ```

3. **Acesse o dashboard**:
   - O aplicativo será aberto automaticamente no seu navegador
   - URL padrão: http://localhost:8501

## Funcionalidades

- **Dashboard Principal**: Visualização do status de todas as máquinas
- **Análise Detalhada**: Seleção de máquina específica para análise
- **Previsão de Falhas**: Simulação de modelo de ML para predição
- **Atualização de Dados**: Botão para recarregar dados em tempo real

## Estrutura do Projeto

```
src/
├── app.py              # Aplicação principal Streamlit
├── data_connector.py   # Simulação de dados e APIs
requirements.txt        # Dependências do projeto
```

## Solução de Problemas

### Erro de Import
Se você encontrar erros de import, certifique-se de que:
- Todas as dependências estão instaladas: `pip install -r requirements.txt`
- Você está executando o comando a partir do diretório `src/`

### Porta em Uso
Se a porta 8501 estiver em uso, o Streamlit tentará usar a próxima porta disponível (8502, 8503, etc.).


