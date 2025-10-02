#!/bin/bash

# =============================================================================
# SCRIPT DE VALIDAÇÃO DA INFRAESTRUTURA TERRAFORM
# =============================================================================

set -e

echo "Validando estrutura Terraform..."

# Verificar se estamos no diretório correto
if [ ! -f "main.tf" ]; then
    echo "Execute este script a partir do diretório terraform/"
    exit 1
fi

echo "Estrutura de diretórios encontrada"

# Validar módulo de ingestão
echo "🔍 Validando módulo de ingestão..."
cd modules/ingestion
terraform init -backend=false
terraform validate
echo "Módulo de ingestão válido"
cd ../..

# Validar configuração principal
echo "Validando configuração principal..."
terraform init -backend=false
terraform validate
echo "Configuração principal válida"

echo "Todas as validações passaram com sucesso!"
echo ""
echo "Próximos passos:"
echo "1. Edite terraform.tfvars se necessário"
echo "2. terraform init"
echo "3. terraform plan"
echo "4. terraform apply"
