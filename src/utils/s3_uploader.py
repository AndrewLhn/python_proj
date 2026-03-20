import boto3
import json
import logging
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_REGION, S3_BUCKET_NAME, DATA_FILE_PREFIX, TIMESTAMP
)

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        self.bucket_name = S3_BUCKET_NAME
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    
    def validate_data_before_upload(self, data: list) -> bool:
        """Проверка данных перед загрузкой"""
        if not data:
            logger.error("No data to upload")
            return False
        
        # Проверяем, что это список
        if not isinstance(data, list):
            logger.error("Data is not a list")
            return False
        
        # Проверяем каждый элемент
        for item in data:
            if not isinstance(item, dict):
                logger.error("Data item is not a dictionary")
                return False
            
            # Проверяем обязательные поля
            required_fields = ['repository', 'extracted_at']
            for field in required_fields:
                if field not in item:
                    logger.error(f"Missing required field: {field}")
                    return False
        
        logger.info(f"Data validation passed. {len(data)} items ready for upload")
        return True
    
    def generate_file_name(self) -> str:
        """Генерация имени файла с timestamp"""
        return f"{DATA_FILE_PREFIX}_{TIMESTAMP}.json"
    
    def upload_data(self, data: list) -> bool:
        """Загрузка данных в S3"""
        try:
            # Валидация
            if not self.validate_data_before_upload(data):
                return False
            
            # Генерация имени файла
            file_name = self.generate_file_name()
            
            # Конвертация в JSON
            json_data = json.dumps(data, indent=2, default=str)
            
            # Загрузка в S3
            logger.info(f"Uploading to s3://{self.bucket_name}/{file_name}")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'extraction_date': TIMESTAMP,
                    'record_count': str(len(data))
                }
            )
            
            logger.info(f"Successfully uploaded {file_name} to S3")
            
            # Также сохраняем локально для отладки
            self.save_local_backup(data, file_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return False
    
    def save_local_backup(self, data: list, file_name: str):
        """Сохранение локальной копии для отладки"""
        try:
            os.makedirs('output', exist_ok=True)
            local_path = f"output/{file_name}"
            
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Local backup saved to {local_path}")
        except Exception as e:
            logger.error(f"Error saving local backup: {e}")