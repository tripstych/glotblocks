import json
import os
import random
import re
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union, Pattern


class ConlangEngine:
    """
    Ontological Word Generator using an additive blender approach.

    - Loads configuration from a JSON file with sections: definitions, constraints, orthography, ontology.
    - Supports weighted blending: Inputs can be a list of tags or a dict of {tag: scalar_weight}.
    - CRITICAL: Raises exceptions if tags are missing or generation fails (Fail Fast).
    """

    def __init__(self, json_path: str, seed: int = None):
        self.json_path = json_path
        self.config = self._load_config(json_path)

        if seed is not None:
            random.seed(seed)


        self.lexicon = {} 

        # Sections (with safe defaults)
        self.definitions: Dict[str, List[str]] = self.config.get("definitions", {})
        self.constraints_raw: Dict[str, Union[str, Dict]] = self.config.get("constraints", {})
        self.orthography: Dict[str, List[Dict[str, str]]] = self.config.get("orthography", {})
        self.ontology: Dict[str, Dict] = self.config.get("ontology", {})
        
        # Extract morphology definitions from definitions section
        self.morphology: Dict[str, Dict] = self.definitions.pop("morphology", {})

        # Compile constraints for performance
        self.constraints: Dict[str, List[Pattern]] = {}
        self._compile_constraints()

        self.lexicton = Dict[str, Dict]
        #test bed
        self.shadow_lexicton = Dict[str, Dict]
        
        # Track missing tags for debugging
        self.missing_tags = {}  # {tag: count}

        # Prepare quick lookup for phoneme classification within definitions
        # Map phoneme -> set(def_keys) it belongs to
        self._phoneme_to_defs: Dict[str, set] = defaultdict(set)
        for def_key, items in self.definitions.items():
            for phon in items:
                self._phoneme_to_defs[phon].add(def_key)

    def _load_config(self, path: str) -> Dict:
        print(f"Loading config from {path}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compile_constraints(self):
        """Helper to pre-compile all regex patterns from the JSON."""
        for name, spec in self.constraints_raw.items():
            compiled_list: List[Pattern] = []

            def _compile_one(pat: str, flags: int = 0) -> Optional[Pattern]:
                try:
                    return re.compile(pat, flags)
                except re.error as e:
                    logging.warning(f"Invalid regex for constraint '{name}': {e}")
                    return None

            # Normalize spec to list of definitions
            spec_list = spec if isinstance(spec, list) else [spec]
            
            for item in spec_list:
                pat_str = None
                flags_val = 0
                
                if isinstance(item, str):
                    pat_str = item
                elif isinstance(item, dict):
                    pat_str = item.get("pattern") or item.get("regex")
                    # Basic flag support
                    if item.get("flags") and "i" in str(item.get("flags")).lower():
                        flags_val = re.IGNORECASE

                if pat_str:
                    pat = _compile_one(pat_str, flags_val)
                    if pat:
                        compiled_list.append(pat)

            if compiled_list:
                self.constraints[name] = compiled_list

    
    def _aggregate(self, tags_input: Union[List[str], Dict[str, float]]) -> Tuple[Dict, Dict, List, List]:
        """
        Builds weighted pools based on tags.
        - POS tags (Noun/Verb) provide shapes/rules.
        - Element tags (Fire/Water) provide sounds.
        - If sounds are missing at the end, defaults (C/V) are injected.
        """
        
        # 1. Normalize input to {tag: multiplier}
        if isinstance(tags_input, list):
            active_tags = {tag: 1.0 for tag in tags_input}
        elif isinstance(tags_input, dict):
            active_tags = tags_input
        else:
            raise ValueError(f"CRITICAL: Invalid input type for tags: {type(tags_input)}")

        pools: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        shapes_weights: Dict[str, float] = defaultdict(float)
        rules_enabled_order: List[str] = []
        spelling_order: List[str] = []
        rules_seen = set()
        spelling_seen = set()

        # 2. Iterate through all tags (Noun, Fire, etc.)
        for tag, input_scalar in active_tags.items():
            concept = self.ontology.get(tag)
            
            # CRITICAL CHECK: Missing Ontology Key
            if concept is None:
                # Track missing tag
                self.missing_tags[tag] = self.missing_tags.get(tag, 0) + 1
                if input_scalar > 0:
                    print(f"WARNING: Missing tag '{tag}' in ontology (count: {self.missing_tags[tag]})")
                continue

            # Calculate Weight
            base_weight = float(concept.get("weight", 1.0))
            final_weight = base_weight * float(input_scalar)

            if final_weight <= 0:
                continue

            # A. Sounds (From Elements)
            for entry in concept.get("add_sounds", []):
                # 1. Determine phonemes to add
                phonemes_to_add = []
                if entry in self.definitions:
                    phonemes_to_add = self.definitions[entry] # It's a class (e.g., "Liquids")
                else:
                    phonemes_to_add = [entry] # It's a literal (e.g., "l")

                # 2. Add to buckets
                for phon in phonemes_to_add:
                    # Add to specific defined buckets (e.g. 'l' -> 'Liquids', 'C')
                    parent_categories = self._phoneme_to_defs.get(phon, set())
                    if parent_categories:
                        for cat in parent_categories:
                            pools[cat][phon] += final_weight
                    else:
                        # Fallback for unclassified literals
                        pools["any"][phon] += final_weight

            # B. Shapes (From POS)
            for shape in concept.get("add_shapes", []):
                shapes_weights[shape] += final_weight

            # C. Rules (From POS)
            for rule_name in concept.get("add_rules", []):
                if rule_name not in rules_seen:
                    rules_seen.add(rule_name)
                    rules_enabled_order.append(rule_name)

            if "default" in self.orthography:
                spelling_order.append("default")
                spelling_seen.add("default")

            # D. Spelling
            for orth_key in concept.get("add_spelling", []):
                if orth_key not in spelling_seen:
                    spelling_seen.add(orth_key)
                    spelling_order.append(orth_key)

        # 3. SAFETY NET (The "Engine" Logic)
        # If we have shapes (from Noun) but NO sounds (missing Element), 
        # load the generic definitions so generation doesn't crash.
        # This keeps your 'noun' tag clean (it doesn't need to know about sounds).
        if not pools or (not pools.get("C") and not pools.get("any")):
            if "C" in self.definitions:
                for phon in self.definitions["C"]:
                    pools["C"][phon] += 1.0
                    # Also map to specific buckets if needed, or rely on _fill_shape logic
            if "V" in self.definitions:
                for phon in self.definitions["V"]:
                    pools["V"][phon] += 1.0

        return pools, shapes_weights, rules_enabled_order, spelling_order

    def _expand_shape(self, shape_template: str) -> str:
        """
        Parses '(X)' as optional. 
        '(C)V(C)' -> 50% 'CVC', 25% 'VC', 25% 'CV', etc.
        """
        # Finds anything inside parenthesis like (C) or (s)
        # Randomly decides to replace it with the content OR empty string
        return re.sub(r'\(([^)]+)\)', lambda m: random.choice([m.group(1), ""]), shape_template)

    def _choose_shape(self, shapes_weights: Dict[str, float]) -> Optional[str]:
        if not shapes_weights:
            return None
        
        shapes = sorted(shapes_weights.keys())
        weights = [max(shapes_weights[s], 0.0) for s in shapes]
        
        if sum(weights) == 0:
            chosen_template = random.choice(shapes)
        else:
            chosen_template = random.choices(shapes, weights=weights, k=1)[0]
            
        # EXPAND THE TEMPLATE HERE
        return self._expand_shape(chosen_template)

    def _fill_shape(self, shape: str, pools: Dict[str, Dict[str, float]]) -> Optional[str]:
        out = []
        for ch in shape:
            # Candidates: Specific pool + 'any' pool
            slot_pool = pools.get(ch, {})
            any_pool = pools.get("any", {})

            # Gather all unique candidates (sorted for reproducibility with seed)
            candidates = set(slot_pool.keys()) | set(any_pool.keys())
            candidate_list = sorted(candidates)
            
            if not candidate_list:
                return None

            # Calculate weights
            weights = []
            for p in candidate_list:
                w = slot_pool.get(p, 0.0) + any_pool.get(p, 0.0)
                weights.append(w)

            if sum(weights) == 0:
                choice = random.choice(candidate_list)
            else:
                choice = random.choices(candidate_list, weights=weights, k=1)[0]
            out.append(choice)
        return "".join(out)

    def _violates_constraints(self, word: str, rules_enabled: List[str]) -> bool:
        for rule_name in rules_enabled:
            patterns = self.constraints.get(rule_name)
            if not patterns:
                continue
            for pattern in patterns:
                if pattern.search(word):
                    return True
        return False

    def _apply_orthography(self, word: str, spelling_order: List[str]) -> str:
        out = word
        for orth_key in spelling_order:
            rules = self.orthography.get(orth_key)
            if rules is None:
                continue
            for r in rules:
                frm = r.get("from", "")
                to = r.get("to", "")
                if frm:
                    out = out.replace(frm, to)
        return out

    def generate(self, tags: Union[List[str], Dict[str, float]], attempts: int = 100) -> str:
        """
        Generate a word blending the provided tags.
        Raises Exceptions on failure (Missing Blueprint or constraint exhaustion).
        Returns the string word.
        """
        pools, shapes_weights, rules_enabled, spelling_order = self._aggregate(tags)

        # FIX: Safe formatting for error messages (Handle List vs Dict)
        tags_display = list(tags.keys()) if isinstance(tags, dict) else tags

        # --- CRITICAL CHECK 2: NO BLUEPRINT ---
        if not shapes_weights:
            raise RuntimeError(f"CRITICAL ERROR: The tags {tags_display} provided ZERO syllable shapes. Generation is impossible. Check 'add_shapes' in your JSON.")


        seen_words = []
        for _ in range(max(1, int(attempts))):
            shape = self._choose_shape(shapes_weights)
            if not shape:
                continue
            
            word = self._fill_shape(shape, pools)
            if word is None:
                continue
                
            #then what? we'll wind up with the same results
            if self._violates_constraints(word, rules_enabled):
                continue
            
            if self.lexicon.get(word) == False:
                self.lexicon[word] = word
                return word

            word = self._apply_orthography(word, spelling_order)
            if not self.lexicon.get(word):
                self.lexicon[word] = word
                return word

            shape += self._choose_shape(shapes_weights)
            word = self._fill_shape(shape, pools)
            if not self.lexicon.get(word):
                self.lexicon[word] = word
                return word

        # --- CRITICAL CHECK 3: EXHAUSTION ---
        raise RuntimeError(f"CRITICAL ERROR: Failed to generate valid word after {attempts} attempts for tags {tags_display}. Constraints might be too strict or phoneme pools too small.")

    def generate_suffix(self, grammar_type: str, attempts: int = 50) -> str:
        """
        Generate a grammatical suffix based on morphology defined in template.
        Uses the anchor and shape from self.morphology[grammar_type].
        """
        # Look up morphology definition
        morph_def = self.morphology.get(grammar_type)
        if not morph_def or not isinstance(morph_def, dict):
            # Fallback if grammar type not defined
            return "a"
        
        # Get anchor and shape from template
        anchor = morph_def.get("anchor", "")
        shape = morph_def.get("shape", "V")
        
        # Build tags from the anchor to get the right sounds
        anchor_tags = {anchor: 1.0} if anchor else {}
        
        # Aggregate pools based on the anchor
        pools, _, rules_enabled, spelling_order = self._aggregate(anchor_tags)
        
        for _ in range(max(1, int(attempts))):
            suffix = self._fill_shape(shape, pools)
            if suffix is None:
                continue
            
            if self._violates_constraints(suffix, rules_enabled):
                continue
            
            suffix = self._apply_orthography(suffix, spelling_order)
            return suffix
        
        # Fallback: return a simple vowel
        return "a"

    def report_missing_tags(self, output_file=None):
        """Report all missing tags, sorted by frequency."""
        if not self.missing_tags:
            print("No missing tags detected.")
            return
        
        sorted_tags = sorted(self.missing_tags.items(), key=lambda x: -x[1])
        print(f"\n--- MISSING TAGS REPORT ({len(sorted_tags)} unique) ---")
        for tag, count in sorted_tags[:50]:  # Top 50
            print(f"  {tag}: {count}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for tag, count in sorted_tags:
                    f.write(f"{tag}\t{count}\n")
            print(f"Full report saved to: {output_file}")
