#!/usr/bin/env python3

import requests
import re

def test_fetch_monthly():
    """Test the monthly fetch function in isolation"""
    print("🔍 Testing BGG monthly stats fetch...")
    
    url = "https://boardgamegeek.com/playstats/thing/285774/2025-06"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"📡 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✅ Response status: {response.status_code}")
        
        html = response.text
        print(f"📄 HTML length: {len(html)} characters")
        
        # Test our regex patterns
        user_ids = set()
        usernames = set()

        # Stage 1: Find all avatarblock divs
        div_pattern = re.compile(r"<div[^>]*class=['\"]avatarblock js-avatar['\"][^>]*>", re.IGNORECASE)
        divs = div_pattern.finditer(html)
        found_blocks = list(divs)
        
        print(f"🔍 Found {len(found_blocks)} avatarblock divs")

        if found_blocks:
            for i, div_match in enumerate(found_blocks[:5]):  # Show first 5
                div_tag = div_match.group(0)
                print(f"   Div {i+1}: {div_tag[:100]}...")
                
                # Stage 2: Extract data-userid and data-username
                userid_match = re.search(r"data-userid=['\"](\d+)['\"]", div_tag)
                username_match = re.search(r"data-username=['\"]([^'\"]+)['\"]", div_tag)
                if userid_match:
                    user_ids.add(userid_match.group(1))
                    print(f"      → User ID: {userid_match.group(1)}")
                if username_match:
                    usernames.add(username_match.group(1))
                    print(f"      → Username: {username_match.group(1)}")
        else:
            print("❌ No avatarblock divs found, trying fallback...")
            # Fallback
            userid_matches = re.findall(r"data-userid=['\"](\d+)['\"]", html)
            username_matches = re.findall(r"data-username=['\"]([^'\"]+)['\"]", html)
            user_ids.update(userid_matches)
            usernames.update(username_matches)
            print(f"🔄 Fallback found {len(userid_matches)} user IDs, {len(username_matches)} usernames")

        print(f"📊 Final results:")
        print(f"   User IDs: {len(user_ids)} found")
        print(f"   Usernames: {len(usernames)} found")
        if user_ids:
            print(f"   Sample User IDs: {list(user_ids)[:5]}")
        if usernames:
            print(f"   Sample Usernames: {list(usernames)[:5]}")
            
        return list(user_ids), list(usernames)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

if __name__ == "__main__":
    test_fetch_monthly()
