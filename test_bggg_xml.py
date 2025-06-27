#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import requests
import time

def test_bggg_xml_api():
    """Test the BGG XML API for Marvel Champions plays"""
    print("🔍 Testing BGG XML API for Marvel Champions plays...")
    
    # Test the XML API endpoint
    url = "https://boardgamegeek.com/xmlapi2/plays?id=285774&page=1"
    headers = {"User-Agent": "Mozilla/5.0 (BGG Marvel Champions Analyzer)"}
    
    try:
        print(f"📡 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"📄 Response length: {len(response.content)} bytes")
            
            # Parse XML
            root = ET.fromstring(response.content)
            plays = root.findall("play")
            
            print(f"🎮 Found {len(plays)} plays on page 1")
            
            # Show some sample plays
            june_2025_plays = 0
            for i, play in enumerate(plays[:10]):  # Show first 10
                play_id = play.get("id")
                play_date = play.get("date") 
                userid = play.get("userid")
                location = play.get("location", "")
                
                print(f"   Play {i+1}: ID={play_id}, Date={play_date}, User={userid}, Location={location[:30]}")
                
                if play_date and play_date.startswith("2025-06"):
                    june_2025_plays += 1
                    
            print(f"📊 Plays from June 2025: {june_2025_plays} out of first 10")
            
            # Test filtering for June 2025
            user_ids = set()
            for play in plays:
                play_date = play.get("date")
                userid = play.get("userid")
                
                if play_date and play_date.startswith("2025-06") and userid:
                    user_ids.add(userid)
                    
            print(f"👥 Unique users from June 2025 (page 1): {len(user_ids)}")
            if user_ids:
                print(f"   Sample user IDs: {list(user_ids)[:5]}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_bggg_xml_api()
