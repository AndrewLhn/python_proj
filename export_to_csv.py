import json
import csv
import os
from datetime import datetime

def export_to_csv():
    """Экспорт данных в CSV формат"""
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print("No output directory found.")
        return
    
    # Находим последний JSON файл
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print("No JSON files found.")
        return
    
    latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    file_path = os.path.join(output_dir, latest_file)
    
    print(f"Reading data from: {latest_file}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # CSV файл для репозиториев
    csv_file = f"output/repositories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Repository', 'Stars', 'Forks', 'Open Issues', 
            'Language', 'Created At', 'Updated At',
            'Contributors Count', 'Description'
        ])
        
        for item in data:
            repo = item['repository']
            writer.writerow([
                repo.get('full_name', ''),
                repo.get('stargazers_count', 0),
                repo.get('forks_count', 0),
                repo.get('open_issues_count', 0),
                repo.get('language', ''),
                repo.get('created_at', ''),
                repo.get('updated_at', ''),
                len(item.get('contributors', [])),
                repo.get('description', '')[:100]  # Ограничиваем длину
            ])
    
    print(f"✅ Exported to CSV: {csv_file}")
    
    # CSV файл для контрибьюторов
    contributors_file = f"output/contributors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(contributors_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Repository', 'Contributor', 'Contributions', 'GitHub Profile'])
        
        for item in data:
            repo_name = item['repository']['full_name']
            for contributor in item.get('contributors', []):
                writer.writerow([
                    repo_name,
                    contributor.get('login', ''),
                    contributor.get('contributions', 0),
                    contributor.get('html_url', '')
                ])
    
    print(f"✅ Exported contributors to: {contributors_file}")
    print(f"\n📊 Summary:")
    print(f"  • Repositories: {len(data)}")
    print(f"  • Total contributors: {sum(len(item.get('contributors', [])) for item in data)}")
    
if __name__ == "__main__":
    export_to_csv()
