#!/usr/bin/env python3
"""Debug script to verify that different user IDs return different data from BGG API"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

from bggscrape import fetch_user_plays_by_userid_direct, colored_print, Colors

def debug_api_data():
    """Test fetching data for different users to see if we get unique data"""
    
    # Test with a small sample of different user IDs
    test_users = ["3654065", "2827562", "1234567"]  # Mix of real and potentially fake IDs
    
    for user_id in test_users:
        colored_print(f"\n🔍 Testing user ID: {user_id}", Colors.CYAN)
        
        try:
            plays = fetch_user_plays_by_userid_direct(user_id, max_plays=3)
            
            if plays:
                colored_print(f"✅ Found {len(plays)} plays for user {user_id}", Colors.GREEN)
                
                # Show details of first play to verify uniqueness
                first_play = plays[0]
                play_id = first_play.get('id')
                play_date = first_play.get('date')
                userid_attr = first_play.get('userid')
                
                colored_print(f"   First play: ID={play_id}, Date={play_date}, UserID attr={userid_attr}", Colors.YELLOW)
                
                # Check if the userid attribute matches what we requested
                if userid_attr != user_id:
                    colored_print(f"⚠️  WARNING: Requested user {user_id} but got plays with userid={userid_attr}", Colors.RED)
                else:
                    colored_print(f"✅ User ID matches: requested={user_id}, returned={userid_attr}", Colors.GREEN)
                    
            else:
                colored_print(f"❌ No plays found for user {user_id}", Colors.RED)
                
        except Exception as e:
            colored_print(f"❌ Error fetching data for user {user_id}: {e}", Colors.RED)

if __name__ == "__main__":
    debug_api_data()
