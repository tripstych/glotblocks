import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    nlp = spacy.load("en_core_web_sm")

def yoda_speak(sentence):
    """
    Translates a sentence into Yoda-speak (OSV order) using spaCy.
    """
    doc = nlp(sentence)
    
    subject_parts = []
    verb_parts = []
    object_parts = []
    
    # Find the root verb and its dependents
    root = None
    for token in doc:
        if token.dep_ == "ROOT":
            root = token
            break
    
    if not root:
        return sentence  # Can't parse, return as-is
    
    for token in doc:
        # Skip punctuation
        if token.is_punct:
            continue
        
        # Verb phrase (root and auxiliaries)
        if token == root or token.dep_ in ("aux", "auxpass", "neg"):
            verb_parts.append(token.text)
        # Subject
        elif token.dep_ in ("nsubj", "nsubjpass") or (token.head.dep_ in ("nsubj", "nsubjpass") and token.dep_ in ("det", "amod", "compound", "poss")):
            subject_parts.append(token.text)
        # Object and everything else
        else:
            object_parts.append(token.text)

    # --- FIX START: Robust Case Cleaning ---
    def clean_case(text_list, is_start=False):
        # 1. Safety check for empty lists
        if not text_list:
            return ""
            
        text = " ".join(text_list)
        
        if is_start:
            return text[0].upper() + text[1:]
        else:
            first_word = text_list[0]
            # Don't lowercase "I" or proper nouns (heuristically capitalized words)
            if first_word != "I" and not first_word[0].isupper():
                 return text
            if first_word == "I": 
                return text
            # Lowercase the first letter
            return text[0].lower() + text[1:]
    # --- FIX END ---

    # Construct parts
    new_obj = clean_case(object_parts, is_start=True)
    new_subj = clean_case(subject_parts, is_start=False)
    new_verb = " ".join(verb_parts)

    # Assemble the final sentence dynamically to avoid extra commas/spaces
    # Standard Yoda: Object, Verb Subject.
    parts = []
    if new_obj:
        parts.append(f"{new_obj},")
    if new_verb:
        parts.append(new_verb)
    if new_subj:
        parts.append(new_subj)
        
    result = " ".join(parts)
    
    # Ensure it ends with punctuation
    if not result.endswith(('.', '!', '?')):
        result += "."
        
    return result

# --- Main Loop for Testing ---
if __name__ == "__main__":
    print("--- Yoda Translator (Type 'exit' to quit) ---")
    while True:
        user_input = input("Enter a sentence: ")
        if user_input.lower() == 'exit':
            break
        try:
            # Use spaCy for sentence splitting
            doc = nlp(user_input)
            for sent in doc.sents:
                print(yoda_speak(sent.text))
        except Exception as e:
            print(f"Error: {e}")