import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# para carregar as variáveis de ambiente listadas no arquivo .env
load_dotenv()

class S3ClientFactory:
    """
    criação da classe responsável de criar e gerenciar a conexão com o S3
    e que é compatível com Floci/LocalStack e AWS S3 real
    """
    @staticmethod
    def get_client():
        return boto3.client(
            "s3",
            endpoint_url=os.getenv("AWS_ENDPOINT_URL", "na"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "na"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}
            )
        )