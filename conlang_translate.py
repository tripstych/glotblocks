import sys
import argparse
import spacy
from num2words import num2words
import conlang_yoda
import json
import os
import re
from conlang_language_paths import get_dictionary_file, get_suffixes_file

# Load spaCy model
nlp = spacy.load("en_core_web_lg", disable=["ner"])

"""Translator for conlang_lexicon.json.

Lexicon values can be either:
- dict (new format): {"word": "...", "composition": {...}, ...}
- str  (legacy format): "..."
"""

# Map spaCy POS to WordNet-style single letter
SPACY_TO_WN = {
    "NOUN": "n",
    "VERB": "v",
    "ADJ": "a",
    "ADV": "r",
    "PROPN": "n",  # Proper nouns -> noun
}

class ConlangTranslator:
    """English -> conlang translator using a WordNet-style keyed lexicon."""

    def __init__(self, lexicon, suffix_map=None, debug=False):
        self.lexicon = lexicon
        self.missing_words = {}  # Track missing: {"lemma.pos": count}
        # Suffix cache: grammar_type -> conlang suffix (loaded from lexicon metadata or generated)
        self.suffix_map = suffix_map or {}
        self.debug = debug

    @staticmethod
    def get_wordnet_pos(spacy_pos):
        """Map spaCy POS tags to WordNet-style single letter."""
        return SPACY_TO_WN.get(spacy_pos, "n")

    @staticmethod
    def entry_to_word(entry, fallback):
        """Extract a surface form from a lexicon entry."""
        if isinstance(entry, dict):
            return entry.get('word', fallback)
        if isinstance(entry, str):
            return entry
        return fallback

    def find_best_key(self, lemma, wn_pos):
        """Find the best matching key in the lexicon for lemma/POS."""
        # Priority 1: Exact Match (lemma + pos + .01)
        candidate_01 = f"{lemma}.{wn_pos}.01"
        if candidate_01 in self.lexicon:
            return candidate_01

        # Priority 2: Fuzzy Match (lemma + pos)
        prefix = f"{lemma}.{wn_pos}."
        for key in self.lexicon:
            if key.startswith(prefix):
                return key

        # Priority 3: Desperation Match (lemma only, with dot)
        prefix = f"{lemma}."
        for key in self.lexicon:
            if key.startswith(prefix):
                return key

        # Priority 4: Bare word key (for words not in WordNet like "the", "this")
        if lemma in self.lexicon:
            return lemma

        return None

    def detect_morphology(self, token):
        """
        Detect morphological markers using spaCy's morph analysis.
        Returns: (morph_type, lemma) or (None, None)
        """
        lemma = token.lemma_.lower()
        morph = token.morph
        
        # Use spaCy's morphological features
        tense = morph.get("Tense")
        aspect = morph.get("Aspect")
        verb_form = morph.get("VerbForm")
        number = morph.get("Number")
        degree = morph.get("Degree")
        
        # Progressive/Continuous: Aspect=Prog or VerbForm=Ger
        if "Prog" in aspect or "Ger" in verb_form:
            return "continuous", lemma
        
        # Past tense: Tense=Past
        if "Past" in tense and "Part" not in verb_form:
            return "past_tense", lemma
        
        # Plural: Number=Plur (for nouns)
        if "Plur" in number and token.pos_ in ("NOUN", "PROPN"):
            return "plural", lemma
        
        # Third person singular verbs (Number=Sing + Person=3 + Tense=Pres)
        if token.tag_ == "VBZ":
            return "plural", lemma  # Use plural suffix for 3rd person -s
        
        # Comparative: Degree=Cmp
        if "Cmp" in degree:
            return "comparative", lemma
        
        # Superlative: Degree=Sup
        if "Sup" in degree:
            return "superlative", lemma
        
        return None, None

    def translate_sentence(self, sentence):
        """Translate a sentence; unknown words are output as [word]."""
        sentence = re.sub(r"\d+", lambda x: num2words(int(x.group(0))), sentence)
        sentence = sentence.replace("-", " ")
        
        # Use spaCy for tokenization, POS tagging, and lemmatization
        doc = nlp(sentence)
        
        def translate_token(token):
            wn_pos = self.get_wordnet_pos(token.pos_)
            lemma = token.lemma_.lower()
            
            if self.debug:
                print(f"  [{token.text}] pos={token.pos_} tag={token.tag_} lemma={lemma} morph={token.morph}")
            
            # Check for morphology first
            morph_type, morph_lemma = self.detect_morphology(token)
            
            if self.debug and morph_type:
                print(f"    -> morph_type={morph_type} morph_lemma={morph_lemma}")
            
            # If morphology detected, use lemma (base form) + suffix
            if morph_type and morph_type in self.suffix_map and morph_lemma:
                target_key = self.find_best_key(morph_lemma, wn_pos)
                if self.debug:
                    print(f"    -> lookup '{morph_lemma}.{wn_pos}' found key={target_key}")
                if target_key and target_key in self.lexicon:
                    base_word = self.entry_to_word(self.lexicon[target_key], f"[{token.text}]")
                    result = base_word + self.suffix_map[morph_type]
                    if self.debug:
                        print(f"    -> result: {base_word} + {self.suffix_map[morph_type]} = {result}")
                    return result

            # No morphology - try original text first, then lemma
            text_lower = token.text.lower()
            target_key = self.find_best_key(text_lower, wn_pos)
            if not target_key:
                target_key = self.find_best_key(lemma, wn_pos)
            
            if self.debug:
                print(f"    -> no morph, lookup '{text_lower}' or '{lemma}' found key={target_key}")
            
            if target_key and target_key in self.lexicon:
                return self.entry_to_word(self.lexicon[target_key], f"[{token.text}]")
            
            # Track missing word
            missing_key = f"{lemma}.{wn_pos}"
            self.missing_words[missing_key] = self.missing_words.get(missing_key, 0) + 1
            return f"[{token.text}]"

        translation = []
        tokens = list(doc)
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Pass through punctuation
            if not token.text.isalnum():
                translation.append(token.text)
                i += 1
                continue

            # Flip participle-before-noun pairs: "running man" -> "man running"
            # spaCy uses VBG/VBN in tag_ (fine-grained) and VERB in pos_ (coarse)
            if token.tag_ in {'VBG', 'VBN'} and i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if next_token.text.isalnum() and next_token.pos_ == 'NOUN':
                    translation.append(translate_token(next_token))
                    translation.append(translate_token(token))
                    i += 2
                    continue

            translation.append(translate_token(token))
            i += 1

        return " ".join(translation)

    @classmethod
    def from_json(cls, filename, suffix_file=None, debug=False):
        """Load a lexicon JSON file and return a translator."""
        with open(filename, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        # Try to load suffix map from companion file
        suffix_map = {}
        if suffix_file and os.path.exists(suffix_file):
            with open(suffix_file, 'r', encoding='utf-8') as f:
                suffix_map = json.load(f)
            if debug:
                print(f"Loaded suffix map: {suffix_map}")
        
        return cls(lexicon, suffix_map, debug=debug)


def _configure_utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def _load_translator(lexicon_path, suffix_path=None, debug=False):
    if not os.path.exists(lexicon_path):
        raise FileNotFoundError(lexicon_path)
    translator = ConlangTranslator.from_json(lexicon_path, suffix_file=suffix_path, debug=debug)
    return translator


def _detect_convo_path(base_dir):
    for candidate in ('convo.csv', 'convo..csv'):
        p = os.path.join(base_dir, candidate)
        if os.path.exists(p):
            return p
    return None


def _read_convo_sentences(convo_path):
    with open(convo_path, 'r', encoding='utf-8') as f:
        sentences = []
        for line in f:
            match = re.search(r"'((?:\\'|[^'])*)'", line)
            if not match:
                continue
            sentence = match.group(1).replace("\\'", "'").strip()
            if sentence:
                sentences.append(sentence)
    return sentences


def run_auto(translator, convo_path, output_path):
    sentences = _read_convo_sentences(convo_path)

    with open(output_path, "w", encoding="utf-8") as f:
        last = ""
        print("-" * 50)
        for set in sentences:
            if last == set:
                continue
            test = set.split('.')
            if len(test) > 1:
                for myset in test:
                    if last == myset:
                        continue
                    out = translator.translate_sentence(set)
                continue
            out = translator.translate_sentence(set)
            if out == last:
                continue
            print(out)
            f.write(out + "\n")
            f.flush()
            last = out
            #time.sleep(1)


def run_interactive(translator, output_path=None, yoda_mode=False):
    f = None
    if output_path:
        f = open(output_path, "a", encoding="utf-8")
    try:
        print("Type English to translate. Blank line or 'quit' to exit.")
        while True:
            try:
                line = input('> ')
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line.strip() or line.strip().lower() == 'quit':
                break
            if yoda_mode:
                line = conlang_yoda.yoda_speak(line)
            out = translator.translate_sentence(line)
            print(out)
            if f:
                f.write(out + "\n")
                f.flush()
    finally:
        if f:
            f.close()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['a', 'auto', 'i', 'interactive'])
    parser.add_argument('--language', default='default', help='Language name')
    parser.add_argument('--lexicon', help='Lexicon file (overrides language)')
    parser.add_argument('--convo', default=None)
    parser.add_argument('--output', default=os.path.join(base_dir, 'translation'))
    parser.add_argument('--yoda', action='store_true')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    if not args.mode:
        parser.print_help()
        return

    # Use language_paths unless explicitly overridden
    lexicon_path = args.lexicon or get_dictionary_file(args.language)
    suffix_path = get_suffixes_file(args.language)

    _configure_utf8_stdout()

    try:
        translator = _load_translator(lexicon_path, suffix_path=suffix_path, debug=args.debug)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: {lexicon_path} not found.")
        print("Please run the Generator Script first to create the dictionary file.")
        return

    print(f"Dictionary loaded: {len(translator.lexicon)} words.")

    if args.mode == 'interactive' or args.mode == 'i':
        run_interactive(translator, output_path=args.output, yoda_mode=args.yoda)
        return

    convo_path = args.convo
    if convo_path is None:
        convo_path = _detect_convo_path(base_dir)
    if convo_path is None:
        raise FileNotFoundError(f"No such file or directory: {convo_path}")

    if args.yoda:
        sentences = _read_convo_sentences(convo_path)
        with open(args.output, "w", encoding="utf-8") as f:
            last = ""
            print("-" * 50)
            for set in sentences:
                if last == set:
                    continue
                test = set.split('.')
                if len(test) > 1:
                    for myset in test:
                        if last == myset:
                            continue
                        out = translator.translate_sentence(conlang_yoda.yoda_speak(set))
                    continue
                out = translator.translate_sentence(conlang_yoda.yoda_speak(set))
                if out == last:
                    continue
                print(out)
                f.write(out + "\n")
                f.flush()
                last = out
                #time.sleep(1)
        return

    run_auto(translator, convo_path, args.output)


if __name__ == '__main__':
    main()
