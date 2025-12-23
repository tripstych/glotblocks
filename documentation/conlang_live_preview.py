"""
Live Preview Module for GlotBlocks
Provides real-time word generation with step-by-step explanations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import random
from typing import Dict, List, Tuple, Optional


class LivePreviewPanel:
    """
    A reusable widget that shows live word generation with explanations.
    Can be embedded in the Anchors Editor, Templates Editor, or as standalone.
    """
    
    def __init__(self, parent, engine=None, template=None, anchors=None):
        """
        Args:
            parent: Tkinter parent widget
            engine: ConlangEngine instance (optional, will try to import)
            template: Template dictionary
            anchors: Anchors dictionary
        """
        self.parent = parent
        self.engine = engine
        self.template = template or {}
        self.anchors = anchors or {}
        
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the preview panel UI"""
        # Title
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(
            title_frame, 
            text="🔍 Live Word Generator",
            font=('Arial', 12, 'bold')
        ).pack(side='left')
        
        # Help button
        help_btn = ttk.Button(
            title_frame,
            text="?",
            width=3,
            command=self.show_help
        )
        help_btn.pack(side='right')
        
        # Input section
        input_frame = ttk.LabelFrame(self.frame, text="Test Word Generation", padding=10)
        input_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(input_frame, text="English word or concept:").grid(row=0, column=0, sticky='w')
        
        self.word_entry = ttk.Entry(input_frame, width=30)
        self.word_entry.grid(row=0, column=1, padx=(10, 5), sticky='ew')
        self.word_entry.insert(0, "fire")
        
        ttk.Button(
            input_frame,
            text="Generate",
            command=self.generate_sample
        ).grid(row=0, column=2, padx=(5, 0))
        
        input_frame.columnconfigure(1, weight=1)
        
        # Manual anchor weights section
        weights_frame = ttk.LabelFrame(self.frame, text="Or Set Manual Weights", padding=10)
        weights_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(weights_frame, text="You can manually specify anchor weights:").pack(anchor='w')
        
        self.weights_text = tk.Text(weights_frame, height=3, width=50)
        self.weights_text.pack(fill='x', pady=5)
        self.weights_text.insert('1.0', '{"fire": 0.7, "earth": 0.3}')
        
        ttk.Button(
            weights_frame,
            text="Generate with These Weights",
            command=self.generate_from_weights
        ).pack()
        
        # Output section - scrolled text with explanation
        output_frame = ttk.LabelFrame(self.frame, text="Generation Breakdown", padding=10)
        output_frame.pack(fill='both', expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            height=20,
            font=('Courier', 10)
        )
        self.output_text.pack(fill='both', expand=True)
        
        # Configure text tags for styling
        self.output_text.tag_config('title', font=('Arial', 12, 'bold'), foreground='#0066cc')
        self.output_text.tag_config('step', font=('Arial', 10, 'bold'), foreground='#00aa00')
        self.output_text.tag_config('anchor', foreground='#cc6600', font=('Courier', 10, 'bold'))
        self.output_text.tag_config('sound', foreground='#9900cc', font=('Courier', 11, 'bold'))
        self.output_text.tag_config('result', font=('Arial', 14, 'bold'), foreground='#ff0066')
        self.output_text.tag_config('explanation', foreground='#666666', font=('Arial', 9, 'italic'))
        
        # Quick examples
        examples_frame = ttk.Frame(self.frame)
        examples_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(examples_frame, text="Quick examples:").pack(side='left', padx=(0, 10))
        
        for word in ["fire", "water", "mountain", "storm", "gentle"]:
            ttk.Button(
                examples_frame,
                text=word,
                command=lambda w=word: self.quick_example(w)
            ).pack(side='left', padx=2)
    
    def quick_example(self, word: str):
        """Load a quick example word"""
        self.word_entry.delete(0, tk.END)
        self.word_entry.insert(0, word)
        self.generate_sample()
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Live Word Generator Help

This panel shows you exactly how words are created in your language:

1. Enter an English word/concept OR set manual anchor weights
2. Click Generate
3. Watch the step-by-step breakdown showing:
   - Which anchors are activated and their weights
   - Which sound pools are selected from
   - The probability of each sound selection
   - Constraint checking
   - Final orthography and morphology rules

This helps you understand:
✓ How your anchors influence word sounds
✓ Why words sound the way they do
✓ How to adjust weights for desired effects
✓ Whether your constraints are too strict
✓ How morphology suffixes are applied

Tip: Try different words to see how anchor 
combinations create different sound patterns!
"""
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Live Preview Help")
        dialog.geometry("500x450")
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=('Arial', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        text.insert('1.0', help_text)
        text.config(state='disabled')
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def generate_sample(self):
        """Generate a sample word with full explanation"""
        word = self.word_entry.get().strip()
        if not word:
            self.show_error("Please enter a word")
            return
        
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        
        # Simulate the generation process (you'll replace this with actual engine calls)
        self._show_generation_process(word)
    
    def generate_from_weights(self):
        """Generate using manual weights"""
        try:
            weights_str = self.weights_text.get('1.0', tk.END).strip()
            weights = json.loads(weights_str)
            
            self.output_text.config(state='normal')
            self.output_text.delete('1.0', tk.END)
            self._show_generation_process("manual", manual_weights=weights)
            
        except json.JSONDecodeError:
            self.show_error("Invalid JSON format for weights")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def _show_generation_process(self, word: str, manual_weights: Optional[Dict] = None):
        """
        Display the detailed generation process.
        This is a demonstration - you'll integrate with your actual engine.
        """
        out = self.output_text
        
        # Title
        out.insert(tk.END, f"🔮 Generating word for: '{word}'\n", 'title')
        out.insert(tk.END, "=" * 60 + "\n\n")
        
        # Step 1: Conceptual Analysis
        out.insert(tk.END, "STEP 1: Conceptual Analysis\n", 'step')
        out.insert(tk.END, "-" * 60 + "\n")
        
        if manual_weights:
            weights = manual_weights
            out.insert(tk.END, "Using manually specified weights:\n")
        else:
            # This would normally come from your semantic analysis
            weights = self._mock_get_weights(word)
            out.insert(tk.END, f"Analyzing semantic properties of '{word}'...\n")
        
        out.insert(tk.END, "\nActivated Anchors:\n")
        for anchor, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            out.insert(tk.END, f"  • ", 'anchor')
            out.insert(tk.END, f"{anchor}: ", 'anchor')
            out.insert(tk.END, f"{weight*100:.0f}%\n")
            
            # Show why this anchor was selected
            out.insert(tk.END, f"    └─ ", 'explanation')
            out.insert(tk.END, self._explain_anchor_selection(word, anchor, weight), 'explanation')
            out.insert(tk.END, "\n")
        
        out.insert(tk.END, "\n")
        
        # Step 2: Sound Pool Selection
        out.insert(tk.END, "STEP 2: Building Sound Pools\n", 'step')
        out.insert(tk.END, "-" * 60 + "\n")
        
        sound_pools = self._mock_get_sound_pools(weights)
        
        for pool_type, sounds in sound_pools.items():
            out.insert(tk.END, f"\n{pool_type.upper()} pool:\n")
            out.insert(tk.END, "  Available sounds: ")
            out.insert(tk.END, ", ".join([f"/{s}/" for s in sounds]), 'sound')
            out.insert(tk.END, "\n  Weighted by anchor contributions\n", 'explanation')
        
        out.insert(tk.END, "\n")
        
        # Step 3: Syllable Generation
        out.insert(tk.END, "STEP 3: Generating Syllables\n", 'step')
        out.insert(tk.END, "-" * 60 + "\n")
        
        syllables = self._mock_generate_syllables(sound_pools, weights)
        
        for i, syl_info in enumerate(syllables, 1):
            out.insert(tk.END, f"\nSyllable {i}: ")
            out.insert(tk.END, f"/{syl_info['syllable']}/\n", 'sound')
            
            for component, info in syl_info['components'].items():
                out.insert(tk.END, f"  {component}: ")
                out.insert(tk.END, f"/{info['sound']}/ ", 'sound')
                out.insert(tk.END, f"(from {info['anchor']}, ", 'explanation')
                out.insert(tk.END, f"{info['probability']:.0%} chance)\n", 'explanation')
        
        out.insert(tk.END, "\n")
        
        # Step 4: Constraint Checking
        out.insert(tk.END, "STEP 4: Constraint Checking\n", 'step')
        out.insert(tk.END, "-" * 60 + "\n")
        
        raw_word = "".join([s['syllable'] for s in syllables])
        constraints = self._mock_check_constraints(raw_word)
        
        out.insert(tk.END, f"Raw word: /{raw_word}/\n")
        out.insert(tk.END, f"\nChecking {len(constraints)} constraints...\n")
        
        for constraint in constraints:
            status = "✓" if constraint['passed'] else "✗"
            out.insert(tk.END, f"  {status} {constraint['name']}: {constraint['description']}\n")
        
        if all(c['passed'] for c in constraints):
            out.insert(tk.END, "\n✓ All constraints passed!\n", 'step')
        else:
            out.insert(tk.END, "\n✗ Some constraints failed - word would be regenerated\n", 'explanation')
        
        out.insert(tk.END, "\n")
        
        # Step 5: Orthography & Morphology
        out.insert(tk.END, "STEP 5: Applying Rules\n", 'step')
        out.insert(tk.END, "-" * 60 + "\n")
        
        orthography_result = self._mock_apply_orthography(raw_word)
        
        out.insert(tk.END, f"\nOrthography transformations:\n")
        for rule in orthography_result['rules_applied']:
            out.insert(tk.END, f"  • {rule['name']}: ")
            out.insert(tk.END, f"/{rule['before']}/ → /{rule['after']}/\n")
        
        final_base = orthography_result['result']
        
        # Morphology
        morphology = self._mock_apply_morphology(final_base, weights)
        
        out.insert(tk.END, f"\nMorphology (grammar suffixes):\n")
        out.insert(tk.END, f"  Base: {final_base}\n")
        
        if morphology['suffix']:
            out.insert(tk.END, f"  Suffix: -{morphology['suffix']}\n")
            out.insert(tk.END, f"  Reason: {morphology['reason']}\n", 'explanation')
        
        # Final Result
        out.insert(tk.END, "\n" + "=" * 60 + "\n")
        out.insert(tk.END, "✨ FINAL RESULT ✨\n", 'title')
        out.insert(tk.END, "=" * 60 + "\n\n")
        
        final_word = morphology['final_word']
        
        out.insert(tk.END, f"     {final_word}\n", 'result')
        out.insert(tk.END, f"\n     /{raw_word}/\n", 'sound')
        
        out.insert(tk.END, f"\n\nThis word sounds this way because:\n", 'explanation')
        explanation = self._generate_explanation(word, weights, final_word)
        out.insert(tk.END, explanation, 'explanation')
        
        # Make it read-only
        out.config(state='disabled')
    
    # Mock functions - replace these with actual engine calls
    
    def _mock_get_weights(self, word: str) -> Dict[str, float]:
        """Mock semantic analysis - replace with actual implementation"""
        word_mappings = {
            'fire': {'fire': 0.9, 'air': 0.1},
            'water': {'water': 0.9, 'earth': 0.1},
            'mountain': {'earth': 0.8, 'metal': 0.2},
            'storm': {'air': 0.6, 'water': 0.3, 'fire': 0.1},
            'gentle': {'water': 0.7, 'wood': 0.3},
        }
        return word_mappings.get(word.lower(), {'fire': 0.5, 'water': 0.5})
    
    def _mock_get_sound_pools(self, weights: Dict) -> Dict[str, List[str]]:
        """Mock sound pool generation - replace with actual implementation"""
        # Simplified example
        anchor_sounds = {
            'fire': {'consonants': ['k', 't', 'sh', 'f'], 'vowels': ['a', 'i']},
            'water': {'consonants': ['l', 'm', 'n', 'w'], 'vowels': ['u', 'o']},
            'earth': {'consonants': ['g', 'd', 'r'], 'vowels': ['o', 'u']},
            'air': {'consonants': ['h', 's', 'th'], 'vowels': ['i', 'e']},
            'metal': {'consonants': ['k', 'g', 'ng'], 'vowels': ['i', 'a']},
            'wood': {'consonants': ['y', 'w', 'l'], 'vowels': ['e', 'o']},
        }
        
        pools = {'consonants': [], 'vowels': []}
        for anchor, weight in weights.items():
            if anchor in anchor_sounds:
                pools['consonants'].extend(anchor_sounds[anchor]['consonants'])
                pools['vowels'].extend(anchor_sounds[anchor]['vowels'])
        
        return pools
    
    def _mock_generate_syllables(self, sound_pools: Dict, weights: Dict) -> List[Dict]:
        """Mock syllable generation - replace with actual implementation"""
        # Generate 1-2 syllables
        num_syllables = random.randint(1, 2)
        syllables = []
        
        for _ in range(num_syllables):
            onset = random.choice(sound_pools['consonants'])
            nucleus = random.choice(sound_pools['vowels'])
            coda = random.choice(sound_pools['consonants'] + [''])
            
            # Pick which anchor contributed each sound (simplified)
            main_anchor = max(weights.items(), key=lambda x: x[1])[0]
            
            syllables.append({
                'syllable': onset + nucleus + coda,
                'components': {
                    'onset': {'sound': onset, 'anchor': main_anchor, 'probability': list(weights.values())[0]},
                    'nucleus': {'sound': nucleus, 'anchor': main_anchor, 'probability': list(weights.values())[0]},
                    'coda': {'sound': coda, 'anchor': main_anchor, 'probability': 0.5} if coda else None
                }
            })
            
            # Remove None values
            syllables[-1]['components'] = {k: v for k, v in syllables[-1]['components'].items() if v}
        
        return syllables
    
    def _mock_check_constraints(self, word: str) -> List[Dict]:
        """Mock constraint checking - replace with actual implementation"""
        return [
            {'name': 'no_double_consonants', 'description': 'No repeated consonants', 'passed': True},
            {'name': 'valid_clusters', 'description': 'Only allowed consonant clusters', 'passed': True},
            {'name': 'syllable_structure', 'description': 'Matches CV or CVC pattern', 'passed': True},
        ]
    
    def _mock_apply_orthography(self, word: str) -> Dict:
        """Mock orthography application - replace with actual implementation"""
        return {
            'result': word,
            'rules_applied': [
                {'name': 'sh_spelling', 'before': 'sh', 'after': 'sh'},
            ]
        }
    
    def _mock_apply_morphology(self, base: str, weights: Dict) -> Dict:
        """Mock morphology application - replace with actual implementation"""
        # Add suffix based on dominant anchor
        main_anchor = max(weights.items(), key=lambda x: x[1])[0]
        suffix_map = {
            'fire': 'ar',
            'water': 'um',
            'earth': 'on',
            'air': 'is',
        }
        
        suffix = suffix_map.get(main_anchor, '')
        
        return {
            'suffix': suffix,
            'final_word': base + suffix if suffix else base,
            'reason': f"Noun suffix from dominant {main_anchor} anchor"
        }
    
    def _explain_anchor_selection(self, word: str, anchor: str, weight: float) -> str:
        """Generate human-readable explanation for anchor selection"""
        explanations = {
            'fire': f"'{word}' has qualities of heat, energy, or aggression",
            'water': f"'{word}' implies fluidity, calmness, or depth",
            'earth': f"'{word}' suggests solidity, stability, or groundedness",
            'air': f"'{word}' evokes lightness, movement, or breath",
            'metal': f"'{word}' has connotations of strength or hardness",
            'wood': f"'{word}' relates to growth, flexibility, or nature",
        }
        return explanations.get(anchor, f"Conceptually related to {anchor}")
    
    def _generate_explanation(self, word: str, weights: Dict, final_word: str) -> str:
        """Generate final explanation of why the word sounds the way it does"""
        main_anchor = max(weights.items(), key=lambda x: x[1])[0]
        
        explanations = {
            'fire': "harsh, sharp sounds to evoke heat and energy",
            'water': "flowing, smooth sounds to suggest fluidity",
            'earth': "grounded, solid sounds for stability",
            'air': "light, breathy sounds for movement",
        }
        
        quality = explanations.get(main_anchor, "its conceptual anchors")
        
        return (f"The word '{final_word}' uses {quality}. "
                f"The dominant {main_anchor} anchor ({weights[main_anchor]*100:.0f}%) "
                f"determined most of the sound selections, creating sound symbolism "
                f"where the word's pronunciation reflects its meaning.")
    
    def show_error(self, message: str):
        """Show error message"""
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, f"❌ Error: {message}\n", 'title')
    
    def update_data(self, template=None, anchors=None):
        """Update the template and anchors data"""
        if template:
            self.template = template
        if anchors:
            self.anchors = anchors
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs)


# Standalone demo
if __name__ == "__main__":
    root = tk.Tk()
    root.title("GlotBlocks Live Preview Demo")
    root.geometry("900x700")
    
    # Create the preview panel
    preview = LivePreviewPanel(root)
    preview.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop()
