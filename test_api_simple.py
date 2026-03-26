#!/usr/bin/env python3
"""
Simple API Test using curl
Tests Jira and Confluence API connectivity with real tokens
"""

import os
import subprocess
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_api_with_curl():
    """Test APIs using curl commands."""
    print("🏥 API Health Test with curl")
    print("=" * 40)
    
    # Get environment variables
    jira_token = os.getenv("JIRA_ACCESS_TOKEN")
    confluence_token = os.getenv("CONFLUENCE_ACCESS_TOKEN")
    jira_url = os.getenv("JIRA_BASE_URL")
    confluence_url = os.getenv("CONFLUENCE_BASE_URL")
    
    if not jira_token:
        print("❌ JIRA_ACCESS_TOKEN not set in .env")
        return
    
    if not confluence_token:
        print("❌ CONFLUENCE_ACCESS_TOKEN not set in .env")
        return
    
    if not jira_url:
        print("❌ JIRA_BASE_URL not set in .env")
        return
        
    if not confluence_url:
        print("❌ CONFLUENCE_BASE_URL not set in .env")
        return
    
    print("✅ Environment variables found")
    print(f"   Jira URL: {jira_url}")
    print(f"   Confluence URL: {confluence_url}")
    
    # Test Jira API
    print("\n🔍 Testing Jira API...")
    try:
        # Test Jira REST API endpoint with authentication
        jira_api_url = f'{jira_url.rstrip("/")}/rest/api/2/project'
        cmd = [
            'curl', '-s', '-k', '-L', '-w', '%{http_code}',
            '-H', f'Authorization: Bearer {jira_token}',
            '-H', 'Content-Type: application/json',
            jira_api_url
        ]
        
        print(f"   Testing URL: {jira_api_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout[:200]}...")
        print(f"   Stderr: {result.stderr[:200]}...")
        
        if result.returncode == 0:
            # Extract status code from last 3 characters
            status_code = result.stdout[-3:]
            response_body = result.stdout[:-3]
            
            print(f"   Status Code: {status_code}")
            
            if status_code == '200':
                print("   ✅ Jira API is working!")
                try:
                    projects = json.loads(response_body)
                    if isinstance(projects, list) and len(projects) > 0:
                        print(f"   📊 Found {len(projects)} projects")
                        print(f"   📋 First project: {projects[0].get('key', 'Unknown')}")
                except:
                    print("   📊 Response received (projects data)")
            elif status_code == '401':
                print("   ❌ Authentication failed - invalid token")
            elif status_code == '403':
                print("   ❌ Access forbidden - insufficient permissions")
            elif status_code == '404':
                print("   ❌ Endpoint not found - check URL")
            else:
                print(f"   ❌ Unexpected status: {status_code}")
                if response_body:
                    print(f"   Response: {response_body[:200]}...")
        else:
            print(f"   ❌ Curl command failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("   ❌ Request timeout")
    except Exception as e:
        print(f"   ❌ Jira test failed: {e}")
    
    # Test Confluence API
    print("\n🔍 Testing Confluence API...")
    try:
        # Test Confluence REST API endpoint with authentication
        confluence_api_url = f'{confluence_url.rstrip("/")}/rest/api/space'
        cmd = [
            'curl', '-s', '-k', '-L', '-w', '%{http_code}',
            '-H', f'Authorization: Bearer {confluence_token}',
            '-H', 'Content-Type: application/json',
            confluence_api_url
        ]
        
        print(f"   Testing URL: {confluence_api_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout[:200]}...")
        print(f"   Stderr: {result.stderr[:200]}...")
        
        if result.returncode == 0:
            # Extract status code from last 3 characters
            status_code = result.stdout[-3:]
            response_body = result.stdout[:-3]
            
            print(f"   Status Code: {status_code}")
            
            if status_code == '200':
                print("   ✅ Confluence API is working!")
                try:
                    spaces = json.loads(response_body)
                    if 'results' in spaces and len(spaces['results']) > 0:
                        print(f"   📊 Found {len(spaces['results'])} spaces")
                        print(f"   📋 First space: {spaces['results'][0].get('key', 'Unknown')}")
                except:
                    print("   📊 Response received (spaces data)")
            elif status_code == '401':
                print("   ❌ Authentication failed - invalid token")
            elif status_code == '403':
                print("   ❌ Access forbidden - insufficient permissions")
            elif status_code == '404':
                print("   ❌ Endpoint not found - check URL")
            else:
                print(f"   ❌ Unexpected status: {status_code}")
                if response_body:
                    print(f"   Response: {response_body[:200]}...")
        else:
            print(f"   ❌ Curl command failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("   ❌ Request timeout")
    except Exception as e:
        print(f"   ❌ Confluence test failed: {e}")
    
    print("\n📊 Summary:")
    print("   Tests completed. Check results above.")
    print("\n💡 Tips:")
    print("   - If you see 401 errors, check your tokens")
    print("   - If you see 404 errors, check the URLs")
    print("   - If you see 403 errors, check permissions")

if __name__ == "__main__":
    test_api_with_curl()
