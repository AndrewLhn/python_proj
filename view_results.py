import json
import os
from datetime import datetime

def view_latest_data():
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print("No output directory found. Run extract_github_data.py first.")
        return
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found in output/")
        return
    
    latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    file_path = os.path.join(output_dir, latest_file)
    
    print(f"\n Reading: {latest_file}")
    print(f" Modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
    print("=" * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n Total repositories: {len(data)}")
    print("\n Repository Summary:")
    print("-" * 60)
    
    for i, item in enumerate(data, 1):
        repo = item.get('repository', {})
        contributors = item.get('contributors', [])
        
        print(f"\n{i}. {repo.get('full_name', 'N/A')}")
        print(f"    Stars: {repo.get('stargazers_count', 0):,}")
        print(f"    Forks: {repo.get('forks_count', 0):,}")
        print(f"    Description: {repo.get('description', 'N/A')[:80]}...")
        print(f"    Contributors: {len(contributors)}")
        
      
        if contributors:
            print(f"   Top contributors:")
            for j, contributor in enumerate(contributors[:3], 1):
                print(f"     {j}. {contributor.get('login', 'N/A')} - {contributor.get('contributions', 0)} commits")
    
    print("\n" + "=" * 60)
    print(f" Full data saved in: {file_path}")

if __name__ == "__main__":
    view_latest_data()
