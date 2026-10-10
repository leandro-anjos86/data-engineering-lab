import os
import time
import socket
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
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}
            )
        )

    @staticmethod
    def ensure_bucket_exists(bucket_name: str):
        # Garante que o bucket S3 exista antes de realizar uploads/downloads.
        s3 = S3ClientFactory.get_client()
        try:
            s3.head_bucket(Bucket=bucket_name)
        except Exception:
            s3.create_bucket(Bucket=bucket_name)
            
    @staticmethod
    def ensure_redshift_cluster_exists(cluster_id: str = "redshift-cluster-1"):
        """Garante que o cluster Redshift exista no Floci e aguarda a porta responder."""
        host = os.getenv("REDSHIFT_HOST", "host.docker.internal")
        port = int(os.getenv("REDSHIFT_PORT", 7100))

        # 1. Se a porta já responde, não faz nada
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except (OSError, ConnectionRefusedError):
            pass

        # 2. Se a porta está fechada, solicita o provisionamento ao Floci
        redshift = boto3.client(
            "redshift",
            endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://floci:4566"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
        try:
            redshift.describe_clusters(ClusterIdentifier=cluster_id)
        except Exception:
            try:
                redshift.create_cluster(
                    ClusterIdentifier=cluster_id,
                    NodeType="dc2.large",
                    MasterUsername=os.getenv("REDSHIFT_USER"),
                    MasterUserPassword=os.getenv("REDSHIFT_PASSWORD"),
                    DBName=os.getenv("REDSHIFT_DB"),
                    Port=port
                )
            except Exception:
                pass

        # 3. Aguarda ativamente dentro do método até 20s para a porta abrir
        for _ in range(20):
            try:
                with socket.create_connection((host, port), timeout=1):
                    return
            except (OSError, ConnectionRefusedError):
                time.sleep(1)