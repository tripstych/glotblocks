import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*Evaluating Doc.similarity based on empty vectors.*")

import math
import json
import random
import numpy as np
import argparse
from tqdm import tqdm
import spacy
from collections import Counter
from itertools import combinations
from wordfreq import zipf_frequency, top_n_list
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet as wn
import en_core_web_lg
from conlang_language_paths import get_anchors_file, get_build_data_file

results = {}
# 2. PHONETIC MAPPING (Base-4 Conlang)
anchors = {}


# Parse command line arguments
parser = argparse.ArgumentParser(description='Build elemental dictionary with optional custom anchors')
parser.add_argument('--anchors', type=str, help='JSON file concept anchors dictionary (overrides language)')
parser.add_argument('--output', type=str, help='Output file name (overrides language)')
parser.add_argument('--words', default="words.txt", help="Spelling dictionary")
parser.add_argument('--language', default="default", help="Language name")

args, unknown = parser.parse_known_args()

# Use language_paths unless explicitly overridden
if args.anchors:
    anchors_file = args.anchors
else:
    anchors_file = get_anchors_file(args.language)

if args.output:
    output_file = args.output
else:
    output_file = get_build_data_file(args.language)


nlp = en_core_web_lg.load(disable=["tagger", "parser", "ner", "lemmatizer", "attribute_ruler"])

# Load custom anchors if provided, otherwise use default
try:
    with open(anchors_file, 'r', encoding='utf-8') as f:
        custom_anchors = json.load(f)
    # Validate that it's a proper anchors dictionary
    if isinstance(custom_anchors, dict) and all(isinstance(v, list) for v in custom_anchors.values()):
        anchors = custom_anchors
        print(f"Loaded custom anchors from {anchors_file}")
    else:
        print(f"Invalid anchors format in {anchors_file}, using default anchors")
except FileNotFoundError:
    print(f"Anchor file {anchors_file} not found, using default anchors")
except json.JSONDecodeError as e:
    print(f"Error parsing anchors file {anchors_file}: {e}, using default anchors")

ANCHOR_DOCS = {k: list(nlp.pipe(v, batch_size=64)) for k, v in anchors.items()}

def log_scale(value, in_min=0.2, in_max=0.8, out_max=63):
    """Map value from [in_min, in_max] to [0, out_max] using log scale"""
    if in_min <= 0 or in_max <= 0 or in_min >= in_max:
        return 0
    if value <= in_min:
        return 0
    if value >= in_max:
        return out_max

    log_min = math.log(in_min)
    log_max = math.log(in_max)
    denom = (log_max - log_min)
    if denom == 0:
        return 0
    scale = (math.log(value) - log_min) / denom
    scaled = int(round(scale * out_max))
    if scaled < 0:
        return 0
    if scaled > out_max:
        return out_max
    return scaled

def normalize_compositions(results_dict, out_max=63):
    """Analyze all composition values and apply shifted log scale based on actual data distribution"""
    # Collect all raw similarity values
    all_values = []
    for entry in results_dict.values():
        all_values.extend(entry['composition'].values())
    
    if not all_values:
        return results_dict
    
    all_values = np.array(all_values)
    
    # Find the low and high clusters using percentiles to avoid outlier influence
    in_min = np.percentile(all_values, 5)   # 5th percentile as low cluster
    in_max = np.percentile(all_values, 95)  # 95th percentile as high cluster
    
    # Ensure valid range
    if in_min <= 0:
        in_min = 0.01
    if in_max <= in_min:
        in_max = in_min + 0.01
    
    print(f"\nNormalizing compositions: in_min={in_min:.4f}, in_max={in_max:.4f}")
    
    # Apply log scale to all compositions
    for name, entry in results_dict.items():
        normalized = {}
        for key, val in entry['composition'].items():
            normalized[key] = log_scale(val, in_min=in_min, in_max=in_max, out_max=out_max)
        entry['composition'] = normalized
    
    return results_dict

def process_word(word):
    bump = 15 
    synsets = wn.synsets(word)
    
    # Handle words not in WordNet (function words like "the", "a", etc.)
    if not synsets:
        doc = nlp(word)
        composition = {key: 0.0 for key in anchors}
        closest = ""
        max_sim = 0
        for key in anchors:
            key_max_sim = 0.0
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if sim > key_max_sim:
                    key_max_sim = sim
            composition[key] = key_max_sim  # Store raw similarity
            if key_max_sim > max_sim:
                max_sim = key_max_sim
                closest = key
        
        data = {'spirit': closest, 'composition': composition, 'definition': word}
        results[word] = data
        total = len(results.keys())
        print(f"Processed {total} {word} (no synsets)" + " " * 20, end="\r")
        return True

    # We don't need a global 'skipword' flag or 'final_composition'
    # We process and save each valid synonym individually.
    
    for syn in synsets:
        name = syn.name()
        if len(name.split("_"))>2:
            continue
        nameparts = name.split('.')
        
        # 1. Skip ONLY the specific bad synset, not the whole word
        if len(nameparts) > 3:
            continue

        type = name.split('.')[1]
        defn = syn.definition()
        sword = word*3
        doc = nlp(sword+" "+defn)

        composition = {key: 0.0 for key in anchors}
        closest = ""
        max_sim = 0
        for key in anchors:
            key_max_sim = 0.0
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if sim > key_max_sim:
                    key_max_sim = sim
            composition[key] = key_max_sim  # Store raw similarity
            if key_max_sim > max_sim:
                max_sim = key_max_sim
                closest = key
        
        # 2. Save IMMEDIATELY inside the loop
        data = { 'spirit': closest, 'composition': composition, 'definition': defn}
        results[name] = data
        total = len(results.keys())
        print(f"Processed {total} {name}"+" "*20, end="\r")
        
        # Optional: Print progress per added synset if you want, 
        # or just keep the print in the main loop to reduce spam.
    
    return True

def _process_word(word):
    bump = 15 # bump for word types

    synsets = wn.synsets(word)
    if not synsets:
        return None

    final_composition = None
    skipword = False
    for syn in synsets:
        name = syn.name()
        nameparts = name.split('.')
        if len(nameparts)>3:
            skipword = True
            continue

        type = name.split('.')[1]
        defn = syn.definition()
        doc = nlp(defn)

        composition = {}
        for key in anchors:
            max_sim = -1.0
            for anchor_doc in ANCHOR_DOCS[key]:
                sim = doc.similarity(anchor_doc)
                if sim > max_sim:
                    max_sim = sim
            composition[key] = log_scale(max_sim)

        #DEFUNCT
        # if type == 'v':
        #     composition['air'] = max(64, composition['air'] + bump)
        # if type == 'n':
        #     composition['earth'] = max(64, composition['earth'] + bump)
        # if type == 'a':
        #     composition['water'] = max(64, composition['water'] + bump)
        # if type == 'r':
        #     composition['fire'] = max(64, composition['fire'] + bump)
        final_composition = composition

    if skipword:
        return
    data = { 'composition': final_composition, 'definition': defn}
    results[name] = data
    total = len(results.keys())
    print(f"Processed {total} {name}____________", end="\r")
    return data

def main():
    # Read words from file
    try:
        with open(f"language_data/{args.words}", 'r') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: words.txt not found in the current directory",end="\r")
        return
    
    # Process each word
    total_words = len(words)
    print(f"Processing {total_words} words...", end="\r")
    ft = open(".tmp.counter","w")
    for i, word in enumerate(words, 1):
        ft.seek(0)
        ft.truncate()
        ft.write(f"{len(results)} entries")
        ft.flush()
        process_word(word)
    ft.seek(0)
    ft.truncate()
    ft.write("done")
    ft.close()

    # Normalize compositions based on actual data distribution
    normalize_compositions(results)
    
    print(f"Saving {output_file}:",len(results.keys()))
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Final sweep: check for missing words (using spaCy lemmatization + suffix stripping)
    generated_bases = set()
    for key in results.keys():
        base = key.split('.')[0].lower()
        generated_bases.add(base)
    
    def get_possible_bases(word):
        """Get possible base forms of a word."""
        bases = {word}
        # spaCy lemma
        doc = nlp(word)
        if doc:
            bases.add(doc[0].lemma_.lower())
        # Common suffix patterns
        suffixes = [
            ('ies', 'y'), ('es', ''), ('s', ''),  # plurals
            ('ed', ''), ('ed', 'e'), ('ing', ''), ('ing', 'e'),  # verbs
            ('ly', ''), ('ness', ''), ('ment', ''), ('tion', ''),  # derivational
            ('er', ''), ('est', ''), ('ers', ''),  # comparatives
        ]
        for suffix, replacement in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                bases.add(word[:-len(suffix)] + replacement)
        return bases
    
    missing = []
    for word in words:
        w = word.lower()
        # Check if any possible base form exists
        if not get_possible_bases(w) & generated_bases:
            missing.append(word)
    
    if missing:
        missing_file = output_file.replace('.json', '_missing.txt')
        with open(missing_file, 'w', encoding='utf-8') as f:
            for word in missing:
                f.write(f"{word}\n")
        print(f"\nMissing words: {len(missing)} (saved to {missing_file})")
        if len(missing) <= 20:
            print(f"  {', '.join(missing)}")
    else:
        print("\nNo missing words!")
    
    
if __name__ == "__main__":
    main()
