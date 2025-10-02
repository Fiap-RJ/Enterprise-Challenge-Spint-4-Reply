import os
import json
from lambda_function import lambda_handler

# Configura as variáveis de ambiente para o teste
os.environ["DATA_LAKE_BUCKET"] = "replyec-data-lake-20250115"  # Substitua pelo seu bucket
os.environ["DYNAMODB_TABLE_NAME"] = "MachineFeatureStore"

# Cria um evento de teste (vazio, já que não usamos parâmetros do evento)
test_event = {}

# Cria um contexto de teste (simplificado)
class TestContext:
    def __init__(self):
        self.function_name = "test-lambda-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
        self.aws_request_id = "test-request-id"

# Executa o teste
if __name__ == "__main__":
    print("=== INICIANDO TESTE DO LAMBDA HANDLER ===")
    
    try:
        # Chama o lambda_handler como se estivesse rodando na AWS
        result = lambda_handler(test_event, TestContext())
        print("\n=== RESULTADO ===")
        print(json.dumps(result, indent=2))
        
        if result["statusCode"] == 200:
            print("\n✅ Teste concluído com SUCESSO!")
        else:
            print(f"\n❌ Ocorreu um erro: {result['body']}")
            
    except Exception as e:
        print(f"\n❌ ERRO durante a execução: {str(e)}")
        raise
