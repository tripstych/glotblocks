import logging

# --- CONFIGURATION ---
POS_MAP = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "satellite",  # Satellite adjectives - separate from regular adjectives
    "r": "adverb"
}

# Manual overrides for function words WordNet misses or messes up
SPECIAL_CASES = {
    # Articles / Determiners -> often treated as 'adjectives' or 'particles'
    "the":  "particle",
    "a":    "particle",
    "an":   "particle",
    
    # Prepositions -> connectors
    "from": "preposition",
    "to":   "preposition",
    "in":   "preposition",
    "on":   "preposition",
    "at":   "preposition",
    "with": "preposition",
    
    # Pronouns / Interrogatives
    "what": "pronoun",
    "who":  "pronoun",
    "it":   "pronoun",
    "he":   "pronoun",
    "she":  "pronoun",
    "they": "pronoun",
    "we":   "pronoun",
    "i":    "pronoun",
    "you":  "pronoun",
    "this": "pronoun",
    "that": "pronoun",
    
    # Conjunctions (FANBOYS: for, and, nor, but, or, yet, so)
    "for":  "conjunction",
    "and":  "conjunction",
    "nor":  "conjunction",
    "but":  "conjunction",
    "or":   "conjunction",
    "yet":  "conjunction",
    "so":   "conjunction",
    
    # Interrogatives
    "how":  "adverb",
    "why":  "adverb",
    "when": "adverb",
    "where": "adverb"
}

# Track unmapped POS tags
UNMAPPED_POS = {}  # {pos: count}
# The new "Influencer" triggers (White Label friendly)
TECH_TRIGGERS = [
    "comput", "digit", "electr", "cyber", "mechan", 
    "techno", "screen", "code", "data", "robot", "server", "net"
]

def process_entry(key, data_entry=None):
    """
    Turns raw WordNet data into Engine Tags with flexible layers.
    
    Args:
        key (str): The WordNet key (e.g., "fire.n.01", "computer.n.01")
        data_entry (dict): The value from elemental_source.json (contains "spirit").
                           If None, we try to derive everything from the key.
                           
    Returns:
        dict: A dictionary of tags and weights { 'fire': 4.0, 'noun': 1.0, 'metal': 4.0 }
    """
    tags = {}
    word_stem = ""
    
    # --- 0. EXTRACT RAW WORD ---
    parts = key.split('.')
    word_stem = parts[0].lower() if parts else ""
    
    # --- 1. CHECK SPECIAL CASES (Override for function words) ---
    if word_stem in SPECIAL_CASES:
        special_pos = SPECIAL_CASES[word_stem]
        tags[special_pos] = 1.0
        
        # Add spirit from data_entry if available
        if data_entry and isinstance(data_entry, dict) and "spirit" in data_entry:
            spirit = data_entry.get("spirit")
            if spirit:
                tags[spirit] = 4.0
        
        return tags
    
    # --- 2. PARSE THE KEY (Grammar & Stem) ---
    # Expected format: "word.pos.id" (fire.n.01) or just "word"
    if len(parts) >= 2:
        raw_pos = parts[1]
        
        # Map single letter POS to full tag
        ontology_pos = POS_MAP.get(raw_pos)
        if ontology_pos:
            tags[ontology_pos] = 1.0
        else:
            # Track unmapped POS
            UNMAPPED_POS[raw_pos] = UNMAPPED_POS.get(raw_pos, 0) + 1
            print(f"WARNING: Unmapped POS '{raw_pos}' in key '{key}'")
    else:
        # No POS in key (e.g., words not in WordNet like "the", "aaliyah")
        # Default to noun so we have syllable shapes available
        tags["noun"] = 1.0
            
    # --- 2. DETERMINE CORE CONCEPT (The "Spirit") ---
    # If we have explicit data (must be a dict), use it.
    if data_entry and isinstance(data_entry, dict) and "spirit" in data_entry:
        spirit = data_entry.get("spirit")
        if spirit:  # Skip empty strings
            tags[spirit] = 4.0
        
        # (Optional) Add existing composition nuances
        # This preserves manual tweaks from your JSON file
        for elem, score in data_entry.get("composition", {}).items():
            if elem and elem != spirit and score > 20:
                # Normalize 0-63 score to a small weight (approx 0.5 - 1.5)
                tags[elem] = (score / 63.0) * 1.5

    # If NO data_entry, fall back to the word itself as the concept
    else:
        if word_stem:  # Only add if not empty
            tags[word_stem] = 4.0 # High weight for the core concept
        
    # --- 3. APPLY FLEXIBLE LAYERS ("Metal" Check) ---
    # This fixes the specific "computer" issue. 
    # We check the stem regardless of whether data_entry existed or not.
    
    if any(trigger in word_stem for trigger in TECH_TRIGGERS):
        # We found a tech word! 
        # Add 'metal' or boost it if it's already there.
        tags['metal'] = 4.0 
        
        # Optional: If you want tech words to be LESS "Earthy", you could punish Earth here
        # if 'earth' in tags: tags['earth'] *= 0.5

    return tags

def report_unmapped_pos():
    """Report all unmapped POS tags."""
    if UNMAPPED_POS:
        print(f"\n--- UNMAPPED POS TAGS ({len(UNMAPPED_POS)} unique) ---")
        for pos, count in sorted(UNMAPPED_POS.items(), key=lambda x: -x[1]):
            print(f"  '{pos}': {count}")
    else:
        print("No unmapped POS tags.")

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Test 1: Standard Element (Fire)
    print("Test 1 (Fire):", process_entry("fire.n.01"))
    
    # Test 2: The "Computer" Fix
    # Even without a data_entry, this should now detect 'metal' via the stem
    print("Test 2 (Computer):", process_entry("computer.n.01"))
    
    # Test 3: Existing Data Entry
    dummy_data = {"spirit": "water", "composition": {"earth": 30}}
    print("Test 3 (With Data):", process_entry("lake.n.01", dummy_data))
