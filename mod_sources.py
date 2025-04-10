#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API client for the Modrinth mod repository.
"""

import json
import requests
from datetime import datetime

class ModrinthClient:
    """Client for the Modrinth API."""
    API_BASE = "https://api.modrinth.com/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Project-Launcher-Server/1.0"
        })
    
    def search_mods(self, query, minecraft_version=None, modloader=None, limit=20):
        """Search for mods from Modrinth."""
        try:
            params = {
                'query': query,
                'limit': limit,
                'index': 'relevance',
                'facets': json.dumps([
                    ["project_types:mod"], 
                    # Filter just for mods
                ])
            }
            
            # Build a filter string
            filters = []
            if minecraft_version:
                filters.append(f"game_versions:{minecraft_version}")
                
            if modloader:
                # Adding modloader as a game_versions filter instead of using "loader"
                filters.append(f"game_versions:{modloader}")
                
            if filters:
                params['filter'] = ' AND '.join(filters)
            
            print(f"Search params: {params}")
            response = self.session.get(f"{self.API_BASE}/search", params=params)
            
            if response.status_code != 200:
                print(f"Error in search: {response.text}")
                return []
                
            data = response.json()
            hits = data.get('hits', [])
            
            # Format the results
            return [{
                'id': mod['project_id'],
                'name': mod['title'],
                'author': mod.get('author', ''),
                'description': mod.get('description', ''),
                'downloads': mod.get('downloads', 0),
                'icon_url': mod.get('icon_url'),
                'page_url': f"https://modrinth.com/mod/{mod['project_id']}"
            } for mod in hits]
        except Exception as e:
            print(f"Error searching mods: {str(e)}")
            return []
    
    def get_mod_versions(self, mod_id, minecraft_version=None, modloader=None):
        """Get versions of a mod."""
        try:
            params = {}
            if minecraft_version:
                params["game_versions"] = [minecraft_version]
            
            # Add modloader as a game version
            if modloader:
                if "game_versions" not in params:
                    params["game_versions"] = []
                params["game_versions"].append(modloader)
                
            response = self.session.get(f"{self.API_BASE}/project/{mod_id}/version", params=params)
            if response.status_code == 200:
                versions = response.json()
                return [{
                    'id': version['id'],
                    'version_number': version['version_number'],
                    'name': version['name'],
                    'changelog': version.get('changelog', ''),
                    'date_published': version['date_published'],
                    'game_versions': version['game_versions'],
                    'files': [{
                        'url': file['url'],
                        'filename': file['filename'],
                        'size': file['size'],
                        'primary': file.get('primary', False)
                    } for file in version['files']]
                } for version in versions]
            else:
                print(f"Error getting mod versions: {response.text}")
                return []
        except Exception as e:
            print(f"Error getting mod versions: {str(e)}")
            return []
    
    def download_mod(self, version_id, download_path):
        """Download a specific mod version."""
        try:
            # Get version details
            response = self.session.get(f"{self.API_BASE}/version/{version_id}")
            if response.status_code != 200:
                print(f"Error getting version: {response.text}")
                return False
                
            version = response.json()
            primary_file = next((file for file in version['files'] if file.get('primary', True)), version['files'][0])
            
            # Download the file
            file_response = self.session.get(primary_file['url'], stream=True)
            if file_response.status_code == 200:
                print(f"Downloading mod to {download_path}")
                with open(download_path, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"Error downloading file: {file_response.text}")
                return False
        except Exception as e:
            print(f"Error downloading mod: {str(e)}")
            return False

    def get_popular_mods(self, minecraft_version=None, modloader=None, limit=20):
        """Get popular mods from Modrinth."""
        try:
            params = {
                'limit': limit,
                'index': 'downloads',
                'facets': json.dumps([
                    ["project_types:mod"], 
                    # Use project_types=mod to filter just mods
                ])
            }
            
            # Build a filter string
            filters = []
            if minecraft_version:
                filters.append(f"game_versions:{minecraft_version}")
            
            if modloader:
                # Adding modloader as a game_versions filter instead of "loader"
                filters.append(f"game_versions:{modloader}")
                
            if filters:
                params['filter'] = ' AND '.join(filters)
            
            print(f"Making Modrinth request with params: {params}")
            response = self.session.get(f"{self.API_BASE}/search", params=params)
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []
                
            data = response.json()
            hits = data.get('hits', [])
            print(f"Found {len(hits)} popular mods")
            
            # Format the results
            return [{
                'id': mod['project_id'],
                'name': mod['title'],
                'author': mod.get('author', ''),
                'description': mod.get('description', ''),
                'downloads': mod.get('downloads', 0),
                'icon_url': mod.get('icon_url'),
                'page_url': f"https://modrinth.com/mod/{mod['project_id']}"
            } for mod in hits]
        except Exception as e:
            print(f"Error fetching popular mods: {str(e)}")
            return []

if __name__ == "__main__":
    # Simple test to verify functionality 
    client = ModrinthClient()
    print("Testing Modrinth API...")
    results = client.search_mods("fabric", "1.20.1", limit=5)
    print(f"Found {len(results)} mods:")
    for result in results:
        print(f"- {result['name']} by {result['author']} ({result['downloads']} downloads)")