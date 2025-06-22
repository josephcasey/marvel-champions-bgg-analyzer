#!/usr/bin/env python3
"""
Cross-Repository Analyzer for Marvel Champions BGG Project
Analyzes relationships between main project and agent-rules repositories
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class CrossRepoAnalyzer:
    def __init__(self, github_token: str = None):
        """Initialize with optional GitHub token for API access"""
        self.github_token = github_token
        self.session = requests.Session()
        if github_token:
            self.session.headers.update({'Authorization': f'token {github_token}'})
        
        # Repository configurations
        self.repos = {
            'main': {
                'owner': 'josephcasey',
                'name': 'marvel-champions-bgg-analyzer',
                'path': '/Users/jo/globalbggchamps'
            },
            'agent_rules': {
                'owner': 'steipete',
                'name': 'agent-rules',
                'path': '/Users/jo/globalbggchamps/agent-rules'
            }
        }
    
    def get_repo_info(self, repo_key: str) -> Dict[str, Any]:
        """Get repository information from GitHub API"""
        repo = self.repos[repo_key]
        url = f"https://api.github.com/repos/{repo['owner']}/{repo['name']}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error fetching {repo_key} repo info: {e}")
            return {}
    
    def get_recent_commits(self, repo_key: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent commits from a repository"""
        repo = self.repos[repo_key]
        url = f"https://api.github.com/repos/{repo['owner']}/{repo['name']}/commits"
        
        try:
            response = self.session.get(url, params={'per_page': count})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error fetching {repo_key} commits: {e}")
            return []
    
    def analyze_deployment_consistency(self) -> Dict[str, Any]:
        """Analyze consistency between deployment docs and actual scripts"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'deployment_workflow_analysis': {},
            'consistency_issues': [],
            'recommendations': []
        }
        
        # Check if deploy.mdc exists in agent-rules
        deploy_mdc_path = f"{self.repos['agent_rules']['path']}/project-rules/deploy.mdc"
        deploy_script_path = f"{self.repos['main']['path']}/scripts/deploy-changes.sh"
        
        deploy_mdc_exists = os.path.exists(deploy_mdc_path)
        deploy_script_exists = os.path.exists(deploy_script_path)
        
        analysis['deployment_workflow_analysis'] = {
            'deploy_mdc_exists': deploy_mdc_exists,
            'deploy_script_exists': deploy_script_exists,
            'both_exist': deploy_mdc_exists and deploy_script_exists
        }
        
        # Analyze consistency if both exist
        if deploy_mdc_exists and deploy_script_exists:
            try:
                with open(deploy_mdc_path, 'r') as f:
                    deploy_mdc_content = f.read()
                
                with open(deploy_script_path, 'r') as f:
                    deploy_script_content = f.read()
                
                # Check if README update is mentioned in both
                readme_in_mdc = 'README' in deploy_mdc_content.upper()
                readme_in_script = 'README' in deploy_script_content.upper()
                
                if readme_in_mdc and not readme_in_script:
                    analysis['consistency_issues'].append(
                        "deploy.mdc mentions README updates but deploy-changes.sh doesn't implement them"
                    )
                    analysis['recommendations'].append(
                        "Consider adding README update functionality to deploy-changes.sh or make it a manual step with clear guidance"
                    )
                
            except Exception as e:
                analysis['consistency_issues'].append(f"Error reading deployment files: {e}")
        
        return analysis
    
    def analyze_repo_relationship(self) -> Dict[str, Any]:
        """Analyze the relationship between both repositories"""
        print("🔍 Analyzing repository relationship...")
        
        # Get basic repo info
        main_info = self.get_repo_info('main')
        agent_rules_info = self.get_repo_info('agent_rules')
        
        # Get recent commits
        main_commits = self.get_recent_commits('main', 3)
        agent_rules_commits = self.get_recent_commits('agent_rules', 3)
        
        # Analyze deployment consistency
        deployment_analysis = self.analyze_deployment_consistency()
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'repositories': {
                'main': {
                    'full_name': main_info.get('full_name', 'N/A'),
                    'description': main_info.get('description', 'N/A'),
                    'last_updated': main_info.get('updated_at', 'N/A'),
                    'recent_commits': [
                        {
                            'sha': commit['sha'][:7],
                            'message': commit['commit']['message'],
                            'date': commit['commit']['author']['date']
                        }
                        for commit in main_commits
                    ]
                },
                'agent_rules': {
                    'full_name': agent_rules_info.get('full_name', 'N/A'),
                    'description': agent_rules_info.get('description', 'N/A'),
                    'last_updated': agent_rules_info.get('updated_at', 'N/A'),
                    'recent_commits': [
                        {
                            'sha': commit['sha'][:7],
                            'message': commit['commit']['message'],
                            'date': commit['commit']['author']['date']
                        }
                        for commit in agent_rules_commits
                    ]
                }
            },
            'deployment_analysis': deployment_analysis,
            'recommendations': [
                "Consider creating a unified deployment workflow that handles both repositories",
                "Set up GitHub Actions to sync deployment documentation",
                "Create a script to validate consistency between deploy.mdc and actual scripts"
            ]
        }
        
        return analysis
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print a formatted analysis report"""
        print("\n" + "="*80)
        print("📊 CROSS-REPOSITORY ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📅 Analysis Time: {analysis['timestamp']}")
        
        print("\n🏠 REPOSITORY INFORMATION:")
        for repo_key, repo_data in analysis['repositories'].items():
            print(f"\n  📁 {repo_key.replace('_', ' ').title()}:")
            print(f"     Name: {repo_data['full_name']}")
            print(f"     Description: {repo_data['description']}")
            print(f"     Last Updated: {repo_data['last_updated']}")
            
            print(f"     Recent Commits:")
            for commit in repo_data['recent_commits']:
                print(f"       • {commit['sha']} - {commit['message'][:60]}...")
        
        print("\n🚀 DEPLOYMENT WORKFLOW ANALYSIS:")
        deploy_analysis = analysis['deployment_analysis']['deployment_workflow_analysis']
        print(f"     deploy.mdc exists: {'✅' if deploy_analysis['deploy_mdc_exists'] else '❌'}")
        print(f"     deploy-changes.sh exists: {'✅' if deploy_analysis['deploy_script_exists'] else '❌'}")
        print(f"     Both files exist: {'✅' if deploy_analysis['both_exist'] else '❌'}")
        
        if analysis['deployment_analysis']['consistency_issues']:
            print("\n⚠️  CONSISTENCY ISSUES:")
            for issue in analysis['deployment_analysis']['consistency_issues']:
                print(f"     • {issue}")
        
        print("\n💡 RECOMMENDATIONS:")
        all_recommendations = (
            analysis['deployment_analysis'].get('recommendations', []) +
            analysis.get('recommendations', [])
        )
        for rec in all_recommendations:
            print(f"     • {rec}")
        
        print("\n" + "="*80)

def main():
    """Main function to run the cross-repository analysis"""
    print("🚀 Marvel Champions BGG Cross-Repository Analyzer")
    print("Analyzing relationships between main project and agent-rules...")
    
    # Initialize analyzer (GitHub token optional for public repos)
    analyzer = CrossRepoAnalyzer()
    
    # Run analysis
    analysis = analyzer.analyze_repo_relationship()
    
    # Print report
    analyzer.print_analysis_report(analysis)
    
    # Save analysis to file
    output_file = '/Users/jo/globalbggchamps/cross_repo_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n📄 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()
