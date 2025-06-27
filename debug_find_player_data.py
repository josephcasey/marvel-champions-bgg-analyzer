#!/usr/bin/env python3
"""Find plays that actually have player data"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

import requests
import xml.etree.ElementTree as ET
from bggscrape import safe_api_call, colored_print, Colors

def find_plays_with_players():
    """Find plays that actually have player data"""
    
    colored_print("🔍 Searching for plays with player data...", Colors.CYAN)
    
    total_plays = 0
    plays_with_players = 0
    plays_with_color_data = 0
    
    try:
        for page in range(1, 6):  # Check first 5 pages
            colored_print(f"\n📄 Checking page {page}...", Colors.CYAN)
            
            url = f"https://boardgamegeek.com/xmlapi2/plays?id=285774&page={page}"
            response = safe_api_call(url)
            if response is None:
                continue
            
            root = ET.fromstring(response.content)
            plays = root.findall("play")
            
            page_total = len(plays)
            page_with_players = 0
            page_with_color = 0
            
            for play in plays:
                total_plays += 1
                play_id = play.get('id')
                userid = play.get('userid')
                
                players = play.find("players")
                if players is not None:
                    player_list = players.findall("player")
                    if player_list:
                        plays_with_players += 1
                        page_with_players += 1
                        
                        # Check if any players have color data
                        has_color = False
                        for player in player_list:
                            color = player.get("color", "").strip()
                            if color:
                                has_color = True
                                break
                        
                        if has_color:
                            plays_with_color_data += 1
                            page_with_color += 1
                            
                            # Show example of play with color data
                            if page_with_color <= 2:  # Show first 2 examples per page
                                colored_print(f"   ✅ Play {play_id} (User {userid}) has color data:", Colors.GREEN)
                                for j, player in enumerate(player_list):
                                    color = player.get("color", "").strip()
                                    if color:
                                        colored_print(f"      Player {j+1}: '{color}'", Colors.YELLOW)
            
            colored_print(f"   Page {page}: {page_total} plays, {page_with_players} with players, {page_with_color} with color data", Colors.CYAN)
        
        colored_print(f"\n📊 SUMMARY:", Colors.BOLD)
        colored_print(f"   Total plays checked: {total_plays}", Colors.CYAN)
        colored_print(f"   Plays with players element: {plays_with_players} ({plays_with_players/total_plays*100:.1f}%)", Colors.GREEN if plays_with_players > 0 else Colors.RED)
        colored_print(f"   Plays with color data: {plays_with_color_data} ({plays_with_color_data/total_plays*100:.1f}%)", Colors.GREEN if plays_with_color_data > 0 else Colors.RED)
        
        if plays_with_color_data == 0:
            colored_print(f"\n💡 INSIGHT: Recent Marvel Champions plays on BGG appear to lack detailed player/hero data", Colors.YELLOW)
            colored_print(f"   This explains why the analysis is showing mostly empty results", Colors.YELLOW)
            colored_print(f"   Users may be logging plays without specifying which heroes they used", Colors.YELLOW)
                    
    except Exception as e:
        colored_print(f"❌ Error: {e}", Colors.RED)

if __name__ == "__main__":
    find_plays_with_players()
