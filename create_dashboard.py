import json
import os
from datetime import datetime

def create_html_dashboard():
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print("No output directory found.")
        return
    
   
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print("No JSON files found.")
        return
    
    latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    file_path = os.path.join(output_dir, latest_file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
  
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Data Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f6f8fa;
            color: #24292e;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #0366d6;
        }}
        .stat-label {{
            color: #586069;
            margin-top: 8px;
        }}
        .repo-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .repo-name {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .repo-name a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .repo-stats {{
            display: flex;
            gap: 20px;
            margin: 15px 0;
            color: #586069;
        }}
        .contributor-list {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e1e4e8;
        }}
        .contributor {{
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            background: #f1f8ff;
            border-radius: 20px;
            font-size: 14px;
        }}
        .badge {{
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> GitHub Repositories Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Data source: GitHub API</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(data)}</div>
                <div class="stat-label">Repositories</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(len(item.get('contributors', [])) for item in data)}</div>
                <div class="stat-label">Total Contributors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(item['repository'].get('stargazers_count', 0) for item in data):,}</div>
                <div class="stat-label">Total Stars</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(item['repository'].get('forks_count', 0) for item in data):,}</div>
                <div class="stat-label">Total Forks</div>
            </div>
        </div>
"""
    
    for item in data:
        repo = item['repository']
        contributors = item.get('contributors', [])
        
        html_content += f"""
        <div class="repo-card">
            <div class="repo-name">
                <a href="{repo.get('html_url', '#')}" target="_blank">{repo.get('full_name', 'N/A')}</a>
            </div>
            <div class="repo-stats">
                <span> {repo.get('stargazers_count', 0):,}</span>
                <span> {repo.get('forks_count', 0):,}</span>
                <span> {repo.get('open_issues_count', 0)} issues</span>
                <span> {repo.get('language', 'N/A')}</span>
            </div>
            <div>{repo.get('description', 'No description')}</div>
            <div class="contributor-list">
                <strong>Top Contributors ({len(contributors)}):</strong><br>
"""
        
        for contributor in contributors[:10]:
            html_content += f"""
                <div class="contributor">
                    <a href="{contributor.get('html_url', '#')}" target="_blank">@{contributor.get('login', 'N/A')}</a>
                    <span class="badge">{contributor.get('contributions', 0)} commits</span>
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # Сохраняем HTML
    dashboard_file = f"output/dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f" Dashboard created: {dashboard_file}")
    print(f"   Open in browser: file://{os.path.abspath(dashboard_file)}")
    
    return dashboard_file

if __name__ == "__main__":
    create_html_dashboard()
