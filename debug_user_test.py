#!/usr/bin/env python3
"""Quick debug test to check single user data fetching"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

from bggscrape import fetch_user_plays_by_userid_direct

def test_single_user():
    print("Testing single user data fetch...")
    
    # Test user 1
    user_id = "4734"
    print(f"\nFetching plays for user {user_id}")
    plays1 = fetch_user_plays_by_userid_direct(user_id, max_plays=5)
    print(f"User {user_id}: {len(plays1)} plays")
    if plays1:
        print(f"First play ID: {plays1[0].get('id')}")
        print(f"First play date: {plays1[0].get('date')}")
        print(f"First play user: {plays1[0].get('userid')}")
    
    # Test user 2
    user_id = "3381115"
    print(f"\nFetching plays for user {user_id}")
    plays2 = fetch_user_plays_by_userid_direct(user_id, max_plays=5)
    print(f"User {user_id}: {len(plays2)} plays")
    if plays2:
        print(f"First play ID: {plays2[0].get('id')}")
        print(f"First play date: {plays2[0].get('date')}")
        print(f"First play user: {plays2[0].get('userid')}")
    
    # Check if they're the same (they shouldn't be!)
    if plays1 and plays2:
        same_first_play = plays1[0].get('id') == plays2[0].get('id')
        print(f"\nAre first plays identical? {same_first_play}")
        if same_first_play:
            print("❌ ERROR: Different users returning same plays!")
        else:
            print("✅ Good: Different users return different plays")

if __name__ == "__main__":
    test_single_user()
