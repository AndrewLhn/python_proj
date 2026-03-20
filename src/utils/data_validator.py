import logging
from typing import Tuple, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        self.required_repo_fields = [
            'id', 'name', 'full_name', 'html_url',
            'description', 'created_at', 'updated_at',
            'stargazers_count', 'forks_count', 'open_issues_count'
        ]
        
        self.required_contributor_fields = [
            'login', 'id', 'contributions'
        ]
    
    def validate_github_data(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Валидация всех данных"""
        errors = []
        
        if not isinstance(data, list):
            errors.append("Data must be a list")
            return False, errors
        
        if len(data) == 0:
            errors.append("Data list is empty")
            return False, errors
        
        for i, item in enumerate(data):
            # Проверка структуры
            if 'repository' not in item:
                errors.append(f"Item {i}: Missing 'repository' field")
                continue
            
            # Проверка extracted_at (может быть в корне или в metadata)
            if 'extracted_at' not in item:
                if 'metadata' in item and 'extracted_at' in item['metadata']:
                    # Все хорошо, timestamp в metadata
                    pass
                else:
                    errors.append(f"Item {i}: Missing extraction timestamp")
            
            repo = item.get('repository', {})
            
            # Проверяем наличие id (минимальная проверка)
            if 'id' not in repo:
                errors.append(f"Item {i}: Missing repository id")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info("All data quality checks passed")
        else:
            logger.warning(f"Data quality issues found: {len(errors)} errors")
        
        return is_valid, errors
    
    def check_data_quality_rules(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Проверки качества данных"""
        quality_report = {
            'total_repositories': len(data),
            'repos_with_description': 0,
            'repos_with_contributors': 0,
            'total_contributors': 0,
            'avg_stars': 0,
            'avg_forks': 0,
        }
        
        total_stars = 0
        total_forks = 0
        
        for item in data:
            repo = item.get('repository', {})
            
            if repo.get('description'):
                quality_report['repos_with_description'] += 1
            
            # Проверяем наличие контрибьюторов
            contributors = item.get('contributors', [])
            if contributors:
                quality_report['repos_with_contributors'] += 1
                quality_report['total_contributors'] += len(contributors)
            
            total_stars += repo.get('stargazers_count', 0)
            total_forks += repo.get('forks_count', 0)
        
        if data:
            quality_report['avg_stars'] = total_stars / len(data)
            quality_report['avg_forks'] = total_forks / len(data)
        
        logger.info(f"Data Quality Report: {quality_report}")
        return quality_report
