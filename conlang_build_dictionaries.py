import json
import logging
import argparse
from conlang_engine import ConlangEngine
from conlang_data_loader import process_entry, report_unmapped_pos
from conlang_language_paths import (get_build_data_file, get_template_file, 
                            get_dictionary_file, get_dict_txt_file,
                            get_suffixes_file, get_missing_tags_file)

# Maps English suffixes to grammar concepts (morphology defined in template JSON)
# Order matters: longer suffixes first to avoid partial matches
# Format: (suffix, grammar_type, replacement_to_get_root)
SUFFIX_MAP = [
    ("ies", "plural", "y"),      # carries -> carry
    ("ing", "continuous", ""),   # running -> run
    ("ing", "continuous", "e"),  # making -> make
    ("est", "superlative", ""),  # fastest -> fast
    ("ers", "agent", ""),        # runners -> runner (plural agent)
    ("ed", "past_tense", ""),     # walked -> walk
    ("ed", "past_tense", "e"),    # created -> create
    ("es", "plural", ""),        # boxes -> box
    ("er", "agent", ""),         # runner -> run
    ("er", "comparative", ""),   # faster -> fast (for adjectives)
    ("or", "agent", ""),         # actor -> act
    ("s", "plural", ""),         # cats -> cat
]

parser = argparse.ArgumentParser(description='Process the input file and generate a dictionary output.')
parser.add_argument('--source', type=str, help='Input file (overrides language)')
parser.add_argument('--engine', type=str, help='Conlang engine configuration file (overrides language)')
parser.add_argument('--output', type=str, help='Output file (overrides language)')
parser.add_argument('--language', type=str, default='default', help='Language name')
parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')


args = parser.parse_args()

seed = args.seed if args.seed else None

language = args.language

# Use language_paths unless explicitly overridden
source_file = args.source or get_build_data_file(language)
engine_config = args.engine or get_template_file(language)
output_data_file = args.output or get_dictionary_file(language)
output_dict_file = get_dict_txt_file(language)


def detect_suffix(word):
    """
    Detect if a word has a grammatical suffix.
    Returns: (root_candidates, grammar_type) or (None, None) if no suffix detected.
    """
    word_lower = word.lower()
    for suffix, grammar_type, replacement in SUFFIX_MAP:
        if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 1:
            root = word_lower[:-len(suffix)] + replacement
            if not replacement and len(root) > 2 and root[-1] == root[-2]:
                return [root, root[:-1]], grammar_type
            return [root], grammar_type
    return None, None


def find_root_in_source(root_candidates, source_data):
    """Find a root word key in the source data."""
    for root in root_candidates:
        for key in source_data.keys():
            if key.split('.')[0].lower() == root:
                return key
    return None


def blend_with_grammar(base_tags, grammar_type, morphology):
    """Blend base word tags with grammar anchor from template morphology."""
    morph_def = morphology.get(grammar_type)
    if not morph_def or not isinstance(morph_def, dict):
        return base_tags
    
    anchor = morph_def.get("anchor", "")
    if not anchor:
        return base_tags
    
    blended = dict(base_tags)
    # Add the grammar anchor with moderate weight
    blended[anchor] = blended.get(anchor, 0) + 1.5
    return blended


def main():
    engine = ConlangEngine(engine_config, seed)
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    print(f"Processing {source_file}: {len(source_data)} entries...")
    
    dictionary_output = {}
    words = {}
    dict_counter = {}
    
    # Cache for root words: stem -> (generated_word, engine_inputs)
    root_cache = {}
    # Cache for grammar suffixes: grammar_type -> generated_suffix
    suffix_cache = {}
    # Track derived words
    derived_count = 0
    
    # Separate entries into roots and derived
    root_entries = []
    derived_entries = []
    
    for key, entry in source_data.items():
        word_stem = key.split('.')[0].lower()
        root_candidates, grammar_type = detect_suffix(word_stem)
        
        if root_candidates and grammar_type:
            derived_entries.append((key, entry, root_candidates, grammar_type))
        else:
            root_entries.append((key, entry))
    
    print(f"  Pass 1: {len(root_entries)} root words")
    print(f"  Pass 2: {len(derived_entries)} derived words")
    print(f"  Morphology loaded: {list(engine.morphology.keys())}")
    
    # === PASS 1: Process root words first ===
    for key, entry in root_entries:
        word_stem = key.split('.')[0].lower()
        engine_inputs = process_entry(key, entry)
        
        if not engine_inputs:
            logging.warning(f"Skipping {key}: Could not derive tags.")
            continue

        try:
            word = engine.generate(engine_inputs)
            # Cache this as a potential root
            root_cache[word_stem] = (word, engine_inputs)
        except Exception as e:
            print(f"Failed {key}: {e}")
            exit()
        
        if word is None:
            print(f"Word generation failure: {word} {engine_inputs}")
            exit()
        
        dict_counter[word] = dict_counter.get(word, 0) + 1
        words[key] = word
        
        dictionary_output[key] = {
            "word": word,
            "definition": entry.get("definition"),
            "origin": engine_inputs,
            "derived": False
        }
    
    print(f"  Pass 1 complete: {len(root_cache)} roots cached")
    
    # === PASS 2: Process derived words using cached roots ===
    for key, entry, root_candidates, grammar_type in derived_entries:
        word_stem = key.split('.')[0].lower()
        
        # Try to find root in cache
        root_word = None
        root_inputs = None
        
        for candidate in root_candidates:
            if candidate in root_cache:
                root_word, root_inputs = root_cache[candidate]
                break
        
        # If we have a root, derive the inflected form
        if root_word and root_inputs:
            # Generate or retrieve suffix for this grammar type
            if grammar_type not in suffix_cache:
                suffix = engine.generate_suffix(grammar_type)
                suffix_cache[grammar_type] = suffix
                print(f"  Generated suffix for '{grammar_type}': '{suffix}'")
            else:
                suffix = suffix_cache[grammar_type]
            
            # Combine root + suffix
            word = root_word + suffix
            derived_count += 1
            engine_inputs = blend_with_grammar(root_inputs, grammar_type, engine.morphology)
        else:
            # No root found - generate normally
            engine_inputs = process_entry(key, entry)
            
            if not engine_inputs:
                logging.warning(f"Skipping {key}: Could not derive tags.")
                continue

            try:
                word = engine.generate(engine_inputs)
            except Exception as e:
                print(f"Failed {key}: {e}")
                exit()
        
        if word is None:
            print(f"Word generation failure: {word} {engine_inputs}")
            exit()
        
        dict_counter[word] = dict_counter.get(word, 0) + 1
        words[key] = word
        
        dictionary_output[key] = {
            "word": word,
            "definition": entry.get("definition"),
            "origin": engine_inputs,
            "derived": root_word is not None
        }
    
    print(f"Derived {derived_count} words from roots using grammar suffixes")

    # Save suffix map for translator
    suffix_file = get_suffixes_file(language)
    if suffix_cache:
        print(f"Saving suffix map to {suffix_file}: {suffix_cache}")
        with open(suffix_file, 'w', encoding='utf-8') as f:
            json.dump(suffix_cache, f, indent=2)
    
    f = open(output_dict_file,"w",-1,'utf-8')

    for word in words:
        f.write(f"{word}:{words[word]}\n")

    f.write("-"*80)
    base_words = {}
    for word in words:
        base = word.split(".")[0]
        base_words[base] = base
        f.write(f"{words[word]}:{word}\n")
    f.close()

    f = open("language_data/words.txt","r")
    words = [word.strip() for word in f.readlines()]
    f.close()

    # for word in words:
    #     #this says everything is missing ??
    #     if not base_words.get(word):
    #         print("missing:",word)


    # Add metadata for reproducibility
    from datetime import datetime
    dictionary_output["_meta"] = {
        "seed": seed,
        "generated": datetime.now().isoformat(),
        "language": language,
        "source_file": source_file,
        "engine_config": engine_config
    }
    
    print(f"Dictionary saved to {output_data_file}")
    with open(output_data_file, 'w') as f:
        json.dump(dictionary_output, f, indent=2)
    
    # Report missing tags and unmapped POS
    engine.report_missing_tags(get_missing_tags_file(language))
    report_unmapped_pos()


if __name__ == "__main__":
    main()