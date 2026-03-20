import requests
import json
import logging
import time
import os
from datetime import datetime
from typing import List, Dict, Any
import sys

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
        logging.FileHandler(f'logs/github_extract_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
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
            "User-Agent": "Python-Data-Extractor/1.0"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
            logger.info("✅ Using authenticated GitHub API (higher rate limits)")
        else:
            logger.warning("⚠️  No token provided. Rate limit: 60 requests/hour")
            logger.info("💡 Get a token at: https://github.com/settings/tokens")
    
    def make_request(self, url: str, params: dict = None) -> Dict:
        """Универсальный метод для запросов с обработкой ошибок"""
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                current_time = time.time()
                wait_time = reset_time - current_time + 5
                
                if wait_time > 0 and wait_time < 3600:  # Не ждем больше часа
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                    response = self.session.get(url, headers=self.headers, params=params)
                else:
                    logger.error("Rate limit exceeded and no token provided")
                    return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_repository_data(self, repo_full_name: str) -> Dict[str, Any]:
        """Получение данных о репозитории"""
        url = f"{self.base_url}/repos/{repo_full_name}"
        logger.info(f"Fetching: {repo_full_name}")
        
        data = self.make_request(url)
        
        if data:
            logger.info(f"  ✓ Stars: {data.get('stargazers_count', 0)}, Forks: {data.get('forks_count', 0)}")
        else:
            logger.warning(f"  ✗ Failed to fetch {repo_full_name}")
        
        return data or {}
    
    def get_repo_contributors(self, repo_full_name: str, max_contributors: int = 10) -> List[Dict[str, Any]]:
        """Получение списка контрибьюторов"""
        contributors = []
        
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/contributors"
            params = {'per_page': min(max_contributors, 30)}
            
            data = self.make_request(url, params)
            
            if data and isinstance(data, list):
                contributors = data[:max_contributors]
                logger.info(f"  ✓ Found {len(contributors)} contributors")
            else:
                logger.info(f"  ℹ No contributors data available")
            
            return contributors
            
        except Exception as e:
            logger.error(f"Error fetching contributors: {e}")
            return []
    
    def extract_all_data(self) -> List[Dict[str, Any]]:
        """Основной метод для извлечения всех данных"""
        all_repos_data = []
        
        logger.info("=" * 60)
        logger.info(f"Starting extraction for {len(REPOSITORIES)} repositories")
        logger.info("=" * 60)
        
        for idx, repo_name in enumerate(REPOSITORIES, 1):
            logger.info(f"\n[{idx}/{len(REPOSITORIES)}] Processing: {repo_name}")
            
            # Получаем основную информацию о репозитории
            repo_data = self.get_repository_data(repo_name)
            
            if repo_data and 'id' in repo_data:
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
                        "authenticated": bool(self.token),
                        "extraction_timestamp": datetime.now().isoformat()
                    }
                }
                
                all_repos_data.append(enriched_data)
                logger.info(f"  ✅ Successfully processed")
            else:
                logger.warning(f"  ⚠️  Skipped - no data available")
            
            # Задержка между запросами
            if idx < len(REPOSITORIES):
                time.sleep(1)
        
        return all_repos_data

def main():
    """Основная функция"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 GitHub Data Extraction Tool")
    logger.info("=" * 60)
    
    # Создаем экстрактор
    extractor = GitHubDataExtractor()
    
    # Извлекаем данные
    data = extractor.extract_all_data()
    
    if data:
        logger.info(f"\n📊 Extraction Summary:")
        logger.info(f"  ✅ Successfully processed: {len(data)} repositories")
        
        # Валидация данных
        validator = DataValidator()
        is_valid, errors = validator.validate_github_data(data)
        
        if is_valid:
            logger.info("  ✅ Data validation passed")
            
            # Проверка качества данных
            quality_report = validator.check_data_quality_rules(data)
            logger.info(f"\n📈 Quality Report:")
            logger.info(f"  • Average stars: {quality_report['avg_stars']:.0f}")
            logger.info(f"  • Average forks: {quality_report['avg_forks']:.0f}")
            logger.info(f"  • Repos with description: {quality_report['repos_with_description']}/{quality_report['total_repositories']}")
            logger.info(f"  • Total contributors: {quality_report.get('total_contributors', 0)}")
            
            # Сохраняем данные
            uploader = S3Uploader()
            success = uploader.upload_data(data)
            
            if success:
                logger.info("\n✅ Data successfully saved to output/")
                logger.info("💡 Check the output directory for JSON files")
            else:
                logger.error("\n❌ Failed to save data")
        else:
            logger.error(f"\n❌ Data validation failed with {len(errors)} errors:")
            for error in errors[:5]:  # Показываем первые 5 ошибок
                logger.error(f"  • {error}")
    else:
        logger.error("\n❌ No data extracted. Check your internet connection and GitHub token.")
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Extraction completed!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
