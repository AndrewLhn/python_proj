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
        """
        Валидация всех данных
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(data, list):
            errors.append("Data must be a list")
            return False, errors
        
        if len(data) == 0:
            errors.append("Data list is empty")
            return False, errors
        
        for i, item in enumerate(data):
            # Проверка структуры
            repo_errors = self._validate_repository_item(item, i)
            errors.extend(repo_errors)
            
            # Проверка контрибьюторов
            if 'contributors' in item:
                contributors_errors = self._validate_contributors(item['contributors'], i)
                errors.extend(contributors_errors)
            
            # Проверка метаданных
            if 'metadata' in item:
                metadata_errors = self._validate_metadata(item['metadata'], i)
                errors.extend(metadata_errors)
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info("All data quality checks passed")
        else:
            logger.warning(f"Data quality issues found: {len(errors)} errors")
        
        return is_valid, errors
    
    def _validate_repository_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """Валидация отдельного репозитория"""
        errors = []
        
        # Проверка наличия поля repository
        if 'repository' not in item:
            errors.append(f"Item {index}: Missing 'repository' field")
            return errors
        
        repo = item['repository']
        
        # Проверка обязательных полей
        for field in self.required_repo_fields:
            if field not in repo:
                errors.append(f"Item {index}: Missing required field '{field}' in repository")
        
        # Проверка типов данных
        if 'stargazers_count' in repo and not isinstance(repo['stargazers_count'], int):
            errors.append(f"Item {index}: 'stargazers_count' should be integer")
        
        if 'forks_count' in repo and not isinstance(repo['forks_count'], int):
            errors.append(f"Item {index}: 'forks_count' should be integer")
        
        # Проверка дат
        date_fields = ['created_at', 'updated_at', 'pushed_at']
        for field in date_fields:
            if field in repo:
                try:
                    datetime.fromisoformat(repo[field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    errors.append(f"Item {index}: '{field}' has invalid date format")
        
        return errors
    
    def _validate_contributors(self, contributors: List[Dict[str, Any]], index: int) -> List[str]:
        """Валидация контрибьюторов"""
        errors = []
        
        if not isinstance(contributors, list):
            errors.append(f"Item {index}: 'contributors' must be a list")
            return errors
        
        for j, contributor in enumerate(contributors):
            for field in self.required_contributor_fields:
                if field not in contributor:
                    errors.append(f"Item {index}, contributor {j}: Missing '{field}'")
            
            # Проверка, что contributions - число
            if 'contributions' in contributor and not isinstance(contributor['contributions'], int):
                errors.append(f"Item {index}, contributor {j}: 'contributions' must be integer")
        
        return errors
    
    def _validate_metadata(self, metadata: Dict[str, Any], index: int) -> List[str]:
        """Валидация метаданных"""
        errors = []
        
        if 'extracted_at' not in metadata and 'extracted_at' not in metadata:
            errors.append(f"Item {index}: Missing extraction timestamp")
        
        if 'source' in metadata and metadata['source'] != 'GitHub API':
            errors.append(f"Item {index}: Invalid data source")
        
        return errors
    
    def check_data_quality_rules(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Дополнительные проверки качества данных"""
        quality_report = {
            'total_repositories': len(data),
            'repos_with_description': 0,
            'repos_with_contributors': 0,
            'total_contributors': 0,
            'avg_stars': 0,
            'avg_forks': 0,
            'data_completeness': {}
        }
        
        total_stars = 0
        total_forks = 0
        
        for item in data:
            repo = item.get('repository', {})
            
            # Проверка описания
            if repo.get('description'):
                quality_report['repos_with_description'] += 1
            
            # Подсчет звезд и форков
            total_stars += repo.get('stargazers_count', 0)
            total_forks += repo.get('forks_count', 0)
            
            # Проверка контрибьюторов
            contributors = item.get('contributors', [])
            if contributors:
                quality_report['repos_with_contributors'] += 1
                quality_report['total_contributors'] += len(contributors)
        
        # Вычисление средних значений
        if data:
            quality_report['avg_stars'] = total_stars / len(data)
            quality_report['avg_forks'] = total_forks / len(data)
        
        # Процент заполненности
        quality_report['data_completeness'] = {
            'description': f"{(quality_report['repos_with_description']/len(data)*100):.1f}%" if data else "0%",
            'contributors': f"{(quality_report['repos_with_contributors']/len(data)*100):.1f}%" if data else "0%"
        }
        
        logger.info(f"Data Quality Report: {quality_report}")
        return quality_report