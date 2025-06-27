#!/usr/bin/env python3
"""Debug the actual color field values"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

import requests
import xml.etree.ElementTree as ET
from bggscrape import safe_api_call, colored_print, Colors

def debug_color_fields():
    """Debug what's actually in the color fields of recent plays"""
    
    colored_print("🔍 Fetching recent plays to debug color fields...", Colors.CYAN)
    
    try:
        url = "https://boardgamegeek.com/xmlapi2/plays?id=285774&page=1"
        response = safe_api_call(url)
        if response is None:
            colored_print("❌ Failed to fetch plays", Colors.RED)
            return
        
        root = ET.fromstring(response.content)
        plays = root.findall("play")
        
        colored_print(f"📊 Found {len(plays)} plays", Colors.GREEN)
        
        # Look at first few plays and their player color fields
        for i, play in enumerate(plays[:5]):
            play_id = play.get('id')
            userid = play.get('userid')
            colored_print(f"\n🎯 Play {i+1}: ID={play_id}, User={userid}", Colors.CYAN)
            
            players = play.find("players")
            if players is None:
                colored_print(f"   ❌ No players element", Colors.RED)
                continue
                
            player_list = players.findall("player")
            if not player_list:
                colored_print(f"   ❌ No player list", Colors.RED)
                continue
                
            for j, player in enumerate(player_list):
                # Get raw color attribute
                color_raw = player.get("color")
                color_stripped = player.get("color", "").strip()
                
                colored_print(f"     Player {j+1}:", Colors.YELLOW)
                colored_print(f"       Raw color: {repr(color_raw)}", Colors.CYAN)
                colored_print(f"       Stripped: {repr(color_stripped)}", Colors.CYAN)
                colored_print(f"       Is empty check: {not color_stripped}", Colors.CYAN)
                colored_print(f"       Length: {len(color_stripped) if color_stripped else 0}", Colors.CYAN)
                
                if color_stripped:
                    colored_print(f"       ✅ Non-empty color field", Colors.GREEN)
                else:
                    colored_print(f"       ❌ Empty color field", Colors.RED)
                    
    except Exception as e:
        colored_print(f"❌ Error: {e}", Colors.RED)

if __name__ == "__main__":
    debug_color_fields()
