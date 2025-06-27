#!/usr/bin/env python3
"""Test different BGG API approaches to get user-specific data"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

import requests
import xml.etree.ElementTree as ET
from bggscrape import safe_api_call, colored_print, Colors
import time

def test_api_approaches():
    """Test different ways to get user-specific plays from BGG API"""
    
    test_user = "3654065"
    colored_print(f"\n🔍 Testing different API approaches for user: {test_user}", Colors.CYAN)
    
    # Approach 1: User-specific API without game filter
    colored_print(f"\n1️⃣ Testing user-specific API WITHOUT game filter:", Colors.YELLOW)
    url1 = f"https://boardgamegeek.com/xmlapi2/plays?username={test_user}"
    colored_print(f"🌐 URL: {url1}", Colors.CYAN)
    
    try:
        response1 = safe_api_call(url1)
        if response1:
            root1 = ET.fromstring(response1.content)
            plays1 = root1.findall("play")
            colored_print(f"📊 Found {len(plays1)} total plays for user", Colors.GREEN)
            
            # Count Marvel Champions plays
            mc_plays = []
            for play in plays1:
                items = play.findall(".//item")
                for item in items:
                    if item.get("objectid") == "285774":
                        mc_plays.append(play)
                        break
            
            colored_print(f"🎮 Marvel Champions plays: {len(mc_plays)}", Colors.GREEN)
            
            if mc_plays:
                first_mc_play = mc_plays[0]
                play_id = first_mc_play.get('id')
                userid_attr = first_mc_play.get('userid')
                date = first_mc_play.get('date')
                colored_print(f"   First MC play: ID={play_id}, UserID={userid_attr}, Date={date}", Colors.CYAN)
                
                if userid_attr == test_user:
                    colored_print(f"   ✅ User ID matches!", Colors.GREEN)
                else:
                    colored_print(f"   ⚠️  User ID mismatch: expected {test_user}, got {userid_attr}", Colors.RED)
        
        time.sleep(2)
    except Exception as e:
        colored_print(f"❌ Error with approach 1: {e}", Colors.RED)
    
    # Approach 2: Try with username instead of userid
    # First we need to find the username for this userid
    colored_print(f"\n2️⃣ Testing with username instead of userid:", Colors.YELLOW)
    colored_print(f"   (This would require looking up the username first)", Colors.CYAN)
    
    # Approach 3: Get all recent plays and filter client-side
    colored_print(f"\n3️⃣ Current approach (all recent plays, filter client-side):", Colors.YELLOW)
    url3 = f"https://boardgamegeek.com/xmlapi2/plays?id=285774&page=1"
    colored_print(f"🌐 URL: {url3}", Colors.CYAN)
    
    try:
        time.sleep(2)
        response3 = safe_api_call(url3)
        if response3:
            root3 = ET.fromstring(response3.content)
            plays3 = root3.findall("play")
            colored_print(f"📊 Found {len(plays3)} recent Marvel Champions plays", Colors.GREEN)
            
            # Filter for our test user
            user_plays = [play for play in plays3 if play.get('userid') == test_user]
            colored_print(f"🎯 Plays by user {test_user}: {len(user_plays)}", Colors.GREEN)
            
            if user_plays:
                first_user_play = user_plays[0]
                play_id = first_user_play.get('id')
                date = first_user_play.get('date')
                colored_print(f"   First user play: ID={play_id}, Date={date}", Colors.CYAN)
            else:
                colored_print(f"   ❌ No plays found for user {test_user} in recent plays", Colors.RED)
                colored_print(f"   💡 This explains why we need a different approach!", Colors.YELLOW)
                
                # Show which users ARE in the recent plays
                unique_users = set()
                for play in plays3[:10]:  # Check first 10 plays
                    userid = play.get('userid')
                    if userid:
                        unique_users.add(userid)
                        
                colored_print(f"   📊 Users found in recent 10 plays: {sorted(unique_users)}", Colors.CYAN)
        
    except Exception as e:
        colored_print(f"❌ Error with approach 3: {e}", Colors.RED)

if __name__ == "__main__":
    test_api_approaches()
