import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self, use_s3=False):
        self.use_s3 = use_s3
        self.bucket_name = None
        
        if use_s3:
            try:
                import boto3
                self.s3_client = boto3.client('s3')
                self.bucket_name = os.getenv("S3_BUCKET_NAME", "your-github-data-bucket")
                logger.info("S3Uploader initialized with AWS")
            except Exception as e:
                logger.warning(f"S3 not available: {e}")
                self.use_s3 = False
                logger.info("Falling back to local storage")
        else:
            logger.info("S3Uploader initialized in LOCAL mode (files saved to output/)")
    
    def validate_data_before_upload(self, data: list) -> bool:
        if not data:
            logger.error("No data to upload")
            return False
        
        if not isinstance(data, list):
            logger.error("Data is not a list")
            return False
        
        for item in data:
            if not isinstance(item, dict):
                logger.error("Data item is not a dictionary")
                return False
        
        logger.info(f"Data validation passed. {len(data)} items ready for upload")
        return True
    
    def generate_file_name(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"github_repos_data_{timestamp}.json"
    
    def upload_data(self, data: list) -> bool:
        try:
            if not self.validate_data_before_upload(data):
                return False
            
            file_name = self.generate_file_name()
            
            os.makedirs('output', exist_ok=True)
            
            local_path = f"output/{file_name}"
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f" Data saved locally to: {local_path}")
            logger.info(f" File size: {os.path.getsize(local_path):,} bytes")
            
            if self.use_s3:
                try:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=file_name,
                        Body=json.dumps(data, indent=2, default=str),
                        ContentType='application/json'
                    )
                    logger.info(f" Data also uploaded to S3: s3://{self.bucket_name}/{file_name}")
                except Exception as e:
                    logger.warning(f" S3 upload failed: {e}")
                    logger.info(" Local copy is still available")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False
