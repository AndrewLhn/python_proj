import requests
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Добавляем путь к проекту для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import GITHUB_API_BASE_URL, GITHUB_TOKEN, REPOSITORIES
from utils.s3_uploader import S3Uploader
from utils.data_validator import DataValidator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/github_extract_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubDataExtractor:
    def __init__(self, token: str = None):
        self.base_url = GITHUB_API_BASE_URL
        self.token = token or GITHUB_TOKEN
        self.session = requests.Session()
        
        # Настройка заголовков
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-Data-Extractor"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
            logger.info("Using authenticated GitHub API (higher rate limits)")
        else:
            logger.warning("No token provided. Rate limit: 60 requests/hour")
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Проверка оставшихся лимитов API"""
        try:
            response = self.session.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check rate limit: {e}")
            return {}
    
    def handle_rate_limit(self, response: requests.Response) -> None:
        """Обработка rate limiting"""
        if response.status_code == 403 and 'rate limit' in response.text.lower():
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            current_time = time.time()
            
            if reset_time > current_time:
                sleep_time = reset_time - current_time + 5
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
                return True
        return False
    
    def get_repository_data(self, repo_full_name: str) -> Dict[str, Any]:
        """Получение данных о репозитории"""
        try:
            url = f"{self.base_url}/repos/{repo_full_name}"
            logger.info(f"Fetching data for repository: {repo_full_name}")
            
            response = self.session.get(url, headers=self.headers)
            
            # Проверка rate limiting
            if self.handle_rate_limit(response):
                response = self.session.get(url, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repository {repo_full_name}: {e}")
            return {}
    
    def get_repo_contributors(self, repo_full_name: str, max_contributors: int = 10) -> List[Dict[str, Any]]:
        """Получение списка контрибьюторов с пагинацией"""
        contributors = []
        page = 1
        per_page = 30
        
        try:
            while len(contributors) < max_contributors:
                url = f"{self.base_url}/repos/{repo_full_name}/contributors"
                params = {
                    'page': page,
                    'per_page': min(per_page, max_contributors - len(contributors))
                }
                
                logger.info(f"Fetching contributors page {page} for {repo_full_name}")
                response = self.session.get(url, headers=self.headers, params=params)
                
                if self.handle_rate_limit(response):
                    response = self.session.get(url, headers=self.headers, params=params)
                
                response.raise_for_status()
                
                page_contributors = response.json()
                if not page_contributors:
                    break
                
                contributors.extend(page_contributors)
                page += 1
                
                # Маленькая задержка между запросами
                time.sleep(0.5)
            
            return contributors[:max_contributors]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching contributors for {repo_full_name}: {e}")
            return []
    
    def extract_all_data(self) -> List[Dict[str, Any]]:
        """Основной метод для извлечения всех данных"""
        all_repos_data = []
        
        for repo_name in REPOSITORIES:
            logger.info(f"Processing repository: {repo_name}")
            
            # Получаем основную информацию о репозитории
            repo_data = self.get_repository_data(repo_name)
            
            if repo_data:
                # Получаем контрибьюторов
                contributors = self.get_repo_contributors(repo_name)
                
                # Создаем структуру данных
                enriched_data = {
                    "repository": repo_data,
                    "contributors": contributors,
                    "extracted_at": datetime.now().isoformat(),
                    "metadata": {
                        "source": "GitHub API",
                        "version": "v3",
                        "authenticated": bool(self.token)
                    }
                }
                
                all_repos_data.append(enriched_data)
                logger.info(f"Successfully processed {repo_name}")
            
            # Задержка между репозиториями
            time.sleep(1)
        
        return all_repos_data

def main():
    """Основная функция"""
    logger.info("Starting GitHub data extraction")
    
    # Создаем экстрактор
    extractor = GitHubDataExtractor()
    
    # Проверяем rate limit
    rate_limit = extractor.check_rate_limit()
    if rate_limit:
        remaining = rate_limit.get('rate', {}).get('remaining', 0)
        logger.info(f"API Rate Limit remaining: {remaining}")
    
    # Извлекаем данные
    data = extractor.extract_all_data()
    
    if data:
        logger.info(f"Successfully extracted data for {len(data)} repositories")
        
        # Валидация данных
        validator = DataValidator()
        is_valid, errors = validator.validate_github_data(data)
        
        if is_valid:
            logger.info("Data validation passed")
            
            # Загружаем в S3
            uploader = S3Uploader()
            success = uploader.upload_data(data)
            
            if success:
                logger.info("Data successfully uploaded to S3")
            else:
                logger.error("Failed to upload data to S3")
        else:
            logger.error(f"Data validation failed: {errors}")
    else:
        logger.error("No data extracted")

if __name__ == "__main__":
    main()