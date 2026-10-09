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
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "na"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
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
        # Garante que o cluster Redshift exista no Floci para disponibilizar a porta 7100.
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
            redshift.create_cluster(
                ClusterIdentifier=cluster_id,
                NodeType="dc2.large",
                MasterUsername=os.getenv("REDSHIFT_USER"),
                MasterUserPassword=os.getenv("REDSHIFT_PASSWORD"),
                DBName=os.getenv("REDSHIFT_DB"),
                Port=int(os.getenv("REDSHIFT_PORT"))
            )