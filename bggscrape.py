import xml.etree.ElementTree as ET
import requests
import re
import time
import json
from googletrans import Translator
from collections import Counter, defaultdict

# Initialize translator
translator = Translator()

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'      # Success/Official matches
    YELLOW = '\033[93m'     # Translations
    RED = '\033[91m'        # Unmatched/Errors
    BLUE = '\033[94m'       # Fuzzy matches
    CYAN = '\033[96m'       # Info
    MAGENTA = '\033[95m'    # Warnings
    BOLD = '\033[1m'        # Bold text
    RESET = '\033[0m'       # Reset to default

def colored_print(text, color=Colors.RESET):
    """Print text with color"""
    print(f"{color}{text}{Colors.RESET}")

def status_colored_print(original, translated, status_info):
    """Print translation/matching info with appropriate colors"""
    if "TRANSLATED" in status_info and "OFFICIAL" in status_info:
        colored_print(f"  ✅ Translated & Matched: '{original}' → '{translated}'", Colors.GREEN)
    elif "TRANSLATED" in status_info:
        colored_print(f"  🔄 Translated: '{original}' → '{translated}'", Colors.YELLOW)
    elif "OFFICIAL" in status_info and "FUZZY_MATCHED" in status_info:
        colored_print(f"  🎯 Fuzzy Matched: '{original}' → '{translated}'", Colors.BLUE)
    elif "OFFICIAL" in status_info:
        colored_print(f"  ✅ Official Match: '{original}'", Colors.GREEN)
    else:
        colored_print(f"  ❌ Unmatched: '{original}' → '{translated}'", Colors.RED)

# Load official hero names from the GitHub repository
def load_official_hero_names():
    """Load the official hero names list from GitHub"""
    try:
        url = "https://github.com/josephcasey/mybgg/raw/refs/heads/master/cached_hero_names.json"
        response = requests.get(url)
        response.raise_for_status()
        hero_names = json.loads(response.text)
        
        # Create a normalized lookup dict for fuzzy matching
        normalized_heroes = {}
        for hero in hero_names:
            # Store both the original and various normalized versions
            normalized_heroes[hero.lower()] = hero
            normalized_heroes[hero.lower().replace('-', ' ')] = hero
            normalized_heroes[hero.lower().replace('.', '')] = hero
            normalized_heroes[hero.lower().replace(' ', '')] = hero
            normalized_heroes[hero.lower().replace('-', '').replace('.', '').replace(' ', '')] = hero
            
        return hero_names, normalized_heroes
    except Exception as e:
        print(f"Error loading official hero names: {e}")
        return [], {}

# Load the official hero names
OFFICIAL_HEROES, HERO_LOOKUP = load_official_hero_names()
colored_print(f"✅ Loaded {len(OFFICIAL_HEROES)} official hero names", Colors.GREEN)

def match_to_official_hero(hero_name):
    """Match a hero name to the official hero list"""
    if not hero_name:
        return None, False, False
    
    # Try exact match first
    if hero_name in OFFICIAL_HEROES:
        return hero_name, True, False
    
    # Try normalized matches
    normalized = hero_name.lower().strip()
    
    # Handle common hero name variations
    hero_normalizations = {
        # Spider-Man variants - normalize all to the official list version
        'spiderman': 'spidey',  # Spidey is in the official list
        'spider-man': 'spidey', 
        'spider man': 'spidey',
        'spider-woman': 'spiderwoman',
        'spider woman': 'spiderwoman',
        # Miles Morales handling - he's a separate hero
        'miles morales': 'miles morales',
        'spider-man - miles morales': 'miles morales',
        'spider-man - miles morales (aggr': 'miles morales',  # Handle truncated version
        # Other common variants
        'ant-man': 'ant man',
        'ant man': 'ant man',
        'dr strange': 'dr. strange',
        'dr. strange': 'dr strange',
        'doctor strange': 'dr strange',
        # War Machine / Iron Man variants
        'war machine': 'war machine',
        'iron man': 'iron man',
        # Captain variants
        'captain america': 'captain america',
        'captain marvel': 'captain marvel',
        # Wolverine variants
        'wolverine': 'wolverine',
        'wolvie': 'wolverine',
        # Nick Fury variants
        'nickfury': 'nick fury',
        'nick fury': 'nick fury',
        # Other heroes that might be missing
        'falcon': 'falcon',
        'adam warlock': 'adam warlock',
        'spectrum': 'spectrum',
    }
    
    # Apply hero normalizations
    if normalized in hero_normalizations:
        normalized = hero_normalizations[normalized]
    
    # Try various normalized forms with case-insensitive matching
    variations = [
        normalized,
        normalized.replace('-', ' '),
        normalized.replace('.', ''),
        normalized.replace(' ', ''),
        normalized.replace('-', '').replace('.', '').replace(' ', ''),
        # Handle case variations for Spider-Man specifically
        'spider-man' if 'spider' in normalized and 'man' in normalized else normalized,
        'spidey' if 'spider' in normalized and 'man' in normalized else normalized,
    ]
    
    for variation in variations:
        if variation in HERO_LOOKUP:
            official_name = HERO_LOOKUP[variation]
            return official_name, True, variation != normalized
    
    # Special handling for heroes we know should match but aren't in the official list
    # These might be newer heroes or need to be added to the GitHub list
    known_heroes = {
        'falcon': 'Falcon',
        'adam warlock': 'Adam Warlock', 
        'spectrum': 'Spectrum',
        'miles morales': 'Miles Morales',
        # Handle Spider-Man variants that should all be treated as the same character
        'spidey': 'Spider-Man',  # Use the most common name
        'spider-man': 'Spider-Man',
        'spiderman': 'Spider-Man',
    }
    
    if normalized in known_heroes:
        colored_print(f"  🔧 Known hero not in official list: '{hero_name}' → '{known_heroes[normalized]}'", Colors.BLUE)
        return known_heroes[normalized], True, True
    
    # No match found
    return hero_name, False, False

def translate_hero_name(hero_name):
    """Translate non-English hero names to English"""
    if not hero_name or not hero_name.strip():
        return hero_name, False
    
    was_translated = False
    
    # Manual translations for Marvel character names
    translations = {
        # Spanish heroes
        'Halcón': 'Falcon',
        'Soldado de invierno': 'Winter Soldier',
        'Araña': 'Spider',
        'Hombre Araña': 'Spider-Man',
        'Mujer Araña': 'Spider-Woman',
        'Máquina de Guerra': 'War Machine',
        'Ojo de Halcón': 'Hawkeye',
        'Capitán América': 'Captain America',
        'Hombre Hormiga': 'Ant-Man',
        'Avispa': 'Wasp',
        'Viuda Negra': 'Black Widow',
        'Pantera Negra': 'Black Panther',
        'Bruja Escarlata': 'Scarlet Witch',
        'Visión': 'Vision',
        'Thor': 'Thor',
        'Hulk': 'Hulk',
        'Iron Man': 'Iron Man',
        'Capitana Marvel': 'Captain Marvel',
        'Doctor Extraño': 'Doctor Strange',
        'Estrella Señora': 'Star-Lord',
        'Gamora': 'Gamora',
        'Drax': 'Drax',
        'Rocket': 'Rocket',
        'Groot': 'Groot',
        # Chinese hero names
        '凤凰女': 'Phoenix',
        '钢铁侠': 'Iron Man',
        '美国队长': 'Captain America',
        '蜘蛛侠': 'Spider-Man',
        '蜘蛛女侠': 'Spider-Woman',
        '金刚狼': 'Wolverine',
        '雷神': 'Thor',
        '绿巨人': 'Hulk',
        '黑寡妇': 'Black Widow',
        '鹰眼': 'Hawkeye',
        '奇异博士': 'Doctor Strange',
        '万磁王': 'Magneto',
        # Chinese villain/scenario names (mark as non-heroes)
        '红坦克': '[VILLAIN] Juggernaut',
        '惊恶先生': '[VILLAIN] Mister Sinister',
        '纷争': '[SCENARIO] Strife',
        '围攻': '[SCENARIO] Siege',
        '逃出': '[SCENARIO] Escape',
        '毁灭博士': '[VILLAIN] Doctor Doom',
        '绿魔': '[VILLAIN] Green Goblin',
    }
    
    # Check manual translations first
    if hero_name in translations:
        translated = translations[hero_name]
        if translated.startswith('[VILLAIN]') or translated.startswith('[SCENARIO]'):
            colored_print(f"  🚫 Skipping non-hero: '{hero_name}' → '{translated}'", Colors.MAGENTA)
            return None, True  # Return None to skip this entry
        else:
            colored_print(f"  🔧 Manual translation: '{hero_name}' → '{translated}'", Colors.YELLOW)
            return translated, True
    
    try:
        # Check if the string contains non-ASCII characters (likely non-English)
        if any(ord(char) > 127 for char in hero_name):
            # Try to translate to English
            translated = translator.translate(hero_name, dest='en')
            if translated and translated.text:
                # Check if it's likely a villain or scenario
                villain_keywords = ['villain', 'boss', 'enemy', 'scheme', 'escape', 'siege', 'attack']
                if any(keyword in translated.text.lower() for keyword in villain_keywords):
                    colored_print(f"  🚫 Skipping likely villain/scenario: '{hero_name}' → '{translated.text}'", Colors.MAGENTA)
                    return None, True
                else:
                    colored_print(f"  🤖 Auto-translated: '{hero_name}' → '{translated.text}'", Colors.YELLOW)
                    return translated.text, True
                
        return hero_name, False
        
    except Exception as e:
        colored_print(f"  ❌ Translation error for '{hero_name}': {e}", Colors.RED)
        return hero_name, False

def fetch_plays_xml(page=1, username=None):
    if username:
        url = f"https://boardgamegeek.com/xmlapi2/plays?username={username}&id=285774&page={page}"
    else:
        url = f"https://boardgamegeek.com/xmlapi2/plays?id=285774&page={page}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return ET.fromstring(response.content)

def extract_usernames_from_plays(root):
    """Extract usernames/userids from plays XML"""
    userids = []
    for play in root.findall("play"):
        userid = play.get("userid")
        if userid:
            userids.append(userid)
    return list(set(userids))  # Remove duplicates

def fetch_user_plays_by_userid_direct(userid, max_plays=100):
    """Fetch up to max_plays for a specific user using direct user plays API"""
    all_plays = []
    page = 1
    plays_fetched = 0
    
    print(f"Fetching plays for user ID: {userid} using direct user API")
    
    while plays_fetched < max_plays:
        try:
            print(f"  Fetching page {page}...")
            # Try using the user-specific plays endpoint
            url = f"https://boardgamegeek.com/xmlapi2/plays?userid={userid}&id=285774&page={page}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
            plays = root.findall("play")
            if not plays:
                print(f"  No more plays found on page {page}")
                break
            
            # All plays should be for this user and game already
            valid_plays = []
            for play in plays:
                # Verify it's Marvel Champions
                items = play.findall(".//item")
                for item in items:
                    if item.get("objectid") == "285774":
                        valid_plays.append(play)
                        plays_fetched += 1
                        break
                if plays_fetched >= max_plays:
                    break
            
            all_plays.extend(valid_plays)
            print(f"  Found {len(valid_plays)} Marvel Champions plays on page {page}, total: {plays_fetched}")
            
            if len(plays) < 100:  # BGG typically returns 100 plays per page
                print("  Reached end of user's plays")
                break
                
            page += 1
            
            # Be respectful to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    print(f"Total Marvel Champions plays fetched for user {userid}: {plays_fetched}")
    return all_plays

def extract_hero_mentions(root):
    plays = []
    for play in root.findall("play"):
        comments = play.find("comments")
        if comments is not None and comments.text:
            plays.append(comments.text.strip())

    hero_counts = {}
    for comment in plays:
        matches = re.findall(r'\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\b', comment)
        for match in matches:
            normalized = match.lower()
            hero_counts[normalized] = hero_counts.get(normalized, 0) + 1
    return pd.DataFrame(hero_counts.items(), columns=["hero_name", "mention_count"]).sort_values("mention_count", ascending=False)

def extract_hero_names_from_plays(plays_list):
    """Extract hero names from the color field in player data and translate to English"""
    hero_counts = {}
    translation_cache = {}  # Cache translations to avoid API calls
    unmatched_heroes = []  # Track heroes that don't match official list
    unmatched_xml_examples = {}  # Store XML examples for unmatched heroes
    
    # Track skipped plays with detailed information
    skipped_plays = {
        'no_players': [],
        'empty_color': [],
        'meaningless_names': [],
        'villains': [],
        'scenarios': [],
        'translation_errors': []
    }
    
    # Statistics tracking
    total_plays = len(plays_list)
    plays_with_players = 0
    total_players = 0
    total_players_with_color = 0
    
    colored_print("🎯 Extracting and translating hero names...", Colors.CYAN)
    
    for play in plays_list:
        play_id = play.get('id')
        play_date = play.get('date')
        userid = play.get('userid')
        
        # Extract comments for debugging
        comments_elem = play.find('comments')
        comments = comments_elem.text.strip() if comments_elem is not None and comments_elem.text else ""
        
        players = play.find("players")
        if players is None:
            # Track plays with no players element
            skipped_plays['no_players'].append({
                'play_id': play_id,
                'play_date': play_date,
                'userid': userid,
                'comments': comments,
                'reason': 'No players element found'
            })
            continue
            
        player_list = players.findall("player")
        if len(player_list) == 0:
            # Track plays with empty players list
            skipped_plays['no_players'].append({
                'play_id': play_id,
                'play_date': play_date,
                'userid': userid,
                'comments': comments,
                'reason': 'Empty players list'
            })
            continue
            
        plays_with_players += 1
        total_players += len(player_list)
        
        for player in player_list:
            color = player.get("color", "").strip()
            if not color:
                # Track players with empty color field
                skipped_plays['empty_color'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'player_xml': player.attrib,
                    'reason': 'Empty color field'
                })
                continue
                
            total_players_with_color += 1
            
            # Clean up the hero name (remove extra info like aspects, team numbers, etc.)
            cleaned_name = clean_hero_name(color)
            
            # Skip empty or meaningless names
            if not cleaned_name:
                skipped_plays['meaningless_names'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'original_color': color,
                    'cleaned_name': cleaned_name,
                    'player_xml': player.attrib,
                    'reason': 'Meaningless name after cleaning'
                })
                continue
            
            # Use cached translation if available
            if cleaned_name in translation_cache:
                translated_name, was_translated = translation_cache[cleaned_name]
            else:
                translated_name, was_translated = translate_hero_name(cleaned_name)
                translation_cache[cleaned_name] = (translated_name, was_translated)
                # Small delay to be respectful to translation API
                if was_translated:
                    time.sleep(0.1)
            
            # Skip if translation resulted in empty string or None (villains/scenarios)
            if not translated_name:
                # Check if it was filtered as villain or scenario by looking at translation result
                test_translation = None
                category = 'translation_errors'
                
                try:
                    # Try translation again to get the actual result for categorization
                    test_translation, _ = translate_hero_name(cleaned_name)
                    if test_translation and isinstance(test_translation, str):
                        if '[VILLAIN]' in test_translation:
                            category = 'villains'
                        elif '[SCENARIO]' in test_translation:
                            category = 'scenarios'
                except:
                    pass
                    
                skipped_plays[category].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'original_color': color,
                    'cleaned_name': cleaned_name,
                    'translated_name': str(test_translation) if test_translation else None,
                    'player_xml': player.attrib,
                    'reason': f'Filtered as {category[:-1]}' if category in ['villains', 'scenarios'] else 'Translation returned None'
                })
                continue
                
            if not str(translated_name).strip():
                skipped_plays['translation_errors'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'original_color': color,
                    'cleaned_name': cleaned_name,
                    'translated_name': translated_name,
                    'player_xml': player.attrib,
                    'reason': 'Empty string after translation'
                })
                continue
            
            # Try to match to official hero list
            official_name, is_official, was_fuzzy_matched = match_to_official_hero(translated_name)
            
            # Use the official name if found, otherwise use translated name
            final_name = official_name if is_official else translated_name
            
            # Track status for reporting
            status_flags = []
            if was_translated:
                status_flags.append("TRANSLATED")
            if is_official:
                status_flags.append("OFFICIAL")
            else:
                status_flags.append("UNMATCHED")
                if final_name not in unmatched_heroes:
                    unmatched_heroes.append(final_name)
                    # Store XML example for debugging
                    unmatched_xml_examples[final_name] = {
                        'original_color': color,
                        'cleaned_name': cleaned_name,
                        'translated_name': translated_name,
                        'player_xml': player.attrib,
                        'play_id': play_id,
                        'play_date': play_date,
                        'userid': userid,
                        'comments': comments
                    }
            if was_fuzzy_matched:
                status_flags.append("FUZZY_MATCHED")
            
            # Show status with color coding
            status_str = ", ".join(status_flags)
            if cleaned_name != final_name or status_flags:
                status_colored_print(cleaned_name, final_name, status_str)
            
            # Create a key that includes status info
            key = f"{final_name} [{status_str}]"
            hero_counts[key] = hero_counts.get(key, 0) + 1
    
    # Report statistics
    colored_print(f"\n📊 Play Analysis Statistics:", Colors.BOLD)
    colored_print(f"- Total plays analyzed: {total_plays}", Colors.CYAN)
    colored_print(f"- Plays with player data: {plays_with_players} ({plays_with_players/total_plays*100:.1f}%)", Colors.CYAN)
    colored_print(f"- Total players found: {total_players}", Colors.CYAN)
    colored_print(f"- Players with color data: {total_players_with_color} ({total_players_with_color/total_players*100:.1f}% of players)" if total_players > 0 else "- Players with color data: 0", Colors.CYAN)
    colored_print(f"- Average players per play: {total_players/plays_with_players:.1f}" if plays_with_players > 0 else "- Average players per play: 0", Colors.CYAN)
    
    # Report skipped plays with detailed breakdown
    total_skipped = sum(len(category_list) for category_list in skipped_plays.values())
    if total_skipped > 0:
        colored_print(f"\n🚫 Skipped Plays Analysis ({total_skipped} total):", Colors.MAGENTA)
        
        for category, plays in skipped_plays.items():
            if plays:
                category_name = category.replace('_', ' ').title()
                colored_print(f"\n   📋 {category_name}: {len(plays)} plays", Colors.YELLOW)
                
                # Show first few examples with XML details
                for i, play_info in enumerate(plays[:3]):  # Show first 3 examples
                    colored_print(f"      Example {i+1}:", Colors.CYAN)
                    colored_print(f"         Play ID: {play_info['play_id']}", Colors.CYAN)
                    colored_print(f"         Date: {play_info['play_date']}", Colors.CYAN)
                    colored_print(f"         User ID: {play_info['userid']}", Colors.CYAN)
                    colored_print(f"         Reason: {play_info['reason']}", Colors.CYAN)
                    if play_info.get('comments'):
                        colored_print(f"         Comments: {play_info['comments'][:100]}{'...' if len(play_info['comments']) > 100 else ''}", Colors.CYAN)
                    if play_info.get('original_color'):
                        colored_print(f"         Original color: '{play_info['original_color']}'", Colors.CYAN)
                    if play_info.get('cleaned_name'):
                        colored_print(f"         Cleaned name: '{play_info['cleaned_name']}'", Colors.CYAN)
                    if play_info.get('translated_name'):
                        colored_print(f"         Translated: '{play_info['translated_name']}'", Colors.CYAN)
                    if play_info.get('player_xml'):
                        colored_print(f"         Player XML: {play_info['player_xml']}", Colors.CYAN)
                
                if len(plays) > 3:
                    colored_print(f"      ... and {len(plays) - 3} more {category_name.lower()}", Colors.CYAN)
    
    # Report unmatched heroes with detailed XML debugging info
    if unmatched_heroes:
        colored_print(f"\n⚠️  Unmatched heroes found ({len(unmatched_heroes)}):", Colors.MAGENTA)
        for hero in unmatched_heroes:
            colored_print(f"\n   🔍 Hero: {hero}", Colors.RED)
            if hero in unmatched_xml_examples:
                example = unmatched_xml_examples[hero]
                colored_print(f"      📝 XML Debug Info:", Colors.YELLOW)
                colored_print(f"         Original color field: '{example['original_color']}'", Colors.YELLOW)
                colored_print(f"         Cleaned name: '{example['cleaned_name']}'", Colors.YELLOW)
                colored_print(f"         Translated name: '{example['translated_name']}'", Colors.YELLOW)
                colored_print(f"         Play ID: {example['play_id']}", Colors.YELLOW)
                colored_print(f"         Play Date: {example['play_date']}", Colors.YELLOW)
                colored_print(f"         User ID: {example['userid']}", Colors.YELLOW)
                if example.get('comments'):
                    colored_print(f"         Comments: {example['comments'][:100]}{'...' if len(example['comments']) > 100 else ''}", Colors.YELLOW)
                colored_print(f"         Full player XML: {example['player_xml']}", Colors.YELLOW)
    
    if not hero_counts:
        return []
    
    # Parse the results to separate name and status
    results = []
    for key, count in hero_counts.items():
        # Extract name and status from the key
        if '[' in key and key.endswith(']'):
            name = key[:key.rfind('[')].strip()
            status = key[key.rfind('[')+1:-1]
        else:
            name = key
            status = "UNKNOWN"
        results.append({"hero_name": name, "play_count": count, "status": status})
    
    # Sort by play count (descending)
    results.sort(key=lambda x: x["play_count"], reverse=True)
    return results

def clean_hero_name(raw_name):
    """Clean up hero name by removing aspects, team info, etc."""
    if not raw_name or not raw_name.strip():
        return ""
    
    # Remove common prefixes and suffixes
    name = raw_name.strip()
    
    # Skip if it's just a team number or empty
    if re.match(r'^(Team\s*\d+|팀\s*\d+|Team\s*[A-Z]?)$', name, re.IGNORECASE):
        return ""
    
    # Handle special cases first
    # Extract hero name from "Aspect: X／Hero" format
    aspect_match = re.match(r'^Aspect:\s*[^／]+／(.+)$', name)
    if aspect_match:
        name = aspect_match.group(1).strip()
    
    # Remove aspect information
    name = re.sub(r'／.*$', '', name)  # Remove everything after ／
    name = re.sub(r'/.*$', '', name)  # Remove everything after /
    name = re.sub(r'\s*-\s*(Aggr|Prot|Just|Lead|Leadership|Justice|Protection|Aggression).*$', '', name, re.IGNORECASE)
    name = re.sub(r'\s*\(.*\).*$', '', name)  # Remove parenthetical info
    name = re.sub(r'ASPECT:.*', '', name, re.IGNORECASE)  # Remove aspect info
    name = re.sub(r'Team\s*\d+.*', '', name, re.IGNORECASE)  # Remove team numbers
    name = re.sub(r'팀\s*\d+.*', '', name)  # Remove Korean team numbers
    
    # Clean up spacing
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Return empty string if nothing meaningful remains
    if len(name) < 2 or name.isdigit():
        return ""
    
    return name

def extract_hero_mentions_from_plays(plays_list):
    """Extract hero mentions from a list of play elements"""
    comments = []
    for play in plays_list:
        comment_elem = play.find("comments")
        if comment_elem is not None and comment_elem.text:
            comments.append(comment_elem.text.strip())

    hero_counts = {}
    for comment in comments:
        matches = re.findall(r'\b[A-Z][a-z]+(?:[-\s][A-Z][a-z]+)*\b', comment)
        for match in matches:
            normalized = match.lower()
            hero_counts[normalized] = hero_counts.get(normalized, 0) + 1
    
    if not hero_counts:
        return []
        
    # Convert to list of dictionaries and sort by count
    results = [{"hero_name": hero, "mention_count": count} for hero, count in hero_counts.items()]
    results.sort(key=lambda x: x["mention_count"], reverse=True)
    return results

# First, get some recent plays to find active users
colored_print("🔍 Fetching recent plays to find active users...", Colors.CYAN)
root = fetch_plays_xml(page=1)

userids = extract_usernames_from_plays(root)
colored_print(f"👥 Found {len(userids)} users in recent plays", Colors.GREEN)
colored_print(f"First 10 user IDs: {userids[:10]}", Colors.CYAN)

if userids:
    first_userid = userids[0]
    colored_print(f"\n🎯 Analyzing plays for first user ID: {first_userid}", Colors.BOLD)
    
    # Fetch up to 100 plays for the first user using direct API
    user_plays = fetch_user_plays_by_userid_direct(first_userid, max_plays=100)
    
    if user_plays:
        # Analyze hero names from Team/Color fields
        hero_results = extract_hero_names_from_plays(user_plays)
        colored_print(f"\n🎯 Hero usage analysis for user {first_userid} (with official matching):", Colors.BOLD)
        
        # Print top 30 hero results
        for i, hero in enumerate(hero_results[:30]):
            print(f"{i+1:2d}. {hero['hero_name']:<20} {hero['play_count']:>3} plays [{hero['status']}]")
        
        # Show summary statistics with colors
        total_plays = sum(hero['play_count'] for hero in hero_results)
        official_plays = sum(hero['play_count'] for hero in hero_results if 'OFFICIAL' in hero['status'])
        translated_plays = sum(hero['play_count'] for hero in hero_results if 'TRANSLATED' in hero['status'])
        unmatched_plays = sum(hero['play_count'] for hero in hero_results if 'UNMATCHED' in hero['status'])
        
        colored_print(f"\n📊 Summary Statistics:", Colors.BOLD)
        colored_print(f"- Total hero plays analyzed: {total_plays}", Colors.CYAN)
        colored_print(f"- ✅ Official matches: {official_plays} ({official_plays/total_plays*100:.1f}%)" if total_plays > 0 else "- ✅ Official matches: 0 (0.0%)", Colors.GREEN)
        colored_print(f"- 🔄 Translated plays: {translated_plays} ({translated_plays/total_plays*100:.1f}%)" if total_plays > 0 else "- 🔄 Translated plays: 0 (0.0%)", Colors.YELLOW)
        colored_print(f"- ❌ Unmatched plays: {unmatched_plays} ({unmatched_plays/total_plays*100:.1f}%)" if total_plays > 0 else "- ❌ Unmatched plays: 0 (0.0%)", Colors.RED)
        
        # Also show comment-based analysis for comparison
        comment_results = extract_hero_mentions_from_plays(user_plays)
        colored_print(f"\n💬 Comment-based analysis for comparison:", Colors.BOLD)
        for i, hero in enumerate(comment_results[:5]):
            print(f"{i+1}. {hero['hero_name']:<15} {hero['mention_count']:>3} mentions")
    else:
        colored_print(f"❌ No plays found for user {first_userid}", Colors.RED)
else:
    print("No users found in recent plays")
