#!/usr/bin/env python3
"""
Conlang Template Wizard - Step-by-step guide for creating a new language template.
Walks users through phonology, phonotactics, morphology, orthography, and ontology.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import argparse
from conlang_language_paths import get_template_file, get_anchors_file, get_language_dir

# =============================================================================
# PRESETS - Common language "flavors" for quick setup
# =============================================================================

PHONOLOGY_PRESETS = {
    "Balanced (Default)": {
        "C": ["p", "t", "k", "b", "d", "g", "m", "n", "s", "z", "l", "r", "h", "w", "y"],
        "V": ["a", "e", "i", "o", "u"],
        "Stops": ["p", "t", "k", "b", "d", "g"],
        "Fricatives": ["f", "v", "s", "z", "h"],
        "Liquids": ["l", "r", "w", "y"],
        "Nasals": ["m", "n", "ng"],
    },
    "Polynesian (Soft, Vowel-Heavy)": {
        "C": ["p", "t", "k", "m", "n", "ng", "h", "w", "l", "r"],
        "V": ["a", "e", "i", "o", "u", "aa", "ee", "ii", "oo", "uu"],
        "Stops": ["p", "t", "k"],
        "Fricatives": ["h"],
        "Liquids": ["l", "r", "w"],
        "Nasals": ["m", "n", "ng"],
    },
    "Germanic (Harsh, Consonant Clusters)": {
        "C": ["p", "t", "k", "b", "d", "g", "f", "v", "s", "z", "th", "sh", "ch", "m", "n", "l", "r", "w", "y", "h"],
        "V": ["a", "e", "i", "o", "u", "ae", "oe", "ue"],
        "Stops": ["p", "t", "k", "b", "d", "g"],
        "Fricatives": ["f", "v", "s", "z", "th", "sh", "ch", "h"],
        "Liquids": ["l", "r", "w", "y"],
        "Nasals": ["m", "n", "ng"],
    },
    "Japanese-like (CV Structure)": {
        "C": ["k", "s", "t", "n", "h", "m", "y", "r", "w", "g", "z", "d", "b", "p"],
        "V": ["a", "i", "u", "e", "o"],
        "Stops": ["k", "t", "g", "d", "b", "p"],
        "Fricatives": ["s", "z", "h"],
        "Liquids": ["r", "w", "y"],
        "Nasals": ["m", "n"],
    },
    "Elvish (Flowing, Musical)": {
        "C": ["l", "r", "n", "m", "th", "dh", "s", "f", "v", "w", "y", "t", "d", "k", "g"],
        "V": ["a", "e", "i", "o", "u", "ai", "ei", "au", "iu"],
        "Stops": ["t", "d", "k", "g"],
        "Fricatives": ["th", "dh", "s", "f", "v"],
        "Liquids": ["l", "r", "w", "y"],
        "Nasals": ["m", "n"],
    },
    "Harsh/Guttural (Orcish)": {
        "C": ["k", "g", "kh", "gh", "r", "rr", "z", "zh", "sh", "t", "d", "b", "p", "m", "n"],
        "V": ["a", "u", "o", "aa", "uu"],
        "Stops": ["k", "g", "t", "d", "b", "p"],
        "Fricatives": ["kh", "gh", "z", "zh", "sh"],
        "Liquids": ["r", "rr"],
        "Nasals": ["m", "n"],
    },
}

SYLLABLE_PRESETS = {
    # === REAL LANGUAGE FAMILIES ===
    "English (High Complexity)": {
        # Onset: High (str-, spr-, scr-), Coda: High (-ngst, -mpts)
        # Pattern: (C)(C)(C)V(C)(C)(C)(C)
        "noun": ["CVC", "CCVC", "CVCC", "CCVCC", "CVCCC"],
        "verb": ["CVC", "CCVC", "CVCC", "CCCVC"],
        "adjective": ["CVC", "CCVC", "CVCC"],
        "adverb": ["CVCCC", "CCVCC"],
        "_meta": {"onset": "high", "coda": "high", "pattern": "(C)(C)(C)V(C)(C)(C)(C)"}
    },
    "Latin/Romance (Medium)": {
        # Onset: Med (pr-, bl-, tr-), Coda: Low (-n, -s, -l)
        # Pattern: (C)(C)V(C)
        "noun": ["CVCV", "CVC", "CCVC", "CCVCV"],
        "verb": ["CVC", "CCVC", "CVCV"],
        "adjective": ["CVC", "CVCV", "CCVC"],
        "adverb": ["CVCV", "CCVCV"],
        "_meta": {"onset": "medium", "coda": "low", "pattern": "(C)(C)V(C)"}
    },
    "Sino-Tibetan (Low Complexity)": {
        # Onset: Low (single C), Coda: Low (-n, -ng)
        # Pattern: (C)(G)V(C) where G=glide
        "noun": ["CV", "CVC", "CVV", "CGVC"],
        "verb": ["CV", "CVC", "CGV"],
        "adjective": ["CV", "CVC"],
        "adverb": ["CV", "CVCV"],
        "_meta": {"onset": "low", "coda": "low", "pattern": "(C)(G)V(C)"}
    },
    "Arabic (Triconsonantal Roots)": {
        # Onset: Low (no initial clusters), Coda: Med (-CC allowed)
        # Pattern: CV(V)(C)(C)
        "noun": ["CVCC", "CVCVC", "CVVC", "CVCVVC"],
        "verb": ["CVC", "CVCC", "CVCVC"],
        "adjective": ["CVCC", "CVCVC"],
        "adverb": ["CVCCV", "CVCVC"],
        "_meta": {"onset": "low", "coda": "medium", "pattern": "CV(V)(C)(C)"}
    },
    "Japanese (Minimal, Open)": {
        # Onset: Very Low (single C), Coda: None (only -n)
        # Pattern: (C)V - strictly open syllables
        "noun": ["CVCV", "CVVCV", "CVCVCV"],
        "verb": ["CV", "CVCV", "CVVCV"],
        "adjective": ["CVCV", "CVVCV"],
        "adverb": ["CVCV", "CVVCV"],
        "_meta": {"onset": "very_low", "coda": "none", "pattern": "(C)V"}
    },
    # === FICTIONAL STYLES ===
    "Simple (CV)": {
        "noun": ["CV", "CVCV", "CVCCV"],
        "verb": ["CVC", "CVCVC"],
        "adjective": ["VCV", "CVCV"],
        "adverb": ["VCV", "VCVC"],
    },
    "Open Syllables (ends in vowel)": {
        "noun": ["CVCV", "CVCCV", "CVCVCV"],
        "verb": ["CVCCV", "CVCV"],
        "adjective": ["VCV", "CVCV"],
        "adverb": ["VCV", "VCVCV"],
    },
    "Closed Syllables (ends in consonant)": {
        "noun": ["CVC", "CVCC", "CVCVC"],
        "verb": ["CVC", "CVCC"],
        "adjective": ["CVC", "VCVC"],
        "adverb": ["CVC", "CVCVC"],
    },
    "Complex Clusters (Germanic/Slavic)": {
        "noun": ["CCVC", "CVCC", "CCVCC", "CVCVC", "CCCVC"],
        "verb": ["CCVC", "CVCC", "CVC", "CCVCC"],
        "adjective": ["CCV", "CCVC", "VCC", "CCVCC"],
        "adverb": ["CCV", "CCVCV", "CCVCC"],
    },
}

ELEMENT_PRESETS = {
    "Classical Four Elements": ["fire", "water", "earth", "air"],
    "Chinese Wu Xing": ["fire", "water", "earth", "metal", "wood"],
    "Nature-Based": ["fire", "water", "earth", "air", "life", "death"],
    "Abstract Concepts": ["light", "dark", "order", "chaos", "time", "space"],
    "Sensory": ["sight", "sound", "touch", "taste", "smell", "motion"],
}

ELEMENT_SOUND_MAPPING = {
    "fire": {"sounds": ["Stops", "Fricatives"], "note": "Sharp, explosive sounds"},
    "water": {"sounds": ["Liquids", "V"], "note": "Flowing, smooth sounds"},
    "earth": {"sounds": ["Nasals", "Stops"], "note": "Deep, grounded sounds"},
    "air": {"sounds": ["Fricatives", "V"], "note": "Breathy, light sounds"},
    "metal": {"sounds": ["Fricatives", "Stops"], "note": "Hard, ringing sounds"},
    "wood": {"sounds": ["Liquids", "Nasals"], "note": "Organic, growing sounds"},
    "life": {"sounds": ["V", "Liquids"], "note": "Open, vibrant sounds"},
    "death": {"sounds": ["Stops", "Fricatives"], "note": "Closed, final sounds"},
    "light": {"sounds": ["Fricatives", "V"], "note": "Bright, clear sounds"},
    "dark": {"sounds": ["Stops", "Nasals"], "note": "Muted, heavy sounds"},
    "order": {"sounds": ["Stops", "Nasals"], "note": "Regular, structured sounds"},
    "chaos": {"sounds": ["Fricatives", "Liquids"], "note": "Unpredictable, varied sounds"},
    "time": {"sounds": ["Fricatives", "V"], "note": "Continuous, flowing sounds"},
    "space": {"sounds": ["V", "Liquids"], "note": "Open, expansive sounds"},
    "sight": {"sounds": ["Fricatives", "V"], "note": "Sharp, clear sounds"},
    "sound": {"sounds": ["Nasals", "Liquids"], "note": "Resonant sounds"},
    "touch": {"sounds": ["Stops", "Nasals"], "note": "Tactile, direct sounds"},
    "taste": {"sounds": ["Liquids", "V"], "note": "Soft, subtle sounds"},
    "smell": {"sounds": ["Fricatives", "Nasals"], "note": "Airy, nasal sounds"},
    "motion": {"sounds": ["Liquids", "Stops"], "note": "Dynamic, active sounds"},
}


class TemplateWizard:
    def __init__(self, root, language_name="NewLanguage"):
        self.root = root
        self.language_name = language_name
        self.root.title(f"Language Template Wizard")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Wizard state
        self.current_step = 0
        self.steps = [
            ("Welcome", self._build_welcome_step),
            ("Anchors (Concepts)", self._build_anchors_step),
            ("Phonology", self._build_phonology_step),
            ("Syllable Structure", self._build_syllable_step),
            ("Sound Symbolism", self._build_ontology_step),
            ("Grammar (Morphology)", self._build_morphology_step),
            ("Orthography", self._build_orthography_step),
            ("Review & Create", self._build_review_step),
        ]
        
        # Anchor groups defined by user (used by morphology and sound symbolism)
        self.anchors = []
        
        # Template data being built
        self.template = {
            "definitions": {"desc": "Phoneme categories"},
            "constraints": {"desc": "Phonotactic rules"},
            "orthography": {"desc": "Spelling rules"},
            "ontology": {"desc": "Sound symbolism mappings"},
        }
        
        self._create_ui()
        self._show_step(0)
    
    def _create_ui(self):
        """Create the wizard UI framework"""
        # Header with step indicator
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(fill='x', padx=10, pady=10)
        
        self.step_label = ttk.Label(self.header_frame, text="", font=('Arial', 16, 'bold'))
        self.step_label.pack(side='left')
        
        self.progress_label = ttk.Label(self.header_frame, text="", foreground='gray')
        self.progress_label.pack(side='right')
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        # Main content area
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.root)
        self.nav_frame.pack(fill='x', padx=10, pady=10)
        
        self.back_btn = ttk.Button(self.nav_frame, text="← Back", command=self._prev_step)
        self.back_btn.pack(side='left', padx=5)
        
        self.cancel_btn = ttk.Button(self.nav_frame, text="Cancel", command=self._cancel)
        self.cancel_btn.pack(side='left', padx=5)
        
        self.next_btn = ttk.Button(self.nav_frame, text="Next →", command=self._next_step)
        self.next_btn.pack(side='right', padx=5)
    
    def _show_step(self, step_index):
        """Display a specific step"""
        self.current_step = step_index
        
        # Update header
        step_name, builder_func = self.steps[step_index]
        self.step_label.config(text=step_name)
        self.progress_label.config(text=f"Step {step_index + 1} of {len(self.steps)}")
        
        # Update progress bar
        progress = (step_index / (len(self.steps) - 1)) * 100
        self.progress['value'] = progress
        
        # Clear content
        for child in self.content_frame.winfo_children():
            child.destroy()
        
        # Build step content
        builder_func()
        
        # Update navigation buttons
        self.back_btn.config(state='normal' if step_index > 0 else 'disabled')
        
        if step_index == len(self.steps) - 1:
            self.next_btn.config(text="✓ Create Template", command=self._finish)
        else:
            self.next_btn.config(text="Next →", command=self._next_step)
    
    def _prev_step(self):
        if self.current_step > 0:
            self._save_current_step()
            self._show_step(self.current_step - 1)
    
    def _next_step(self):
        if self.current_step < len(self.steps) - 1:
            self._save_current_step()
            self._show_step(self.current_step + 1)
    
    def _save_current_step(self):
        """Save data from current step before moving"""
        pass  # Each step saves its own data in real-time
    
    def _cancel(self):
        if messagebox.askyesno("Cancel", "Discard this template and exit?"):
            self.root.destroy()
    
    # =========================================================================
    # STEP BUILDERS
    # =========================================================================
    
    def _build_welcome_step(self):
        """Welcome screen with language name input"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True, pady=20)
        
        ttk.Label(frame, text="Welcome to the Language Template Wizard!", 
                  font=('Arial', 18, 'bold')).pack(pady=20)
        
        ttk.Label(frame, text=(
            "This wizard will guide you through creating a complete language template.\n"
            "You'll define:\n\n"
            "  1. Anchors - Core concepts (elements) that give your language flavor\n"
            "  2. Phonology - The sounds your language uses\n"
            "  3. Syllable Structure - How sounds combine into words\n"
            "  4. Sound Symbolism - How anchors map to sounds\n"
            "  5. Grammar - How meaning is modified (tenses, plurals linked to anchors)\n"
            "  6. Orthography - Spelling and writing rules\n\n"
            "You can choose from presets or customize everything."
        ), font=('Arial', 11), justify='left').pack(pady=10)
        
        # Language name
        name_frame = ttk.LabelFrame(frame, text="Language Name", padding=15)
        name_frame.pack(fill='x', padx=50, pady=20)
        
        ttk.Label(name_frame, text="Enter a name for your language:").pack(anchor='w')
        
        self.lang_name_var = tk.StringVar(value=self.language_name)
        name_entry = ttk.Entry(name_frame, textvariable=self.lang_name_var, font=('Arial', 14), width=30)
        name_entry.pack(pady=10)
        name_entry.focus_set()
        
        def update_name(*args):
            self.language_name = self.lang_name_var.get().strip() or "NewLanguage"
        self.lang_name_var.trace('w', update_name)
        
        ttk.Label(name_frame, text="(This will be used for file naming)", foreground='gray').pack()
    
    def _build_anchors_step(self):
        """Define conceptual anchors (elements) - MUST come before morphology and sound symbolism"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Your Conceptual Anchors", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text=(
            "Anchors are the core concepts that give your language its 'flavor'.\n"
            "They influence how words sound based on meaning (sound symbolism).\n"
            "Grammar suffixes will also be linked to anchors."
        ), foreground='gray').pack()
        
        # Preset selector
        preset_frame = ttk.LabelFrame(frame, text="Quick Presets", padding=10)
        preset_frame.pack(fill='x', padx=10, pady=10)
        
        self.anchor_preset_var = tk.StringVar(value="Chinese Wu Xing")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.anchor_preset_var,
                                     values=list(ELEMENT_PRESETS.keys()), state='readonly', width=30)
        preset_combo.pack(side='left', padx=5)
        
        def apply_preset():
            elements = ELEMENT_PRESETS.get(self.anchor_preset_var.get(), [])
            self.anchors = elements.copy()
            self._refresh_anchor_list()
        
        ttk.Button(preset_frame, text="Apply Preset", command=apply_preset).pack(side='left', padx=10)
        
        # Current anchors display
        edit_frame = ttk.LabelFrame(frame, text="Your Anchors", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        list_frame = ttk.Frame(edit_frame)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.anchor_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10, font=('Arial', 12))
        self.anchor_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.anchor_listbox.yview)
        
        # Add/remove controls
        ctrl_frame = ttk.Frame(edit_frame)
        ctrl_frame.pack(fill='x', pady=10)
        
        ttk.Label(ctrl_frame, text="New anchor:").pack(side='left', padx=5)
        self.new_anchor_var = tk.StringVar()
        anchor_entry = ttk.Entry(ctrl_frame, textvariable=self.new_anchor_var, width=20)
        anchor_entry.pack(side='left', padx=5)
        
        def add_anchor():
            name = self.new_anchor_var.get().strip().lower()
            if name and name not in self.anchors:
                self.anchors.append(name)
                self._refresh_anchor_list()
                self.new_anchor_var.set("")
        
        def remove_anchor():
            sel = self.anchor_listbox.curselection()
            if sel:
                anchor = self.anchor_listbox.get(sel[0])
                if anchor in self.anchors:
                    self.anchors.remove(anchor)
                self._refresh_anchor_list()
        
        anchor_entry.bind('<Return>', lambda e: add_anchor())
        ttk.Button(ctrl_frame, text="Add", command=add_anchor).pack(side='left', padx=5)
        ttk.Button(ctrl_frame, text="Remove Selected", command=remove_anchor).pack(side='left', padx=5)
        
        # Description of each anchor type
        desc_frame = ttk.LabelFrame(frame, text="Common Anchor Meanings", padding=10)
        desc_frame.pack(fill='x', padx=10, pady=5)
        
        descriptions = [
            "fire - energy, action, passion, destruction",
            "water - flow, emotion, change, adaptation", 
            "earth - stability, physical, grounded, solid",
            "air - thought, freedom, lightness, spirit",
            "metal - structure, technology, precision, hardness",
            "wood - growth, life, flexibility, nature",
        ]
        ttk.Label(desc_frame, text="\n".join(descriptions), font=('Arial', 9), foreground='#555').pack(anchor='w')
        
        # Apply default preset
        apply_preset()
    
    def _refresh_anchor_list(self):
        """Update anchor listbox display"""
        self.anchor_listbox.delete(0, 'end')
        for anchor in self.anchors:
            self.anchor_listbox.insert('end', anchor)
    
    def _build_phonology_step(self):
        """Phonology: consonants, vowels, sound categories"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Your Sound Inventory", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text="Choose a preset or customize the sounds your language uses.", 
                  foreground='gray').pack()
        
        # Preset selector
        preset_frame = ttk.LabelFrame(frame, text="Quick Presets", padding=10)
        preset_frame.pack(fill='x', padx=10, pady=10)
        
        self.phon_preset_var = tk.StringVar(value="Balanced (Default)")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.phon_preset_var,
                                     values=list(PHONOLOGY_PRESETS.keys()), state='readonly', width=40)
        preset_combo.pack(side='left', padx=5)
        
        def apply_preset():
            preset = PHONOLOGY_PRESETS.get(self.phon_preset_var.get(), {})
            for cat, sounds in preset.items():
                self.template["definitions"][cat] = sounds.copy()
            self._refresh_phonology_display()
        
        ttk.Button(preset_frame, text="Apply Preset", command=apply_preset).pack(side='left', padx=10)
        
        # Display/edit area
        edit_frame = ttk.LabelFrame(frame, text="Sound Categories (edit as CSV)", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.phon_entries = {}
        categories = [("C", "Consonants"), ("V", "Vowels"), ("Stops", "Stop Consonants"), 
                      ("Fricatives", "Fricatives"), ("Liquids", "Liquids/Glides"), ("Nasals", "Nasals")]
        
        for i, (key, label) in enumerate(categories):
            ttk.Label(edit_frame, text=f"{label}:", font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky='w', padx=5, pady=3)
            
            var = tk.StringVar()
            entry = ttk.Entry(edit_frame, textvariable=var, width=60)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
            self.phon_entries[key] = var
            
            # Save on change
            def save_cat(key=key, var=var):
                sounds = [s.strip() for s in var.get().split(',') if s.strip()]
                self.template["definitions"][key] = sounds
            var.trace('w', lambda *a, k=key, v=var: save_cat(k, v))
        
        edit_frame.columnconfigure(1, weight=1)
        
        # Initialize with default
        apply_preset()
    
    def _refresh_phonology_display(self):
        """Update phonology entry fields from template data"""
        for key, var in self.phon_entries.items():
            sounds = self.template["definitions"].get(key, [])
            var.set(", ".join(sounds))
    
    def _build_syllable_step(self):
        """Syllable structure / phonotactics"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Syllable Structures", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text=(
            "Syllable patterns use: C=Consonant, V=Vowel\n"
            "Example: 'CVCV' = consonant-vowel-consonant-vowel (e.g., 'taka')"
        ), foreground='gray').pack()
        
        # Preset selector
        preset_frame = ttk.LabelFrame(frame, text="Quick Presets", padding=10)
        preset_frame.pack(fill='x', padx=10, pady=10)
        
        self.syl_preset_var = tk.StringVar(value="Simple (CV)")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.syl_preset_var,
                                     values=list(SYLLABLE_PRESETS.keys()), state='readonly', width=40)
        preset_combo.pack(side='left', padx=5)
        
        def apply_preset():
            preset = SYLLABLE_PRESETS.get(self.syl_preset_var.get(), {})
            for pos, shapes in preset.items():
                if pos.startswith("_"):  # Skip metadata keys like _meta
                    continue
                if not isinstance(shapes, list):
                    continue
                if pos not in self.template["ontology"]:
                    self.template["ontology"][pos] = {}
                self.template["ontology"][pos]["add_shapes"] = shapes.copy()
            self._refresh_syllable_display()
        
        ttk.Button(preset_frame, text="Apply Preset", command=apply_preset).pack(side='left', padx=10)
        
        # Display/edit area
        edit_frame = ttk.LabelFrame(frame, text="Syllable Patterns by Part of Speech", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.syl_entries = {}
        pos_types = [("noun", "Nouns"), ("verb", "Verbs"), ("adjective", "Adjectives"), 
                     ("adverb", "Adverbs"), ("particle", "Particles"), ("conjunction", "Conjunctions")]
        
        for i, (key, label) in enumerate(pos_types):
            ttk.Label(edit_frame, text=f"{label}:", font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky='w', padx=5, pady=3)
            
            var = tk.StringVar()
            entry = ttk.Entry(edit_frame, textvariable=var, width=50)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
            self.syl_entries[key] = var
            
            ttk.Label(edit_frame, text="(comma-separated)", foreground='gray').grid(
                row=i, column=2, sticky='w', padx=5)
            
            def save_shapes(key=key, var=var):
                shapes = [s.strip() for s in var.get().split(',') if s.strip()]
                if key not in self.template["ontology"]:
                    self.template["ontology"][key] = {"weight": 1.0}
                self.template["ontology"][key]["add_shapes"] = shapes
            var.trace('w', lambda *a, k=key, v=var: save_shapes(k, v))
        
        edit_frame.columnconfigure(1, weight=1)
        apply_preset()
    
    def _refresh_syllable_display(self):
        """Update syllable entry fields from template data"""
        for key, var in self.syl_entries.items():
            shapes = self.template["ontology"].get(key, {}).get("add_shapes", [])
            var.set(", ".join(shapes))
    
    def _build_morphology_step(self):
        """Grammar / morphology definitions"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Grammar Suffixes", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text=(
            "Define how grammatical concepts are expressed.\n"
            "Each suffix has an 'anchor' (element that influences its sound) and a 'shape' (structure)."
        ), foreground='gray').pack()
        
        # Morphology table
        edit_frame = ttk.LabelFrame(frame, text="Grammar Suffixes", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ("Type", "Anchor", "Shape", "Note")
        self.morph_tree = ttk.Treeview(edit_frame, columns=columns, show='headings', height=8)
        for col in columns:
            self.morph_tree.heading(col, text=col)
            self.morph_tree.column(col, width=120 if col != "Note" else 200)
        self.morph_tree.pack(fill='both', expand=True, pady=5)
        
        # Default morphology
        default_morph = {
            "past_tense": {"anchor": "metal", "shape": "VC", "note": "Fixed, completed"},
            "future_tense": {"anchor": "air", "shape": "V", "note": "Open, potential"},
            "plural": {"anchor": "earth", "shape": "VC", "note": "Accumulation"},
            "continuous": {"anchor": "water", "shape": "VCV", "note": "Flowing, ongoing"},
            "agent": {"anchor": "fire", "shape": "C", "note": "Active, doing"},
        }
        
        if "morphology" not in self.template["definitions"]:
            self.template["definitions"]["morphology"] = default_morph
        
        for mtype, mdata in self.template["definitions"]["morphology"].items():
            if mtype != "desc" and isinstance(mdata, dict):
                self.morph_tree.insert('', 'end', iid=mtype, values=(
                    mtype, mdata.get("anchor", ""), mdata.get("shape", ""), mdata.get("note", "")
                ))
        
        # Edit form
        form_frame = ttk.Frame(edit_frame)
        form_frame.pack(fill='x', pady=10)
        
        ttk.Label(form_frame, text="Type:").grid(row=0, column=0, padx=2)
        self.morph_type_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.morph_type_var, width=15).grid(row=0, column=1, padx=2)
        
        ttk.Label(form_frame, text="Anchor:").grid(row=0, column=2, padx=2)
        self.morph_anchor_var = tk.StringVar()
        self.morph_anchor_combo = ttk.Combobox(form_frame, textvariable=self.morph_anchor_var, 
                                                values=self.anchors, width=12)
        self.morph_anchor_combo.grid(row=0, column=3, padx=2)
        
        ttk.Label(form_frame, text="Shape:").grid(row=0, column=4, padx=2)
        self.morph_shape_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.morph_shape_var, width=10).grid(row=0, column=5, padx=2)
        
        ttk.Label(form_frame, text="Note:").grid(row=0, column=6, padx=2)
        self.morph_note_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.morph_note_var, width=20).grid(row=0, column=7, padx=2)
        
        def add_morph():
            mtype = self.morph_type_var.get().strip()
            if not mtype:
                return
            entry = {
                "anchor": self.morph_anchor_var.get().strip(),
                "shape": self.morph_shape_var.get().strip(),
                "note": self.morph_note_var.get().strip()
            }
            self.template["definitions"]["morphology"][mtype] = entry
            if self.morph_tree.exists(mtype):
                self.morph_tree.item(mtype, values=(mtype, entry["anchor"], entry["shape"], entry["note"]))
            else:
                self.morph_tree.insert('', 'end', iid=mtype, values=(mtype, entry["anchor"], entry["shape"], entry["note"]))
        
        def del_morph():
            sel = self.morph_tree.selection()
            if sel:
                mtype = sel[0]
                self.morph_tree.delete(mtype)
                if mtype in self.template["definitions"]["morphology"]:
                    del self.template["definitions"]["morphology"][mtype]
        
        def on_select(e):
            sel = self.morph_tree.selection()
            if sel:
                vals = self.morph_tree.item(sel[0])['values']
                self.morph_type_var.set(vals[0])
                self.morph_anchor_var.set(vals[1])
                self.morph_shape_var.set(vals[2])
                self.morph_note_var.set(vals[3])
        
        self.morph_tree.bind('<<TreeviewSelect>>', on_select)
        
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Add/Update", command=add_morph).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete", command=del_morph).pack(side='left', padx=5)
    
    def _build_orthography_step(self):
        """Orthography / spelling rules"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Spelling Rules", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text=(
            "Orthography rules transform sounds into written form.\n"
            "Example: 'th' → 'Þ' (thorn character)"
        ), foreground='gray').pack()
        
        # Orthography table
        edit_frame = ttk.LabelFrame(frame, text="Spelling Transformations", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ("From", "To")
        self.ortho_tree = ttk.Treeview(edit_frame, columns=columns, show='headings', height=10)
        self.ortho_tree.heading("From", text="From (sound)")
        self.ortho_tree.heading("To", text="To (written)")
        self.ortho_tree.column("From", width=200)
        self.ortho_tree.column("To", width=200)
        self.ortho_tree.pack(fill='both', expand=True, pady=5)
        
        # Initialize orthography
        if "default" not in self.template["orthography"]:
            self.template["orthography"]["default"] = []
        
        for rule in self.template["orthography"]["default"]:
            self.ortho_tree.insert('', 'end', values=(rule.get("from", ""), rule.get("to", "")))
        
        # Edit form
        form_frame = ttk.Frame(edit_frame)
        form_frame.pack(fill='x', pady=10)
        
        ttk.Label(form_frame, text="From:").pack(side='left', padx=5)
        self.ortho_from_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ortho_from_var, width=15).pack(side='left', padx=5)
        
        ttk.Label(form_frame, text="To:").pack(side='left', padx=5)
        self.ortho_to_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.ortho_to_var, width=15).pack(side='left', padx=5)
        
        def add_rule():
            from_val = self.ortho_from_var.get().strip()
            to_val = self.ortho_to_var.get().strip()
            if from_val:
                self.template["orthography"]["default"].append({"from": from_val, "to": to_val})
                self.ortho_tree.insert('', 'end', values=(from_val, to_val))
                self.ortho_from_var.set("")
                self.ortho_to_var.set("")
        
        def del_rule():
            sel = self.ortho_tree.selection()
            if sel:
                idx = self.ortho_tree.index(sel[0])
                self.ortho_tree.delete(sel[0])
                if idx < len(self.template["orthography"]["default"]):
                    del self.template["orthography"]["default"][idx]
        
        ttk.Button(form_frame, text="Add", command=add_rule).pack(side='left', padx=10)
        ttk.Button(form_frame, text="Delete Selected", command=del_rule).pack(side='left', padx=5)
        
        # Common suggestions
        sug_frame = ttk.LabelFrame(frame, text="Common Transformations (click to add)", padding=5)
        sug_frame.pack(fill='x', padx=10, pady=5)
        
        suggestions = [("th", "Þ"), ("sh", "ʃ"), ("ch", "ç"), ("ng", "ŋ"), ("ae", "æ"), ("oe", "œ")]
        for i, (f, t) in enumerate(suggestions):
            def add_sug(f=f, t=t):
                self.template["orthography"]["default"].append({"from": f, "to": t})
                self.ortho_tree.insert('', 'end', values=(f, t))
            ttk.Button(sug_frame, text=f"{f}→{t}", command=add_sug).grid(row=0, column=i, padx=3)
    
    def _build_ontology_step(self):
        """Sound symbolism / element-to-sound mapping - uses anchors defined earlier"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Define Sound Symbolism", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(frame, text=(
            "Map your anchors to sound categories.\n"
            "This creates the 'flavor' of your language - how meaning relates to sound."
        ), foreground='gray').pack()
        
        # Show which anchors are being configured
        info_frame = ttk.LabelFrame(frame, text="Your Anchors (from Step 2)", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        anchor_display = ", ".join(self.anchors) if self.anchors else "(none defined)"
        ttk.Label(info_frame, text=anchor_display, font=('Arial', 11, 'bold')).pack(anchor='w')
        
        # Auto-populate anchors with default sound mappings
        def populate_anchors():
            for anchor in self.anchors:
                if anchor not in self.template["ontology"]:
                    mapping = ELEMENT_SOUND_MAPPING.get(anchor, {"sounds": ["C", "V"], "note": ""})
                    self.template["ontology"][anchor] = {
                        "weight": 1.5,
                        "add_sounds": mapping["sounds"],
                        "note": f"ELEM: {mapping['note']}" if mapping['note'] else ""
                    }
            self._refresh_ontology_display()
        
        # Element table
        edit_frame = ttk.LabelFrame(frame, text="Anchor-to-Sound Mappings", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ("Element", "Weight", "Sounds", "Note")
        self.onto_tree = ttk.Treeview(edit_frame, columns=columns, show='headings', height=8)
        for col in columns:
            self.onto_tree.heading(col, text=col)
            self.onto_tree.column(col, width=100 if col != "Note" else 200)
        self.onto_tree.pack(fill='both', expand=True, pady=5)
        
        # Edit form
        form_frame = ttk.Frame(edit_frame)
        form_frame.pack(fill='x', pady=10)
        
        ttk.Label(form_frame, text="Anchor:").grid(row=0, column=0, padx=2)
        self.onto_elem_var = tk.StringVar()
        ttk.Combobox(form_frame, textvariable=self.onto_elem_var, values=self.anchors, width=12).grid(row=0, column=1, padx=2)
        
        ttk.Label(form_frame, text="Weight:").grid(row=0, column=2, padx=2)
        self.onto_weight_var = tk.StringVar(value="1.5")
        ttk.Entry(form_frame, textvariable=self.onto_weight_var, width=6).grid(row=0, column=3, padx=2)
        
        ttk.Label(form_frame, text="Sounds (CSV):").grid(row=0, column=4, padx=2)
        self.onto_sounds_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.onto_sounds_var, width=20).grid(row=0, column=5, padx=2)
        
        ttk.Label(form_frame, text="Note:").grid(row=0, column=6, padx=2)
        self.onto_note_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.onto_note_var, width=20).grid(row=0, column=7, padx=2)
        
        def add_elem():
            elem = self.onto_elem_var.get().strip()
            if not elem:
                return
            try:
                weight = float(self.onto_weight_var.get())
            except:
                weight = 1.0
            sounds = [s.strip() for s in self.onto_sounds_var.get().split(',') if s.strip()]
            note = self.onto_note_var.get().strip()
            
            self.template["ontology"][elem] = {
                "weight": weight,
                "add_sounds": sounds,
                "note": note
            }
            self._refresh_ontology_display()
        
        def del_elem():
            sel = self.onto_tree.selection()
            if sel:
                elem = sel[0]
                if elem in self.template["ontology"]:
                    del self.template["ontology"][elem]
                self._refresh_ontology_display()
        
        def on_select(e):
            sel = self.onto_tree.selection()
            if sel:
                vals = self.onto_tree.item(sel[0])['values']
                self.onto_elem_var.set(vals[0])
                self.onto_weight_var.set(vals[1])
                self.onto_sounds_var.set(vals[2])
                self.onto_note_var.set(vals[3])
        
        self.onto_tree.bind('<<TreeviewSelect>>', on_select)
        
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Add/Update", command=add_elem).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete", command=del_elem).pack(side='left', padx=5)
        
        # Auto-populate with user's anchors
        populate_anchors()
    
    def _refresh_ontology_display(self):
        """Update ontology tree from template data"""
        self.onto_tree.delete(*self.onto_tree.get_children())
        pos_tags = {"noun", "verb", "adjective", "adverb", "satellite", "conjunction", 
                    "particle", "preposition", "pronoun", "conjuction"}
        for key, data in self.template["ontology"].items():
            if key == "desc" or key in pos_tags:
                continue
            if isinstance(data, dict):
                self.onto_tree.insert('', 'end', iid=key, values=(
                    key,
                    data.get("weight", 1.0),
                    ", ".join(data.get("add_sounds", [])),
                    data.get("note", "")
                ))
    
    def _build_review_step(self):
        """Final review before creating template"""
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Review Your Language Template", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Summary
        summary_frame = ttk.LabelFrame(frame, text="Summary", padding=10)
        summary_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        summary_text = tk.Text(summary_frame, height=20, width=80, font=('Consolas', 10))
        summary_text.pack(fill='both', expand=True)
        
        # Generate summary
        defs = self.template["definitions"]
        onto = self.template["ontology"]
        ortho = self.template["orthography"]
        
        summary = f"Language: {self.language_name}\n"
        summary += "=" * 50 + "\n\n"
        
        summary += "PHONOLOGY\n"
        summary += f"  Consonants: {', '.join(defs.get('C', []))}\n"
        summary += f"  Vowels: {', '.join(defs.get('V', []))}\n\n"
        
        summary += "SYLLABLE STRUCTURES\n"
        for pos in ["noun", "verb", "adjective", "adverb"]:
            shapes = onto.get(pos, {}).get("add_shapes", [])
            if shapes:
                summary += f"  {pos}: {', '.join(shapes)}\n"
        summary += "\n"
        
        if "morphology" in defs:
            summary += "GRAMMAR SUFFIXES\n"
            for mtype, mdata in defs["morphology"].items():
                if mtype != "desc" and isinstance(mdata, dict):
                    summary += f"  {mtype}: {mdata.get('shape', '')} (→{mdata.get('anchor', '')})\n"
            summary += "\n"
        
        summary += "ELEMENTS/ANCHORS\n"
        pos_tags = {"noun", "verb", "adjective", "adverb", "satellite", "conjunction", 
                    "particle", "preposition", "pronoun", "conjuction", "desc"}
        for elem, data in onto.items():
            if elem not in pos_tags and isinstance(data, dict):
                sounds = data.get("add_sounds", [])
                summary += f"  {elem}: {', '.join(sounds)}\n"
        summary += "\n"
        
        if ortho.get("default"):
            summary += "ORTHOGRAPHY RULES\n"
            for rule in ortho["default"][:5]:
                summary += f"  {rule.get('from', '')} → {rule.get('to', '')}\n"
            if len(ortho["default"]) > 5:
                summary += f"  ... and {len(ortho['default']) - 5} more\n"
        
        summary_text.insert('1.0', summary)
        summary_text.config(state='disabled')
        
        # Output location
        out_frame = ttk.LabelFrame(frame, text="Output Files", padding=10)
        out_frame.pack(fill='x', padx=10, pady=10)
        
        template_path = get_template_file(self.language_name)
        anchors_path = get_anchors_file(self.language_name)
        ttk.Label(out_frame, text=f"Template: {template_path}\nAnchors:  {anchors_path}", 
                  font=('Consolas', 9)).pack(anchor='w')
    
    def _finish(self):
        """Create the template and anchors files"""
        # Ensure language directory exists
        get_language_dir(self.language_name)
        
        template_path = get_template_file(self.language_name)
        anchors_path = get_anchors_file(self.language_name)
        
        try:
            # Save template
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(self.template, f, indent=2, ensure_ascii=False)
            
            # Build and save anchors file
            # Format: { "anchor_name": ["Concept1", "Concept2", ...] }
            anchors_data = {}
            for anchor in self.anchors:
                # Get default concepts from ELEMENT_SOUND_MAPPING or generate basic ones
                mapping = ELEMENT_SOUND_MAPPING.get(anchor, {})
                note = mapping.get("note", "")
                # Create a list of associated concepts
                concepts = [
                    anchor.capitalize(),  # The anchor name itself
                    note if note else f"{anchor.capitalize()} concepts",
                ]
                anchors_data[anchor] = concepts
            
            with open(anchors_path, 'w', encoding='utf-8') as f:
                json.dump(anchors_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", 
                f"Language files created!\n\n"
                f"Template: {template_path}\n"
                f"Anchors: {anchors_path}\n\n"
                "You can now edit them in the respective editors.")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save files:\n{e}")


def main():
    parser = argparse.ArgumentParser(description='Conlang Template Wizard')
    parser.add_argument('--language', help='Initial language name', default="NewLanguage")
    args = parser.parse_args()
    
    root = tk.Tk()
    app = TemplateWizard(root, args.language)
    root.mainloop()


if __name__ == "__main__":
    main()
