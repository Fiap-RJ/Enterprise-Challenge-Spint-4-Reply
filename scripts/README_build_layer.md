# Script de Build do AWS Lambda Layer para Pandas

Este documento descreve como usar o script `build_layer.sh` para automatizar a criação de um AWS Lambda Layer contendo pandas e suas dependências.

## 📋 Pré-requisitos

- **Python 3.11** ou superior instalado no sistema
- **pip** (geralmente vem com Python)
- **zip** (geralmente disponível em sistemas Linux/macOS)

## 🚀 Como Usar

### 1. Navegar para o Diretório do Projeto

```bash
cd /home/arthur/Projects/Fiap/Enterprise-Challenge-Spint-4-Reply
```

### 2. Executar o Script

```bash
./scripts/build_layer.sh
```

### 3. Verificar o Resultado

Após a execução bem-sucedida, você encontrará:

- **Arquivo gerado**: `dist/pandas_layer.zip`
- **Tamanho**: Aproximadamente 50-100 MB (dependendo das dependências)

## 📁 Estrutura do Arquivo Gerado

O arquivo `pandas_layer.zip` terá a seguinte estrutura interna:

```
pandas_layer.zip
└── python/
    ├── pandas/
    ├── numpy/
    ├── pytz/
    ├── dateutil/
    └── ... (outras dependências)
```

## 🔧 Configuração do Terraform

O script já atualiza automaticamente a variável do Terraform para referenciar o caminho correto:

```hcl
variable "pandas_layer_zip_path" {
  description = "Caminho para o arquivo ZIP do Lambda Layer do pandas"
  type        = string
  default     = "./dist/pandas_layer.zip"
}
```

## 🛠️ Funcionalidades do Script

### ✅ O que o Script Faz

1. **Limpeza**: Remove diretórios de build anteriores
2. **Verificação**: Confirma se Python 3.11+ está disponível
3. **Ambiente Virtual**: Cria um ambiente virtual isolado
4. **Instalação**: Instala pandas e numpy com todas as dependências
5. **Estrutura**: Organiza as bibliotecas na estrutura correta (`python/`)
6. **Compactação**: Cria o arquivo ZIP do Lambda Layer
7. **Verificação**: Confirma que a estrutura está correta
8. **Limpeza**: Remove arquivos temporários
9. **Relatório**: Mostra informações sobre o arquivo gerado

### 🎨 Output Colorido

O script usa cores para facilitar a leitura:

- 🔵 **Azul**: Informações gerais
- 🟢 **Verde**: Sucessos
- 🟡 **Amarelo**: Avisos
- 🔴 **Vermelho**: Erros

## 🚨 Tratamento de Erros

O script para imediatamente se:

- Python não estiver instalado
- Falhar na instalação das dependências
- A estrutura do Lambda Layer estiver incorreta
- Não conseguir criar o arquivo ZIP

## 📊 Exemplo de Execução

```bash
$ ./scripts/build_layer.sh

[INFO] Iniciando build do AWS Lambda Layer para pandas...
[INFO] Limpando diretórios de build anteriores...
[INFO] Verificando versão do Python...
[INFO] Versão do Python detectada: 3.11
[INFO] Criando ambiente virtual Python...
[INFO] Atualizando pip...
[INFO] Instalando pandas e dependências...
[INFO] Criando estrutura de diretórios para Lambda Layer...
[INFO] Copiando bibliotecas para estrutura do Lambda Layer...
[INFO] Verificando estrutura do Lambda Layer...
[SUCCESS] Estrutura do Lambda Layer verificada com sucesso!
[INFO] Criando arquivo ZIP do Lambda Layer...
[SUCCESS] Arquivo pandas_layer.zip criado com sucesso! Tamanho: 67M
[INFO] Limpando diretório de build temporário...
[SUCCESS] Build do Lambda Layer concluído com sucesso!

Arquivo gerado: dist/pandas_layer.zip
Para usar no Terraform, atualize a variável 'pandas_layer_zip_path' para:
  "./dist/pandas_layer.zip"

[INFO] Estrutura do arquivo ZIP:
Archive:  dist/pandas_layer.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2025-01-15 10:30   python/
     1234  2025-01-15 10:30   python/pandas/__init__.py
     ...

[SUCCESS] Lambda Layer pronto para deploy!
```

## 🔄 Rebuild

Para recriar o Lambda Layer (útil após atualizações):

```bash
# O script automaticamente limpa builds anteriores
./scripts/build_layer.sh
```

## 📝 Notas Importantes

- O script cria um ambiente virtual temporário que é removido após a execução
- O arquivo final é salvo em `dist/pandas_layer.zip`
- A estrutura `python/` é obrigatória para o AWS Lambda Layer funcionar
- O script é compatível com Python 3.11 (ambiente de execução da Lambda)

## 🆘 Solução de Problemas

### Erro: "Python3 não encontrado"
```bash
# Instalar Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### Erro: "zip não encontrado"
```bash
# Instalar zip
sudo apt install zip
```

### Erro: "Permissão negada"
```bash
# Tornar o script executável
chmod +x scripts/build_layer.sh
```
