import boto3
import json
import os
from decimal import Decimal

DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'FailureHistory')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def lambda_handler(event, context):
    """
    Ponto de entrada da Lambda. Recebe um evento de falha do IoT Core
    e o insere na tabela DynamoDB de histórico de falhas.
    """
    print(f"Recebido evento de falha: {json.dumps(event)}")

    try:
        
        # 3. Inserção no DynamoDB
        print(f"Inserindo item na tabela {DYNAMODB_TABLE_NAME}: {event}")
        
        response = table.put_item(
            Item=event
        )
        
        print("Item inserido com sucesso no DynamoDB.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Rótulo de falha registrado com sucesso!',
                'item': event
            })
        }
    
    except Exception as e:
        print(f"Erro inesperado ao processar o evento: {e}")
        return {'statusCode': 500, 'body': json.dumps("Erro interno no servidor.")}