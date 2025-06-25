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

# Configuration for debug output
TERMINAL_DEBUG = True  # Set to True to enable detailed XML dumps and verbose output

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

# Load official villain names from the GitHub repository
def load_official_villain_names():
    """Load the official villain names list from GitHub"""
    try:
        url = "https://github.com/josephcasey/mybgg/raw/refs/heads/master/cached_villain_names.json"
        response = requests.get(url)
        response.raise_for_status()
        villain_names = json.loads(response.text)
        
        # Create a normalized lookup dict for villain detection
        normalized_villains = {}
        for villain in villain_names:
            # Store both the original and various normalized versions
            villain_lower = villain.lower()
            normalized_villains[villain_lower] = villain
            normalized_villains[villain_lower.replace('-', ' ')] = villain
            normalized_villains[villain_lower.replace('.', '')] = villain
            normalized_villains[villain_lower.replace(' ', '')] = villain
            normalized_villains[villain_lower.replace('-', '').replace('.', '').replace(' ', '')] = villain
            # Also handle common villain name patterns
            if ' 1/' in villain_lower or ' 2/' in villain_lower or ' a' == villain_lower[-2:]:
                base_name = villain_lower.split(' ')[0]
                normalized_villains[base_name] = villain
            
        return villain_names, normalized_villains
    except Exception as e:
        print(f"Error loading official villain names: {e}")
        return [], {}

def is_villain_name(name):
    """Check if a name matches known villains"""
    if not name:
        return False
    
    normalized = name.lower().strip()
    
    # Check against villain list
    if normalized in VILLAIN_LOOKUP:
        return True
    
    # Check for common villain patterns
    villain_patterns = [
        'vs ', ' vs', 'versus',
        'villain', 'boss', 'enemy',
        'scenario', 'campaign', 'mission'
    ]
    
    for pattern in villain_patterns:
        if pattern in normalized:
            return True
    
    return False

# Load the official hero and villain names
OFFICIAL_HEROES, HERO_LOOKUP = load_official_hero_names()
OFFICIAL_VILLAINS, VILLAIN_LOOKUP = load_official_villain_names()
colored_print(f"✅ Loaded {len(OFFICIAL_HEROES)} official hero names", Colors.GREEN)
colored_print(f"✅ Loaded {len(OFFICIAL_VILLAINS)} official villain names", Colors.GREEN)

def match_to_official_hero(hero_name):
    """Match a hero name to the official hero list, including AH (Altered Heroes) handling"""
    if not hero_name:
        return None, False, False, False
    
    # Check for AH (Altered Heroes) convention first
    is_altered = False
    base_name = hero_name
    if hero_name.lower().startswith('ah - ') or hero_name.lower().startswith('ah-'):
        is_altered = True
        # Extract the base hero name from "AH - Hero" or "AH-Hero"
        if ' - ' in hero_name:
            base_name = hero_name.split(' - ', 1)[1].strip()
        elif hero_name.lower().startswith('ah-'):
            base_name = hero_name[3:].strip()
        
        if TERMINAL_DEBUG:
            colored_print(f"  🔄 Altered Hero detected: '{hero_name}' → base: '{base_name}'", Colors.BLUE)
    
    # Try exact match first (on base name for AH heroes)
    if base_name in OFFICIAL_HEROES:
        return base_name, True, False, is_altered
    
    # Try normalized matches
    normalized = base_name.lower().strip()
    
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
        'cap marvel': 'captain marvel',  # Captain Marvel nickname
        'capmarv': 'captain marvel',     # Captain Marvel abbreviation
        # Wolverine variants
        'wolverine': 'wolverine',
        'wolvie': 'wolverine',
        # Black Panther variants
        'black panther': 'black panther',
        'panther': 'black panther',      # Black Panther nickname
        # Nick Fury variants
        'nickfury': 'nick fury',
        'nick fury': 'nick fury',
        # Drax variants
        'drax': 'drax',
        'drax the destroyer': 'drax',
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
            return official_name, True, variation != normalized, is_altered
    
    # Special handling for heroes we know should match but aren't in the official list
    # These might be newer heroes or need to be added to the GitHub list
    known_heroes = {
        'falcon': 'Falcon',
        'adam warlock': 'Adam Warlock', 
        'spectrum': 'Spectrum',
        'miles morales': 'Miles Morales',
        'black panther': 'Black Panther',
        'captain marvel': 'Captain Marvel',
        'drax': 'Drax',
        # Handle Spider-Man variants that should all be treated as the same character
        'spidey': 'Spider-Man',  # Use the most common name
        'spider-man': 'Spider-Man',
        'spiderman': 'Spider-Man',
    }
    
    if normalized in known_heroes:
        colored_print(f"  🔧 Known hero not in official list: '{base_name}' → '{known_heroes[normalized]}'", Colors.BLUE)
        return known_heroes[normalized], True, True, is_altered
    
    # No match found
    return base_name, False, False, is_altered

def translate_hero_name(hero_name):
    """Translate non-English hero names to English and filter out villains"""
    if not hero_name or not hero_name.strip():
        return hero_name, False
    
    # First check if this is a known villain - if so, mark for filtering
    if is_villain_name(hero_name):
        if TERMINAL_DEBUG:
            colored_print(f"  🦹 Villain detected: '{hero_name}' - filtering out", Colors.MAGENTA)
        return None, False  # Return None to indicate this should be filtered
    
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
    # Convert to list of dictionaries and sort by count
    results = [{"hero_name": hero, "mention_count": count} for hero, count in hero_counts.items()]
    results.sort(key=lambda x: x["mention_count"], reverse=True)
    return results

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
            # Try to extract hero names from comments before giving up
            heroes_from_comments = parse_heroes_from_comments(comments, play_id)
            
            if heroes_from_comments:
                # Found heroes in comments! Process each one
                if TERMINAL_DEBUG:
                    colored_print(f"\n🔍 RECOVERED - Found Heroes in Comments (No Players Element):", Colors.GREEN)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   No players element, but heroes from comments: {[h['matched'] for h in heroes_from_comments]}", Colors.GREEN)
                    if comments:
                        colored_print(f"   Comments: {comments[:200]}...", Colors.CYAN)
                
                # Process each hero found in comments
                for hero_data in heroes_from_comments:
                    hero_name = hero_data['matched']
                    
                    # Determine status based on how it was matched
                    if hero_data['is_altered']:
                        status = 'ALTERED_HERO|OFFICIAL|FROM_COMMENTS|NO_PLAYERS'
                    elif hero_data['is_official']:
                        status = 'OFFICIAL|FROM_COMMENTS|NO_PLAYERS'
                    elif hero_data['is_fuzzy']:
                        status = 'OFFICIAL|FUZZY_MATCHED|FROM_COMMENTS|NO_PLAYERS'
                    else:
                        status = 'FROM_COMMENTS|NO_PLAYERS'
                    
                    # Add to results
                    if hero_name in hero_counts:
                        hero_counts[hero_name]['count'] += 1
                        hero_counts[hero_name]['status'].add(status)
                    else:
                        hero_counts[hero_name] = {
                            'count': 1, 
                            'status': {status},
                            'is_altered': hero_data['is_altered']
                        }
                    
                    if TERMINAL_DEBUG:
                        status_colored_print(hero_data['original'], hero_name, status)
                
                # Don't skip this record since we found heroes, but mark it as having heroes without players
                plays_with_players += 1  # Count as having usable data even though no structured players
                continue
            else:
                # Track plays with no players element and no heroes in comments
                if TERMINAL_DEBUG:
                    colored_print(f"\n🚫 SKIPPED - No Players Element:", Colors.MAGENTA)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   Raw Play XML:", Colors.YELLOW)
                    play_xml_str = ET.tostring(play, encoding='unicode', method='xml')
                    colored_print(f"   {play_xml_str[:500]}...", Colors.YELLOW)  # First 500 chars
                    if comments:
                        colored_print(f"   📄 FULL COMMENTS:", Colors.CYAN)
                        colored_print(f"   {comments}", Colors.CYAN)
                    else:
                        colored_print(f"   📄 No comments in this play", Colors.CYAN)
                    colored_print(f"   📝 No heroes found in comments either", Colors.RED)
                    colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                
                skipped_plays['no_players'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'full_xml': ET.tostring(play, encoding='unicode', method='xml'),
                    'reason': 'No players element found, no heroes in comments'
                })
                continue
            
        player_list = players.findall("player")
        if len(player_list) == 0:
            # Try to extract hero names from comments before giving up
            heroes_from_comments = parse_heroes_from_comments(comments, play_id)
            
            if heroes_from_comments:
                # Found heroes in comments! Process each one
                if TERMINAL_DEBUG:
                    colored_print(f"\n🔍 RECOVERED - Found Heroes in Comments (Empty Players List):", Colors.GREEN)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   Empty players list, but heroes from comments: {[h['matched'] for h in heroes_from_comments]}", Colors.GREEN)
                    if comments:
                        colored_print(f"   Comments: {comments[:200]}...", Colors.CYAN)
                
                # Process each hero found in comments
                for hero_data in heroes_from_comments:
                    hero_name = hero_data['matched']
                    
                    # Determine status based on how it was matched
                    if hero_data['is_altered']:
                        status = 'ALTERED_HERO|OFFICIAL|FROM_COMMENTS|EMPTY_PLAYERS'
                    elif hero_data['is_official']:
                        status = 'OFFICIAL|FROM_COMMENTS|EMPTY_PLAYERS'
                    elif hero_data['is_fuzzy']:
                        status = 'OFFICIAL|FUZZY_MATCHED|FROM_COMMENTS|EMPTY_PLAYERS'
                    else:
                        status = 'FROM_COMMENTS|EMPTY_PLAYERS'
                    
                    # Add to results
                    if hero_name in hero_counts:
                        hero_counts[hero_name]['count'] += 1
                        hero_counts[hero_name]['status'].add(status)
                    else:
                        hero_counts[hero_name] = {
                            'count': 1, 
                            'status': {status},
                            'is_altered': hero_data['is_altered']
                        }
                    
                    if TERMINAL_DEBUG:
                        status_colored_print(hero_data['original'], hero_name, status)
                
                # Don't skip this record since we found heroes
                plays_with_players += 1  # Count as having usable data
                continue
            else:
                # Track plays with empty players list and no heroes in comments
                if TERMINAL_DEBUG:
                    colored_print(f"\n🚫 SKIPPED - Empty Players List:", Colors.MAGENTA)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   Players Element XML:", Colors.YELLOW)
                    players_xml_str = ET.tostring(players, encoding='unicode', method='xml')
                    colored_print(f"   {players_xml_str}", Colors.YELLOW)
                    if comments:
                        colored_print(f"   📄 FULL COMMENTS:", Colors.CYAN)
                        colored_print(f"   {comments}", Colors.CYAN)
                    else:
                        colored_print(f"   📄 No comments in this play", Colors.CYAN)
                    colored_print(f"   📝 No heroes found in comments either", Colors.RED)
                    colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                
                skipped_plays['no_players'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'full_xml': ET.tostring(players, encoding='unicode', method='xml'),
                    'reason': 'Empty players list, no heroes in comments'
                })
                continue
            
        plays_with_players += 1
        total_players += len(player_list)
        
        for player in player_list:
            color = player.get("color", "").strip()
            if not color:
                # Try to extract hero names from comments before giving up
                heroes_from_comments = parse_heroes_from_comments(comments, play_id)
                
                if heroes_from_comments:
                    # Found heroes in comments! Process each one
                    if TERMINAL_DEBUG:
                        colored_print(f"\n🔍 RECOVERED - Found Heroes in Comments (Empty Color):", Colors.GREEN)
                        colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                        colored_print(f"   Empty color field, but heroes from comments: {[h['matched'] for h in heroes_from_comments]}", Colors.GREEN)
                        if comments:
                            colored_print(f"   Comments: {comments[:200]}...", Colors.CYAN)
                    
                    # Process each hero found in comments
                    for hero_data in heroes_from_comments:
                        hero_name = hero_data['matched']
                        
                        # Determine status based on how it was matched
                        if hero_data['is_altered']:
                            status = 'ALTERED_HERO|OFFICIAL|FROM_COMMENTS|EMPTY_COLOR'
                        elif hero_data['is_official']:
                            status = 'OFFICIAL|FROM_COMMENTS|EMPTY_COLOR'
                        elif hero_data['is_fuzzy']:
                            status = 'OFFICIAL|FUZZY_MATCHED|FROM_COMMENTS|EMPTY_COLOR'
                        else:
                            status = 'FROM_COMMENTS|EMPTY_COLOR'
                        
                        # Add to results
                        if hero_name in hero_counts:
                            hero_counts[hero_name]['count'] += 1
                            hero_counts[hero_name]['status'].add(status)
                        else:
                            hero_counts[hero_name] = {
                                'count': 1, 
                                'status': {status},
                                'is_altered': hero_data['is_altered']
                            }
                        
                        if TERMINAL_DEBUG:
                            status_colored_print(hero_data['original'], hero_name, status)
                    
                    # Don't skip this record since we found heroes
                    continue
                else:
                    # Track players with empty color field and no heroes in comments
                    if TERMINAL_DEBUG:
                        colored_print(f"\n🚫 SKIPPED - Empty Color Field:", Colors.MAGENTA)
                        colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                        colored_print(f"   Raw Player XML:", Colors.YELLOW)
                        # Convert player element to string for full XML dump
                        player_xml_str = ET.tostring(player, encoding='unicode', method='xml')
                        colored_print(f"   {player_xml_str}", Colors.YELLOW)
                        colored_print(f"   Player Attributes: {player.attrib}", Colors.CYAN)
                        if comments:
                            colored_print(f"   📄 FULL COMMENTS:", Colors.CYAN)
                            colored_print(f"   {comments}", Colors.CYAN)
                        else:
                            colored_print(f"   📄 No comments in this play", Colors.CYAN)
                        colored_print(f"   📝 No heroes found in comments either", Colors.RED)
                        colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                    
                    skipped_plays['empty_color'].append({
                        'play_id': play_id,
                        'play_date': play_date,
                        'userid': userid,
                        'comments': comments,
                        'player_xml': player.attrib,
                        'full_xml': ET.tostring(player, encoding='unicode', method='xml'),
                        'reason': 'Empty color field, no heroes in comments'
                    })
                    continue
                
            total_players_with_color += 1
            
            # Clean up the hero name (remove extra info like aspects, team numbers, etc.)
            cleaned_name = clean_hero_name(color)
            
            # Skip empty or meaningless names, but first try to parse from comments
            if not cleaned_name:
                # Try to extract hero names from comments before giving up
                heroes_from_comments = parse_heroes_from_comments(comments, play_id)
                
                if heroes_from_comments:
                    # Found heroes in comments! Process each one
                    if TERMINAL_DEBUG:
                        colored_print(f"\n🔍 RECOVERED - Found Heroes in Comments:", Colors.GREEN)
                        colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                        colored_print(f"   Original Color: '{color}' (meaningless)", Colors.YELLOW)
                        colored_print(f"   Heroes from comments: {[h['matched'] for h in heroes_from_comments]}", Colors.GREEN)
                        if comments:
                            colored_print(f"   Comments: {comments[:200]}...", Colors.CYAN)
                    
                    # Process each hero found in comments
                    for hero_data in heroes_from_comments:
                        hero_name = hero_data['matched']
                        
                        # Determine status based on how it was matched
                        if hero_data['is_altered']:
                            status = 'ALTERED_HERO|OFFICIAL|FROM_COMMENTS'
                        elif hero_data['is_official']:
                            status = 'OFFICIAL|FROM_COMMENTS'
                        elif hero_data['is_fuzzy']:
                            status = 'OFFICIAL|FUZZY_MATCHED|FROM_COMMENTS'
                        else:
                            status = 'FROM_COMMENTS'
                        
                        # Add to results
                        if hero_name in hero_counts:
                            hero_counts[hero_name]['count'] += 1
                            hero_counts[hero_name]['status'].add(status)
                        else:
                            hero_counts[hero_name] = {
                                'count': 1, 
                                'status': {status},
                                'is_altered': hero_data['is_altered']
                            }
                        
                        if TERMINAL_DEBUG:
                            status_colored_print(hero_data['original'], hero_name, status)
                    
                    # Don't skip this record since we found heroes
                    continue
                else:
                    # No heroes found in comments either, skip as meaningless
                    if TERMINAL_DEBUG:
                        colored_print(f"\n🚫 SKIPPED - Meaningless Name:", Colors.MAGENTA)
                        colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                        colored_print(f"   Original Color: '{color}'", Colors.YELLOW)
                        colored_print(f"   Cleaned Name: '{cleaned_name}'", Colors.YELLOW)
                        colored_print(f"   Raw Player XML:", Colors.YELLOW)
                        player_xml_str = ET.tostring(player, encoding='unicode', method='xml')
                        colored_print(f"   {player_xml_str}", Colors.YELLOW)
                        if comments:
                            colored_print(f"   📄 FULL COMMENTS:", Colors.CYAN)
                            colored_print(f"   {comments}", Colors.CYAN)
                        else:
                            colored_print(f"   📄 No comments in this play", Colors.CYAN)
                        colored_print(f"   📝 No heroes found in comments either", Colors.RED)
                        colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                    
                    skipped_plays['meaningless_names'].append({
                        'play_id': play_id,
                        'play_date': play_date,
                        'userid': userid,
                        'comments': comments,
                        'original_color': color,
                        'cleaned_name': cleaned_name,
                        'player_xml': player.attrib,
                        'full_xml': ET.tostring(player, encoding='unicode', method='xml'),
                        'reason': 'Meaningless name after cleaning, no heroes in comments'
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
            
            # Check if this was filtered as a villain or resulted in empty translation
            if translated_name is None:
                if TERMINAL_DEBUG:
                    colored_print(f"\n🚫 SKIPPED - Villain/Scenario Filtered:", Colors.MAGENTA)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   Original Color: '{color}'", Colors.YELLOW)
                    colored_print(f"   Cleaned Name: '{cleaned_name}'", Colors.YELLOW)
                    colored_print(f"   Translation Result: None (filtered)", Colors.RED)
                    colored_print(f"   Raw Player XML:", Colors.YELLOW)
                    player_xml_str = ET.tostring(player, encoding='unicode', method='xml')
                    colored_print(f"   {player_xml_str}", Colors.YELLOW)
                    if comments:
                        colored_print(f"   Comments: {comments[:100]}...", Colors.CYAN)
                    colored_print(f"  🦹 Villain filtered: '{color}' → '{cleaned_name}'", Colors.MAGENTA)
                    colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                
                skipped_plays['villains'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'original_color': color,
                    'cleaned_name': cleaned_name,
                    'player_xml': player.attrib,
                    'full_xml': ET.tostring(player, encoding='unicode', method='xml'),
                    'reason': 'Filtered as villain/scenario'
                })
                continue
            
            # Skip if translation resulted in empty string
            if not translated_name or not translated_name.strip():
                if TERMINAL_DEBUG:
                    colored_print(f"\n🚫 SKIPPED - Translation Error:", Colors.MAGENTA)
                    colored_print(f"   Play ID: {play_id} | Date: {play_date}", Colors.CYAN)
                    colored_print(f"   Original Color: '{color}'", Colors.YELLOW)
                    colored_print(f"   Cleaned Name: '{cleaned_name}'", Colors.YELLOW)
                    colored_print(f"   Translation Result: '{translated_name}'", Colors.RED)
                    colored_print(f"   Raw Player XML:", Colors.YELLOW)
                    player_xml_str = ET.tostring(player, encoding='unicode', method='xml')
                    colored_print(f"   {player_xml_str}", Colors.YELLOW)
                    if comments:
                        colored_print(f"   Comments: {comments[:100]}...", Colors.CYAN)
                    colored_print(f"  ❌ Translation error: '{color}' → '{cleaned_name}' → '{translated_name}'", Colors.RED)
                    colored_print(f"   🔗 BGG Play Link: https://boardgamegeek.com/play/{play_id}", Colors.BLUE)
                
                skipped_plays['translation_errors'].append({
                    'play_id': play_id,
                    'play_date': play_date,
                    'userid': userid,
                    'comments': comments,
                    'original_color': color,
                    'cleaned_name': cleaned_name,
                    'translated_name': translated_name,
                    'player_xml': player.attrib,
                    'full_xml': ET.tostring(player, encoding='unicode', method='xml'),
                    'reason': 'Translation resulted in empty string'
                })
                continue
            
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
            official_name, is_official, was_fuzzy_matched, is_altered = match_to_official_hero(translated_name)
            
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
                    # Store enhanced XML example for debugging
                    unmatched_xml_examples[final_name] = {
                        'original_color': color,
                        'cleaned_name': cleaned_name,
                        'translated_name': translated_name,
                        'player_xml': player.attrib,
                        'play_id': play_id,
                        'play_date': play_date,
                        'userid': userid,
                        'comments': comments,
                        'raw_player_xml': str(ET.tostring(player, encoding='unicode')),  # Full XML before processing
                        'is_altered': is_altered
                    }
            if was_fuzzy_matched:
                status_flags.append("FUZZY_MATCHED")
            if is_altered:
                status_flags.append("ALTERED_HERO")
            
            # Enhanced status with color coding
            status_str = ", ".join(status_flags)
            if cleaned_name != final_name or status_flags:
                if is_altered:
                    colored_print(f"  🔄 Altered Hero: '{cleaned_name}' → '{final_name}' [{status_str}]", Colors.BLUE)
                else:
                    status_colored_print(cleaned_name, final_name, status_str)
            
            # Add to results using consistent structure
            if final_name in hero_counts:
                hero_counts[final_name]['count'] += 1
                hero_counts[final_name]['status'].add(status_str)
                if is_altered:
                    hero_counts[final_name]['is_altered'] = True
            else:
                hero_counts[final_name] = {
                    'count': 1,
                    'status': {status_str},
                    'is_altered': is_altered
                }
    
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
                colored_print(f"         🔗 BGG Play Link: https://boardgamegeek.com/play/{example['play_id']}", Colors.BLUE)
                if example.get('comments'):
                    colored_print(f"         Comments: {example['comments'][:100]}{'...' if len(example['comments']) > 100 else ''}", Colors.YELLOW)
                colored_print(f"         Full player XML: {example['player_xml']}", Colors.YELLOW)
                
                # Enhanced debugging - show raw XML before cleaning
                if TERMINAL_DEBUG and example.get('raw_player_xml'):
                    colored_print(f"         📋 Raw Player XML (before processing):", Colors.CYAN)
                    colored_print(f"         {example['raw_player_xml']}", Colors.CYAN)
                
                # Enhanced debugging - show if it matches villain patterns
                if TERMINAL_DEBUG:
                    villain_match = is_villain_name(example['cleaned_name'])
                    if villain_match:
                        colored_print(f"         🦹 Villain check: MATCHES villain patterns", Colors.MAGENTA)
                    else:
                        colored_print(f"         🦸 Villain check: No villain pattern match", Colors.CYAN)
                    
                    # Check if this was an altered hero
                    if example.get('is_altered'):
                        colored_print(f"         🔄 Altered Hero: This was detected as an AH variant", Colors.BLUE)
                    
                    # Check against both hero and villain lists
                    hero_similarity = find_closest_hero_match(example['cleaned_name'])
                    if hero_similarity:
                        colored_print(f"         🎯 Closest hero match: '{hero_similarity['name']}' (similarity: {hero_similarity['score']:.2f})", Colors.BLUE)
                    
                    villain_similarity = find_closest_villain_match(example['cleaned_name'])
                    if villain_similarity:
                        colored_print(f"         🦹 Closest villain match: '{villain_similarity['name']}' (similarity: {villain_similarity['score']:.2f})", Colors.MAGENTA)

    if not hero_counts:
        return []
    
    # Parse the results to separate name, status, and track altered heroes
    results = []
    hero_totals = {}  # Track total plays per hero (including altered versions)
    altered_counts = {}  # Track altered hero counts separately
    
    for hero_name, hero_data in hero_counts.items():
        # Extract count and status from the data structure
        count = hero_data['count']
        status_set = hero_data['status']
        is_altered_entry = hero_data.get('is_altered', False)
        
        # Convert status set to string
        status = '|'.join(sorted(status_set))
        
        # Add to hero totals
        if hero_name not in hero_totals:
            hero_totals[hero_name] = 0
        hero_totals[hero_name] += count
        
        # Track altered count separately
        if is_altered_entry:
            if hero_name not in altered_counts:
                altered_counts[hero_name] = 0
            altered_counts[hero_name] += count
        
        results.append({
            "hero_name": hero_name, 
            "play_count": count, 
            "status": status,
            "is_altered": is_altered_entry,
            "total_plays": hero_totals[hero_name],  # Will be updated in final pass
            "altered_plays": altered_counts.get(hero_name, 0)
        })
    
    # Update total plays for all entries
    for result in results:
        result["total_plays"] = hero_totals[result["hero_name"]]
        result["altered_plays"] = altered_counts.get(result["hero_name"], 0)
    
    # Sort by total play count (descending), then by individual count
    results.sort(key=lambda x: (x["total_plays"], x["play_count"]), reverse=True)
    
    # Return additional statistics for accurate summary
    stats = {
        'total_plays': total_plays,
        'plays_with_players': plays_with_players,
        'total_players': total_players,
        'total_players_with_color': total_players_with_color
    }
    
    return results, skipped_plays, stats

def find_closest_hero_match(name):
    """Find the closest matching hero name using basic string similarity"""
    if not name or not OFFICIAL_HEROES:
        return None
    
    best_match = None
    best_score = 0
    
    name_lower = name.lower()
    for hero in OFFICIAL_HEROES:
        hero_lower = hero.lower()
        # Simple similarity based on character overlap
        score = len(set(name_lower) & set(hero_lower)) / len(set(name_lower) | set(hero_lower))
        if score > best_score and score > 0.3:  # Minimum similarity threshold
            best_score = score
            best_match = hero
    
    return {"name": best_match, "score": best_score} if best_match else None

def find_closest_villain_match(name):
    """Find the closest matching villain name using basic string similarity"""
    if not name or not OFFICIAL_VILLAINS:
        return None
    
    best_match = None
    best_score = 0
    
    name_lower = name.lower()
    for villain in OFFICIAL_VILLAINS:
        villain_lower = villain.lower()
        # Simple similarity based on character overlap
        score = len(set(name_lower) & set(villain_lower)) / len(set(name_lower) | set(villain_lower))
        if score > best_score and score > 0.3:  # Minimum similarity threshold
            best_score = score
            best_match = villain
    
    return {"name": best_match, "score": best_score} if best_match else None

def clean_hero_name(raw_name):
    """Clean up hero name by removing aspects, team info, etc."""
    if not raw_name or not raw_name.strip():
        return ""
    
    # Remove common prefixes and suffixes
    name = raw_name.strip()
    
    # Skip if it's just a team number or empty
    if re.match(r'^(Team\s*\d+|팀\s*\d+|Team\s*[A-Z]?)$', name, re.IGNORECASE):
        return ""
    
    # Define all Marvel Champions aspects (including Pool)
    aspects = ['Justice', 'Aggression', 'Leadership', 'Protection', 'Pool']
    aspect_pattern = '|'.join([f'({asp})' for asp in aspects])
    
    # Handle special cases first
    # Extract hero name from "Aspect: X／Hero" format
    aspect_match = re.match(r'^Aspect:\s*[^／]+／(.+)$', name)
    if aspect_match:
        name = aspect_match.group(1).strip()
    
    # Enhanced aspect-hero parsing patterns
    aspect_hero_patterns = [
        # "Aspect／Hero" or "Aspect/Hero" - extract hero
        rf'^(?:{aspect_pattern})／(.+)$',
        rf'^(?:{aspect_pattern})/(.+)$',
        
        # "Hero／Aspect" or "Hero/Aspect" - extract hero  
        rf'^(.+)／(?:{aspect_pattern})(?:\s|$)',
        rf'^(.+)/(?:{aspect_pattern})(?:\s|$)',
        
        # "Aspect - Hero" or "Hero - Aspect" formats
        rf'^(?:{aspect_pattern})\s*[-–]\s*(.+)$',
        rf'^(.+)\s*[-–]\s*(?:{aspect_pattern})(?:\s|$)',
        
        # "Aspect Hero" or "Hero Aspect" (space separated)
        rf'^(?:{aspect_pattern})\s+(.+)$',
        rf'^(.+)\s+(?:{aspect_pattern})(?:\s|$)',
        
        # ".Aspect／Hero" format (like ".Aggression／-Gambit")
        rf'^\.(?:{aspect_pattern})／[-]?(.+)$',
        rf'^\.(?:{aspect_pattern})/[-]?(.+)$',
        
        # Handle prefixed hero names like "-Gambit"
        r'^[-](.+)$',
    ]
    
    # Try each pattern to extract hero name
    for pattern in aspect_hero_patterns:
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            # Find the capture group that contains the hero name (not empty and not an aspect)
            for group in match.groups():
                if group and group.strip():
                    candidate = group.strip()
                    # Make sure it's not just an aspect name
                    if not re.match(rf'^(?:{aspect_pattern})$', candidate, re.IGNORECASE):
                        name = candidate
                        break
            break
    
    # Additional cleanup patterns
    name = re.sub(r'／.*$', '', name)  # Remove everything after ／
    name = re.sub(r'/.*$', '', name)  # Remove everything after /
    name = re.sub(r'\s*-\s*(Aggr|Prot|Just|Lead|Leadership|Justice|Protection|Aggression|Pool).*$', '', name, re.IGNORECASE)
    name = re.sub(r'\s*\(.*\).*$', '', name)  # Remove parenthetical info
    name = re.sub(r'ASPECT:.*', '', name, re.IGNORECASE)  # Remove aspect info
    name = re.sub(r'Team\s*\d+.*', '', name, re.IGNORECASE)  # Remove team numbers
    name = re.sub(r'팀\s*\d+.*', '', name)  # Remove Korean team numbers
    
    # Handle specific problematic patterns
    # "Justice Maria Hill" -> "Maria Hill"
    name = re.sub(rf'^(?:{aspect_pattern})\s+(.+)$', r'\6', name, re.IGNORECASE)
    
    # "Bishop Justice" -> "Bishop" (if Justice is at the end)
    name = re.sub(rf'^(.+)\s+(?:{aspect_pattern})$', r'\1', name, re.IGNORECASE)
    
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

def parse_heroes_from_comments(comments, play_id=None):
    """
    Parse hero names from BGG play comments using various heuristics.
    Returns list of potential hero names found in the comments.
    """
    if not comments:
        return []
    
    heroes_found = []
    comment_lower = comments.lower()
    
    # Campaign detection - infer default heroes from campaigns
    campaign_patterns = {
        # English campaign patterns
        r'\b(?:shield|s\.?h\.?i\.?e\.?l\.?d\.?)\s+campaign\b': ['Agent 13', 'Nick Fury'],
        r'\bagents?\s+of\s+shield\b': ['Agent 13', 'Nick Fury'],
        r'\bmutant\s+genesis\b': ['Wolverine', 'Storm', 'Cyclops'],
        r'\bnext\s+evolution\b': ['Colossus', 'Shadowcat'],
        r'\bsinister\s+motives\b': ['Ghost-Spider', 'Miles Morales'],
        r'\bmad\s+titan\'?s?\s+shadow\b': ['Adam Warlock', 'Spectrum'],
        r'\bgalaxy\'?s?\s+most\s+wanted\b': ['Groot', 'Rocket Raccoon'],
        r'\brise\s+of\s+red\s+skull\b': ['Hawkeye', 'Spider-Woman'],
        r'\bhood\b.*\bcampaign\b': ['Captain America', 'Iron Man'],
        
        # French campaign patterns  
        r'\bcampagne\s+shield\b': ['Agent 13', 'Nick Fury'],
        r'\bcampagne\s+s\.?h\.?i\.?e\.?l\.?d\.?\b': ['Agent 13', 'Nick Fury'],
        
        # Spanish campaign patterns
        r'\bcampaña\s+shield\b': ['Agent 13', 'Nick Fury'],
        r'\bcampaña\s+s\.?h\.?i\.?e\.?l\.?d\.?\b': ['Agent 13', 'Nick Fury'],
        
        # German campaign patterns
        r'\bschild\s+kampagne\b': ['Agent 13', 'Nick Fury'],
        r'\bs\.?h\.?i\.?e\.?l\.?d\.?\s+kampagne\b': ['Agent 13', 'Nick Fury'],
    }
    
    # Check for campaign patterns first
    for pattern, default_heroes in campaign_patterns.items():
        if re.search(pattern, comment_lower, re.IGNORECASE):
            for hero in default_heroes:
                heroes_found.append({
                    'original': f'Campaign: {hero}',
                    'cleaned': hero.lower(),
                    'matched': hero,
                    'is_official': True,
                    'is_fuzzy': False,
                    'is_altered': False,
                    'pattern': f'campaign_detection: {pattern}',
                    'source': 'campaign_inference'
                })
            if TERMINAL_DEBUG:
                colored_print(f"    🏛️ Campaign detected: {default_heroes} from pattern '{pattern}'", Colors.GREEN)
            break  # Only use first matching campaign pattern
    
    # Villain detection - look for villain names in comments
    villain_patterns = {
        # Common villain name patterns (English, French, Spanish variants)
        r'\b(?:against|vs\.?|versus|contre|contra)\s+([a-z\-\s]+)\b': 'villain_context',
        r'\b(batroc|bartoc)\b': 'Batroc',  # The villain from your example
        r'\b(red skull|crâne rouge|calavera roja)\b': 'Red Skull',
        r'\b(green goblin|goblin vert|duende verde)\b': 'Green Goblin',
        r'\b(ultron)\b': 'Ultron',
        r'\b(rhino|rhinocéros|rinoceronte)\b': 'Rhino',
        r'\b(klaw|garra)\b': 'Klaw',
        r'\b(taskmaster|supervisor de tareas)\b': 'Taskmaster',
        r'\b(crossbones|huesos cruzados)\b': 'Crossbones',
        r'\b(absorbing man|hombre absorbente)\b': 'Absorbing Man',
        r'\b(titania)\b': 'Titania',
        r'\b(wrecker|demoledor)\b': 'Wrecker',
        r'\b(thunderball)\b': 'Thunderball',
        r'\b(piledriver|piloteador)\b': 'Piledriver',
        r'\b(bulldozer)\b': 'Bulldozer',
        r'\b(nebula)\b': 'Nebula',  # Can be villain in some contexts
        r'\b(ronan|ronan el acusador)\b': 'Ronan',
        r'\b(collector|coleccionista)\b': 'Collector',
        r'\b(drang)\b': 'Drang',
        r'\b(ebony maw)\b': 'Ebony Maw',
        r'\b(thanos)\b': 'Thanos',
        r'\b(magneto|magnéto)\b': 'Magneto',
        r'\b(sentinel|centinela)\b': 'Sentinel',
        r'\b(mystique|mística)\b': 'Mystique',
        r'\b(sabretooth|dientes de sable)\b': 'Sabretooth',
        r'\b(juggernaut|mole)\b': 'Juggernaut',
        r'\b(apocalypse|apocalipsis)\b': 'Apocalypse',
        r'\b(mojo)\b': 'MojoMania',
        r'\b(spiral)\b': 'Spiral',
        r'\b(dark beast|bestia oscura)\b': 'Dark Beast',
    }
    
    for pattern, villain_name in villain_patterns.items():
        matches = re.findall(pattern, comment_lower, re.IGNORECASE)
        if matches and villain_name != 'villain_context':
            if TERMINAL_DEBUG:
                colored_print(f"    🦹 Villain detected in comments: '{villain_name}' from pattern '{pattern}'", Colors.MAGENTA)
        elif matches and villain_name == 'villain_context':
            # Extract the villain name from the context
            for match in matches:
                villain_candidate = match.strip()
                if len(villain_candidate) > 2:
                    if TERMINAL_DEBUG:
                        colored_print(f"    🦹 Potential villain in comments: '{villain_candidate}'", Colors.MAGENTA)
    
    # Common patterns for heroes in Marvel Champions comments
    patterns = [
        # Direct hero mentions with common formats
        r'\b(spider-?man|spiderman)\b',
        r'\b(iron-?man|ironman)\b', 
        r'\b(captain america|cap america|steve rogers)\b',
        r'\b(black widow|natasha)\b',
        r'\b(she-?hulk|jennifer walters)\b',
        r'\b(ms\.?\s*marvel|kamala|kamala khan)\b',
        r'\b(doctor strange|dr\.?\s*strange|stephen strange)\b',
        r'\b(captain marvel|carol danvers)\b',
        r'\b(ant-?man|antman|scott lang)\b',
        r'\b(wasp|janet|hope van dyne)\b',
        r'\b(quicksilver|pietro)\b',
        r'\b(scarlet witch|wanda|wanda maximoff)\b',
        r'\b(hawkeye|clint barton)\b',
        r'\b(black panther|t\'?challa)\b',
        r'\b(spider-?woman|jessica drew)\b',
        r'\b(valkyrie|brunnhilde)\b',
        r'\b(vision|the vision)\b',
        r'\b(war machine|james rhodes|rhodey)\b',
        r'\b(falcon|sam wilson)\b',
        r'\b(winter soldier|bucky|bucky barnes)\b',
        r'\b(hulk|bruce banner)\b',
        r'\b(thor|god of thunder)\b',
        r'\b(wolverine|logan|james howlett)\b',
        r'\b(storm|ororo)\b',
        r'\b(cyclops|scott summers)\b',
        r'\b(phoenix|jean grey)\b',
        r'\b(colossus|piotr)\b',
        r'\b(nightcrawler|kurt wagner)\b',
        r'\b(shadowcat|kitty pryde)\b',
        r'\b(gambit|remy lebeau)\b',
        r'\b(rogue|marie)\b',
        r'\b(deadpool|wade wilson)\b',
        r'\b(cable|nathan summers)\b',
        r'\b(domino|neena thurman)\b',
        r'\b(psylocke|betsy braddock)\b',
        r'\b(angel|warren worthington)\b',
        r'\b(iceman|bobby drake)\b',
        r'\b(magik|illyana rasputin)\b',
        r'\b(nova|richard rider|sam alexander)\b',
        r'\b(spider-?ham|peter porker)\b',
        r'\b(ghost-?spider|spider-?gwen|gwen stacy)\b',
        r'\b(miles morales|miles|ultimate spider-?man)\b',
        r'\b(silk|cindy moon)\b',
        r'\b(spider-?man 2099|miguel o\'?hara)\b',
        r'\b(venom|eddie brock)\b',
        r'\b(groot|i am groot)\b',
        r'\b(rocket raccoon|rocket)\b',
        r'\b(star-?lord|peter quill)\b',
        r'\b(gamora|deadliest woman)\b',
        r'\b(drax|the destroyer)\b',
        r'\b(nebula|blue meanie)\b',
        r'\b(adam warlock|adam)\b',
        r'\b(maria hill|agent hill)\b',
        r'\b(ironheart|riri williams)\b',
        r'\b(x-?23|laura kinney)\b',
        r'\b(jubilee|jubilation lee)\b',
        r'\b(bishop|lucas bishop)\b',
        
        # Marvel Champions specific nickname patterns
        r'\b(cap marvel|capmarv)\b',  # Captain Marvel nicknames
        r'\b(panther)\b',  # Black Panther nickname
        r'\b(spidey)\b',  # Spider-Man nickname
        r'\b(wolverine|wolvie|logan)\b',  # Wolverine variations
        r'\b(drax)\b',  # Drax nickname
        
        # Pattern for "Hero vs Villain" format
        r'\b([a-z\-\s]+)\s+vs?\s+[a-z\-\s]+\b',
        
        # Pattern for "Hero (Aspect)" format
        r'\b([a-z\-\s]+)\s*\([^)]*(?:aggression|justice|protection|leadership|pool)[^)]*\)',
        
        # Pattern for "Hero - Aspect" format  
        r'\b([a-z\-\s]+)\s*[-–]\s*(?:aggression|justice|protection|leadership|pool)\b',
        
        # Pattern for aspect notation like "Justice／She-hulk"
        r'(?:aggression|justice|protection|leadership|pool)／([a-z\-\s]+)',
        r'([a-z\-\s]+)／(?:aggression|justice|protection|leadership|pool)',
        
        # Pattern for hero combinations with "&" or "and"
        r'\b([a-z\-\s]+)\s*[&+]\s*([a-z\-\s]+)',
        
        # Pattern for hero lists with commas
        r'\b([a-z\-\s]+),\s*([a-z\-\s]+)(?:,\s*([a-z\-\s]+))?',
        
        # Pattern for "Hero x Villain" format (x as vs)
        r'\b([a-z\-\s]+)\s+x\s+[a-z\-\s]+\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, comment_lower, re.IGNORECASE)
        for match in matches:
            # Handle both single matches and tuple matches (from multiple capture groups)
            match_list = []
            if isinstance(match, tuple):
                # Multiple capture groups - process each non-empty group
                match_list = [m for m in match if m and m.strip()]
            else:
                # Single match
                match_list = [match] if match and match.strip() else []
            
            for hero_candidate in match_list:
                # Clean up the match
                hero_name = hero_candidate.strip()
                if not hero_name or len(hero_name) < 3:
                    continue
                    
                # Skip common non-hero words
                skip_words = {'with', 'and', 'the', 'vs', 'against', 'lose', 'lost', 'win', 'won', 
                             'play', 'played', 'game', 'solo', 'duo', 'team', 'mode', 'standard', 
                             'expert', 'heroic', 'campaign', 'scenario', 'deck', 'card', 'pack',
                             'experto', 'normal', 'oturum', 'kazandik', 'kazandık'}
                if hero_name.lower() in skip_words:
                    continue
                    
                # Try to match against known heroes
                official_match, is_official, is_fuzzy, is_altered = match_to_official_hero(hero_name)
                if is_official or is_fuzzy:
                    heroes_found.append({
                        'original': hero_candidate,
                        'cleaned': hero_name,
                        'matched': official_match,
                        'is_official': is_official,
                        'is_fuzzy': is_fuzzy,
                        'is_altered': is_altered,
                        'pattern': pattern
                    })
                    
                    if TERMINAL_DEBUG:
                        if is_official:
                            colored_print(f"    ✅ Found hero in comments: '{hero_candidate}' → '{official_match}'", Colors.GREEN)
                        elif is_fuzzy:
                            colored_print(f"    🎯 Fuzzy match in comments: '{hero_candidate}' → '{official_match}'", Colors.BLUE)
    
    # Remove duplicates based on matched hero name
    seen = set()
    unique_heroes = []
    for hero in heroes_found:
        if hero['matched'] not in seen:
            seen.add(hero['matched'])
            unique_heroes.append(hero)
    
    if TERMINAL_DEBUG and unique_heroes:
        colored_print(f"    📝 Total unique heroes found in comments: {len(unique_heroes)}", Colors.CYAN)
        
    return unique_heroes

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
        hero_results, skipped_plays, extraction_stats = extract_hero_names_from_plays(user_plays)
        colored_print(f"\n🎯 Hero usage analysis for user {first_userid} (with official matching):", Colors.BOLD)
        
        # Print top 30 hero results with enhanced AH tracking
        for i, hero in enumerate(hero_results[:30]):
            altered_info = ""
            if hero.get('altered_plays', 0) > 0:
                altered_info = f" (🔄 {hero['altered_plays']} AH)"
            print(f"{i+1:2d}. {hero['hero_name']:<20} {hero['play_count']:>3} plays [{hero['status']}]{altered_info}")
        
        # Show comprehensive summary statistics with colors including all categories
        total_plays = sum(hero['play_count'] for hero in hero_results)
        official_plays = sum(hero['play_count'] for hero in hero_results if 'OFFICIAL' in hero['status'])
        translated_plays = sum(hero['play_count'] for hero in hero_results if 'TRANSLATED' in hero['status'])
        unmatched_plays = sum(hero['play_count'] for hero in hero_results if 'UNMATCHED' in hero['status'])
        altered_plays = sum(hero['play_count'] for hero in hero_results if 'ALTERED_HERO' in hero['status'])
        
        # Calculate skipped player records (not plays) totals
        total_skipped_player_records = sum(len(category_list) for category_list in [
            skipped_plays.get('no_players', []),
            skipped_plays.get('empty_color', []), 
            skipped_plays.get('meaningless_names', []),
            skipped_plays.get('villains', []),
            skipped_plays.get('translation_errors', [])
        ])
        
        # Get individual skipped categories (these are player records, not plays)
        skipped_no_players = len(skipped_plays.get('no_players', []))
        skipped_empty_color = len(skipped_plays.get('empty_color', []))
        skipped_meaningless = len(skipped_plays.get('meaningless_names', []))
        skipped_villains = len(skipped_plays.get('villains', []))
        skipped_translation_errors = len(skipped_plays.get('translation_errors', []))
        
        # Total BGG plays from initial fetch
        total_bgg_plays = len(user_plays)
        
        # Use the accurate statistics from the extraction function
        plays_with_hero_data = extraction_stats['plays_with_players']
        plays_without_hero_data = total_bgg_plays - plays_with_hero_data
        
        colored_print(f"\n📊 BGG Marvel Champions Analysis Summary:", Colors.BOLD)
        colored_print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.CYAN)
        
        # Calculate key totals
        total_player_records = extraction_stats['total_players']
        successful_player_records = extraction_stats['total_players_with_color']
        
        # Main baseline metrics
        colored_print(f"📋 BASELINE DATA:", Colors.BOLD)
        colored_print(f"   • Total BGG plays analyzed: {total_bgg_plays}", Colors.CYAN)
        colored_print(f"   • Total player records found: {total_player_records}", Colors.CYAN)
        
        # BGG Play-level success rates (out of {total_bgg_plays} plays)
        colored_print(f"\n🎯 BGG PLAY SUCCESS RATES (of {total_bgg_plays} plays):", Colors.BOLD)
        colored_print(f"   • Plays with hero data extracted: {plays_with_hero_data} ({plays_with_hero_data/total_bgg_plays*100:.1f}%)" if total_bgg_plays > 0 else "   • Plays with hero data: 0 (0.0%)", Colors.GREEN)
        colored_print(f"   • Plays with no usable data: {plays_without_hero_data} ({plays_without_hero_data/total_bgg_plays*100:.1f}%)" if total_bgg_plays > 0 else "   • Plays with no data: 0 (0.0%)", Colors.YELLOW)
        
        # Player Record-level success rates (out of {total_player_records} player records)
        colored_print(f"\n👥 PLAYER RECORD SUCCESS RATES (of {total_player_records} player records):", Colors.BOLD)
        colored_print(f"   • Successfully resolved hero data: {successful_player_records} ({successful_player_records/total_player_records*100:.1f}%)" if total_player_records > 0 else "   • Successful resolutions: 0 (0.0%)", Colors.GREEN)
        
        # Breakdown of unsuccessful player records
        skipped_player_records = total_player_records - successful_player_records
        colored_print(f"   • Player records skipped: {skipped_player_records} ({skipped_player_records/total_player_records*100:.1f}%)" if total_player_records > 0 else "   • Records skipped: 0 (0.0%)", Colors.YELLOW)
        
        # Detailed skip reasons (of skipped player records)
        if skipped_player_records > 0:
            colored_print(f"     ├─ Empty color field: {skipped_empty_color} ({skipped_empty_color/total_player_records*100:.1f}% of all records)", Colors.MAGENTA)
            colored_print(f"     ├─ Meaningless names: {skipped_meaningless} ({skipped_meaningless/total_player_records*100:.1f}% of all records)", Colors.MAGENTA)
            colored_print(f"     ├─ Villains filtered: {skipped_villains} ({skipped_villains/total_player_records*100:.1f}% of all records)", Colors.MAGENTA)
            colored_print(f"     └─ Translation errors: {skipped_translation_errors} ({skipped_translation_errors/total_player_records*100:.1f}% of all records)", Colors.MAGENTA)
        
        # Additional: Entire plays with no player data (separate category)
        colored_print(f"   • Entire plays with no player element: {skipped_no_players} ({skipped_no_players/total_bgg_plays*100:.1f}% of BGG plays)" if total_bgg_plays > 0 else "   • No player element: 0 (0.0%)", Colors.MAGENTA)
        
        # Hero extraction quality (of successfully extracted heroes)
        colored_print(f"\n✅ HERO EXTRACTION QUALITY (of {total_plays} hero plays):", Colors.BOLD)
        colored_print(f"   • Official matches: {official_plays} ({official_plays/total_plays*100:.1f}%)" if total_plays > 0 else "   • Official matches: 0 (0.0%)", Colors.GREEN)
        colored_print(f"   • Translated names: {translated_plays} ({translated_plays/total_plays*100:.1f}%)" if total_plays > 0 else "   • Translated: 0 (0.0%)", Colors.YELLOW)
        colored_print(f"   • Altered Heroes (AH): {altered_plays} ({altered_plays/total_plays*100:.1f}%)" if total_plays > 0 else "   • Altered Heroes: 0 (0.0%)", Colors.BLUE)
        colored_print(f"   • Unmatched heroes: {unmatched_plays} ({unmatched_plays/total_plays*100:.1f}%)" if total_plays > 0 else "   • Unmatched: 0 (0.0%)", Colors.RED)
        
        # Key performance metrics
        hero_processing_success_rate = (official_plays + translated_plays + altered_plays) / total_plays * 100 if total_plays > 0 else 0
        
        # Count plays recovered from comments (look for FROM_COMMENTS in hero statuses)
        comment_recovered_plays = 0
        for hero_entry in hero_results:
            if 'FROM_COMMENTS' in hero_entry.get('status', ''):
                comment_recovered_plays += hero_entry.get('play_count', 0)
        
        colored_print(f"\n📈 KEY PERFORMANCE METRICS:", Colors.BOLD)
        colored_print(f"   • Overall hero processing success: {hero_processing_success_rate:.1f}% (excludes unmatched)", Colors.CYAN)
        colored_print(f"   • Comment-based recovery: {comment_recovered_plays} hero plays recovered from comments", Colors.CYAN)
        colored_print(f"   • Average hero plays per BGG play: {total_plays/total_bgg_plays:.1f}" if total_bgg_plays > 0 else "   • Average hero plays per play: 0.0", Colors.CYAN)
        
        colored_print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.CYAN)
        
        # Also show comment-based analysis for comparison
        comment_results = extract_hero_mentions_from_plays(user_plays)
        colored_print(f"\n💬 Comment-based analysis for comparison:", Colors.BOLD)
        for i, hero in enumerate(comment_results[:5]):
            print(f"{i+1}. {hero['hero_name']:<15} {hero['mention_count']:>3} mentions")
    else:
        colored_print(f"❌ No plays found for user {first_userid}", Colors.RED)
else:
    print("No users found in recent plays")
