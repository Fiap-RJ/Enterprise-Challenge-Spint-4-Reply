#!/bin/bash

# =============================================================================
# SCRIPT DE BUILD DO AWS LAMBDA LAYER PARA PANDAS + SCIKIT-LEARN
# =============================================================================
# 
# Este script automatiza a criação de um pacote .zip para AWS Lambda Layer
# contendo pandas, scikit-learn e suas dependências, seguindo a estrutura 
# correta exigida pelo AWS Lambda (pasta 'python' dentro do zip).
#
# Autor: DevOps Engineer
# Data: 2025-01-15
# =============================================================================

# Configuração: parar execução em caso de erro
set -e

# =============================================================================
# CONFIGURAÇÕES E VARIÁVEIS
# =============================================================================

# Diretórios
BUILD_DIR=".build/layer"
DIST_DIR="dist"
LAYER_NAME="pandas_sklearn_layer"
PYTHON_VERSION="3.12"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

print_step() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

main() {
    print_step "Iniciando build do AWS Lambda Layer para pandas + scikit-learn..."
    
    # 1. Limpeza e preparação
    print_step "Limpando diretórios de build anteriores..."
    rm -rf .build
    mkdir -p "${BUILD_DIR}"
    mkdir -p "${DIST_DIR}"
    
    # 2. Verificação do Python
    print_step "Verificando versão do Python..."
    if ! command -v python${PYTHON_VERSION} > /dev/null 2>&1; then
        print_error "Python ${PYTHON_VERSION} não encontrado. Por favor, instale Python ${PYTHON_VERSION}."
        exit 1
    fi
    
    PYTHON_VER=$(python${PYTHON_VERSION} --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_step "Versão do Python detectada: ${PYTHON_VER}"
    
    if [ "${PYTHON_VER}" != "${PYTHON_VERSION}" ]; then
        print_error "Versão do Python (${PYTHON_VER}) não corresponde à versão esperada (${PYTHON_VERSION})."
        exit 1
    fi
    
    # 3. Criação do ambiente virtual
    print_step "Criando ambiente virtual Python ${PYTHON_VERSION}..."
    python${PYTHON_VERSION} -m venv "${BUILD_DIR}/venv"
    source "${BUILD_DIR}/venv/bin/activate"
    
    # 4. Atualização do pip
    print_step "Atualizando pip..."
    pip install --upgrade pip
    
    # 5. Instalação do pandas, scikit-learn e dependências
    print_step "Instalando pandas, scikit-learn e dependências..."
    pip install pandas numpy scikit-learn
    
    # 6. Criação da estrutura correta para Lambda Layer
    print_step "Criando estrutura de diretórios para Lambda Layer..."
    mkdir -p "${BUILD_DIR}/python"
    
    # 7. Cópia das bibliotecas para a estrutura correta
    print_step "Copiando bibliotecas para estrutura do Lambda Layer..."
    cp -r "${BUILD_DIR}/venv/lib/python${PYTHON_VER}/site-packages/"* "${BUILD_DIR}/python/"
    
    # 8. Verificação da estrutura
    print_step "Verificando estrutura do Lambda Layer..."
    if [ ! -d "${BUILD_DIR}/python/pandas" ]; then
        print_error "Estrutura do Lambda Layer incorreta. pandas não encontrado."
        exit 1
    fi
    
    if [ ! -d "${BUILD_DIR}/python/numpy" ]; then
        print_error "Estrutura do Lambda Layer incorreta. numpy não encontrado."
        exit 1
    fi
    
    if [ ! -d "${BUILD_DIR}/python/sklearn" ]; then
        print_error "Estrutura do Lambda Layer incorreta. sklearn não encontrado."
        exit 1
    fi
    
    print_success "Estrutura do Lambda Layer verificada com sucesso!"
    
    # 9. Criação do arquivo ZIP
    print_step "Criando arquivo ZIP do Lambda Layer..."
    cd "${BUILD_DIR}"
    zip -r "../../${DIST_DIR}/${LAYER_NAME}.zip" python/
    cd - > /dev/null
    
    # 10. Verificação do arquivo criado
    if [ -f "${DIST_DIR}/${LAYER_NAME}.zip" ]; then
        FILE_SIZE=$(du -h "${DIST_DIR}/${LAYER_NAME}.zip" | cut -f1)
        print_success "Arquivo ${LAYER_NAME}.zip criado com sucesso! Tamanho: ${FILE_SIZE}"
    else
        print_error "Falha ao criar arquivo ZIP do Lambda Layer."
        exit 1
    fi
    
    # 11. Limpeza do ambiente de build
    print_step "Limpando diretório de build temporário..."
    rm -rf .build
    
    # 12. Informações finais
    print_success "Build do Lambda Layer concluído com sucesso!"
    echo ""
    print_step "Arquivo gerado: ${DIST_DIR}/${LAYER_NAME}.zip"
    print_step "Para usar no Terraform, atualize a variável 'pandas_layer_zip_path' para:"
    echo "  \"./${DIST_DIR}/${LAYER_NAME}.zip\""
    echo ""
    print_step "Estrutura do arquivo ZIP:"
    unzip -l "${DIST_DIR}/${LAYER_NAME}.zip" | head -20
    echo ""
    print_success "Lambda Layer pronto para deploy!"
}

# =============================================================================
# EXECUÇÃO
# =============================================================================

# Verificação se está sendo executado diretamente
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
