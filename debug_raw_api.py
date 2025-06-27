#!/usr/bin/env python3
"""Debug script to examine raw BGG API responses for different user IDs"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

import requests
import xml.etree.ElementTree as ET
from bggscrape import safe_api_call, colored_print, Colors
import time

def debug_raw_api():
    """Examine raw BGG API responses to understand the issue"""
    
    test_users = ["3654065", "2827562"]
    
    for user_id in test_users:
        colored_print(f"\n🔍 Testing raw API for user ID: {user_id}", Colors.CYAN)
        
        url = f"https://boardgamegeek.com/xmlapi2/plays?userid={user_id}&id=285774&page=1"
        colored_print(f"🌐 URL: {url}", Colors.YELLOW)
        
        try:
            response = safe_api_call(url)
            if response is None:
                colored_print(f"❌ Failed to get response", Colors.RED)
                continue
                
            # Parse and examine the response
            root = ET.fromstring(response.content)
            plays = root.findall("play")
            
            colored_print(f"📊 Found {len(plays)} plays in response", Colors.GREEN)
            
            if plays:
                # Examine first few plays
                for i, play in enumerate(plays[:3]):
                    play_id = play.get('id')
                    play_date = play.get('date')
                    userid_attr = play.get('userid')
                    
                    colored_print(f"   Play {i+1}: ID={play_id}, Date={play_date}, UserID={userid_attr}", Colors.CYAN)
                    
                    # Check if userid matches our request
                    if userid_attr != user_id:
                        colored_print(f"   ⚠️  MISMATCH: Requested {user_id}, got {userid_attr}", Colors.RED)
                    else:
                        colored_print(f"   ✅ Match: {userid_attr}", Colors.GREEN)
                        
                    # Check game info
                    items = play.findall(".//item")
                    for item in items:
                        game_id = item.get('objectid')
                        game_name = item.get('name')
                        colored_print(f"   Game: ID={game_id}, Name={game_name}", Colors.YELLOW)
                        
            # Let's also check what happens if we don't specify a userid
            colored_print(f"\n🔍 Testing without userid filter (should show recent plays from all users):", Colors.CYAN)
            url_no_user = f"https://boardgamegeek.com/xmlapi2/plays?id=285774&page=1"
            colored_print(f"🌐 URL: {url_no_user}", Colors.YELLOW)
            
            time.sleep(2)  # Delay between requests
            response2 = safe_api_call(url_no_user)
            if response2:
                root2 = ET.fromstring(response2.content)
                plays2 = root2.findall("play")
                colored_print(f"📊 Found {len(plays2)} plays WITHOUT userid filter", Colors.GREEN)
                
                if plays2:
                    first_play_no_filter = plays2[0]
                    play_id_no_filter = first_play_no_filter.get('id')
                    userid_no_filter = first_play_no_filter.get('userid')
                    colored_print(f"   First play without filter: ID={play_id_no_filter}, UserID={userid_no_filter}", Colors.CYAN)
                    
                    # Compare: is the first play the same with and without userid filter?
                    first_play_with_filter = plays[0] if plays else None
                    if first_play_with_filter:
                        play_id_with_filter = first_play_with_filter.get('id')
                        if play_id_with_filter == play_id_no_filter:
                            colored_print(f"   🚨 PROBLEM: Same play ID returned with and without userid filter!", Colors.RED)
                            colored_print(f"   🚨 This suggests the userid parameter is being ignored!", Colors.RED)
                        else:
                            colored_print(f"   ✅ Different plays returned (userid filter working)", Colors.GREEN)
                            
        except Exception as e:
            colored_print(f"❌ Error: {e}", Colors.RED)

if __name__ == "__main__":
    debug_raw_api()
