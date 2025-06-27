#!/usr/bin/env python3
"""Test color field processing logic"""

import sys
sys.path.append('/Users/jo/globalbggchamps')

from bggscrape import clean_hero_name, translate_hero_name, colored_print, Colors

def test_color_processing():
    """Test the color field processing for the problematic entries"""
    
    test_colors = [
        "Bishop (Protection)",
        "Constructed／Captain Marvel",
        "",
        "Team 1",
        "Justice／She-hulk"
    ]
    
    for color in test_colors:
        colored_print(f"\n🔍 Testing color: '{color}'", Colors.CYAN)
        
        # Test clean_hero_name
        cleaned = clean_hero_name(color)
        colored_print(f"   Cleaned: '{cleaned}'", Colors.YELLOW)
        
        if cleaned:
            # Test translate_hero_name
            translated, was_translated = translate_hero_name(cleaned)
            colored_print(f"   Translated: '{translated}' (was_translated={was_translated})", Colors.GREEN)
        else:
            colored_print(f"   ❌ Cleaned to empty string - this explains the 'Empty Color Field' error", Colors.RED)

if __name__ == "__main__":
    test_color_processing()
