#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import requests
import re
import time
import json
import argparse
import sys
from collections import Counter, defaultdict

print("Starting BGG test...")

# Simple test of the main components
def test_main_flow():
    print("1. Testing imports...")
    
    print("2. Testing BGG XML API...")
    url = "https://boardgamegeek.com/xmlapi2/plays?id=285774&page=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        plays = root.findall("play")
        print(f"   Found {len(plays)} plays")
        
        # Count June 2025 users
        june_users = set()
        for play in plays:
            play_date = play.get("date")
            userid = play.get("userid")
            if play_date and play_date.startswith("2025-06") and userid:
                june_users.add(userid)
        print(f"   June 2025 users: {len(june_users)}")
        
        if june_users:
            print(f"   Sample user: {list(june_users)[0]}")
            
            # Test fetching user plays
            sample_user = list(june_users)[0]
            print(f"3. Testing user plays API for user {sample_user}...")
            user_url = f"https://boardgamegeek.com/xmlapi2/plays?username={sample_user}&id=285774&page=1"
            user_response = requests.get(user_url, headers=headers, timeout=10)
            print(f"   User plays status: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_root = ET.fromstring(user_response.content)
                user_plays = user_root.findall("play")
                print(f"   User plays found: {len(user_plays)}")
                
                # Show sample play data
                if user_plays:
                    sample_play = user_plays[0]
                    print(f"   Sample play ID: {sample_play.get('id')}")
                    print(f"   Sample play date: {sample_play.get('date')}")
                    
                    players = sample_play.find("players")
                    if players is not None:
                        player_list = players.findall("player")
                        print(f"   Players in sample play: {len(player_list)}")
                        if player_list:
                            sample_player = player_list[0]
                            color = sample_player.get("color", "")
                            print(f"   Sample player color: '{color}'")
                    else:
                        print("   No players found in sample play")
    
    print("✅ Test completed!")

if __name__ == "__main__":
    test_main_flow()
