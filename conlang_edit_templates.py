import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import re
import argparse
from conlang_language_paths import get_template_file, get_anchors_file

class ConlangEditor:
    def __init__(self, root, language_name="default"):
        self.root = root
        self.language_name = language_name
        self.root.title(f"Ontology Tuner - {language_name}")
        self.root.geometry("1100x750") 
        
        # Default Data
        self.data = {
            "definitions": {"desc": "Phoneme categories"},
            "constraints": {"desc": "Regex rules for validation"},
            "orthography": {"desc": "Spelling replacement rules"},
            "ontology": {"desc": "Core concept Anchors and their acoustic profiles"}
        }
        
        # KNOWN POS TAGS (For grouping)
        self.CORE_POS = {
            "noun",
            "verb",
            "adjective",
            "adverb",
            "satellite",
            "conjunction",
            "conjuction",
            "particle",
            "preposition",
            "pronoun",
        }
        
        # Load defined anchors from anchors file
        self.defined_anchors = set()
        self._load_anchors()
        
        self._create_ui()
        self._load_initial_file()
    
    def _load_anchors(self):
        """Load anchors from language-specific anchors file"""
        anchors_path = get_anchors_file(self.language_name)
        if os.path.exists(anchors_path):
            try:
                with open(anchors_path, 'r', encoding='utf-8') as f:
                    anchors_data = json.load(f)
                self.defined_anchors = set(anchors_data.keys())
                print(f"Loaded {len(self.defined_anchors)} anchors from {anchors_path}")
            except Exception as e:
                print(f"Could not load anchors: {e}")
        else:
            # Try default anchors
            default_path = get_anchors_file("default")
            if os.path.exists(default_path):
                try:
                    with open(default_path, 'r', encoding='utf-8') as f:
                        anchors_data = json.load(f)
                    self.defined_anchors = set(anchors_data.keys())
                    print(f"Loaded {len(self.defined_anchors)} anchors from default")
                except Exception as e:
                    print(f"Could not load default anchors: {e}")
    
    def _load_initial_file(self):
        """Load language-specific or default template file"""
        candidates = [
            get_template_file(self.language_name),
            "default_template.json",
            "conlang_template.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                self.load_file(path)
                return
        print("No template file found, starting with defaults")

    def _create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ontology_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ontology_frame, text="Ontology (Tags)")
        self._build_ontology_tab()
        
        self.definitions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.definitions_frame, text="Definitions (Phonemes)")
        self._build_definitions_tab()
        
        self.constraints_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.constraints_frame, text="Constraints (Rules)")
        self._build_constraints_tab()
        
        self.ortho_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ortho_frame, text="Orthography (Spelling)")
        self._build_orthography_tab()
        
        # Add save buttons at bottom
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        save_as_btn = ttk.Button(button_frame, text="Save As...", command=self.save_as_file)
        save_as_btn.pack(side='right', padx=5)
        
        save_btn = ttk.Button(button_frame, text="Save", command=self.save_file)
        save_btn.pack(side='right', padx=5)
        
        open_btn = ttk.Button(button_frame, text="Open...", command=self.open_file)
        open_btn.pack(side='right', padx=5)
        
        self.status_label = ttk.Label(button_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)

    def _add_desc_header(self, parent, data_key):
        # Hidden purely for UI cleanliness, data is still there
        pass 

    # --- TAB 1: ONTOLOGY (THE FIXED GROUPING) ---
    def _build_ontology_tab(self):
        paned = ttk.PanedWindow(self.ontology_frame, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # LEFT: List
        left_frame = ttk.Frame(paned, width=280)
        paned.add(left_frame, weight=1)
        
        # Filter
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill='x', pady=2)
        ttk.Label(filter_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_concepts)
        ttk.Entry(filter_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True)

        self.concept_listbox = tk.Listbox(left_frame, activestyle='none')
        self.concept_listbox.pack(fill='both', expand=True)
        self.concept_listbox.bind('<<ListboxSelect>>', self._on_concept_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="+ New Element", command=self._add_concept).pack(fill='x')
        ttk.Button(btn_frame, text="- Delete Selected", command=self._del_concept).pack(fill='x')
        
        # RIGHT: Tuner
        self.tuner_frame = ttk.Frame(paned)
        paned.add(self.tuner_frame, weight=3)
        
        # Header Info
        head_frame = ttk.LabelFrame(self.tuner_frame, text="Tag Settings", padding=5)
        head_frame.pack(fill='x', pady=5)
        
        ttk.Label(head_frame, text="Role/Note:").grid(row=0, column=0, sticky='w')
        self.note_var = tk.StringVar()
        ttk.Entry(head_frame, textvariable=self.note_var).grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(head_frame, text="Weight Multiplier:").grid(row=0, column=2, sticky='e')
        self.weight_var = tk.DoubleVar(value=1.0)
        ttk.Entry(head_frame, textvariable=self.weight_var, width=8).grid(row=0, column=3, sticky='e', padx=5)
        
        head_frame.columnconfigure(1, weight=1)
        
        # Tabs for properties
        self.prop_notebook = ttk.Notebook(self.tuner_frame)
        self.prop_notebook.pack(fill='both', expand=True)
        
        self.snd_list = self._create_property_list(self.prop_notebook, "Sounds (Materials)", "definitions")
        self.shp_list = self._create_property_list(self.prop_notebook, "Shapes (Blueprints)", None, "Syntax: '(C)VC'. ( ) is optional.")
        self.rul_list = self._create_property_list(self.prop_notebook, "Rules (Limits)", "constraints")
        self.spl_list = self._create_property_list(self.prop_notebook, "Spelling", "orthography")

        self._toggle_tuner(False)

    def _filter_concepts(self, *args):
        search = self.search_var.get().lower()
        self.concept_listbox.delete(0, 'end')
        
        all_keys = [k for k in self.data.get("ontology", {}).keys() if k != "desc"]
        
        # SEPARATION LOGIC
        pos_group = sorted([k for k in all_keys if k in self.CORE_POS])
        elem_group = sorted([k for k in all_keys if k not in self.CORE_POS])
        
        # Find missing anchors (in anchors file but not in ontology)
        missing_anchors = self.defined_anchors - set(all_keys) - self.CORE_POS
        
        # 1. GRAMMAR SECTION
        self.concept_listbox.insert('end', "--- GRAMMAR (POS) ---")
        self.concept_listbox.itemconfig('end', fg='blue', bg='#f0f0f0', selectbackground='#f0f0f0', selectforeground='blue')
        
        for k in pos_group:
            if search in k.lower():
                self.concept_listbox.insert('end', k)
                self.concept_listbox.itemconfig('end', fg='black')

        # 2. ANCHORS SECTION
        self.concept_listbox.insert('end', "") # Spacer
        self.concept_listbox.insert('end', "--- ANCHORS / CONCEPTS ---")
        self.concept_listbox.itemconfig('end', fg='green', bg='#f0f0f0', selectbackground='#f0f0f0', selectforeground='green')
        
        for k in elem_group:
            if search in k.lower():
                self.concept_listbox.insert('end', k)
                # Color based on anchor status
                if k in self.defined_anchors:
                    self.concept_listbox.itemconfig('end', fg='black')  # Valid anchor
                else:
                    self.concept_listbox.itemconfig('end', fg='#cc0000')  # RED: Not in anchors file
        
        # 3. MISSING ANCHORS (in anchors file but not in template)
        missing_filtered = sorted([k for k in missing_anchors if search in k.lower()])
        if missing_filtered:
            self.concept_listbox.insert('end', "") # Spacer
            self.concept_listbox.insert('end', "--- MISSING (click to add) ---")
            self.concept_listbox.itemconfig('end', fg='#006600', bg='#e8ffe8', selectbackground='#e8ffe8', selectforeground='#006600')
            
            for k in missing_filtered:
                self.concept_listbox.insert('end', f"+ {k}")
                self.concept_listbox.itemconfig('end', fg='#006600', bg='#f0fff0')  # GREEN: New anchor to add

    def _on_concept_select(self, event):
        sel = self.concept_listbox.curselection()
        if not sel:
            self._toggle_tuner(False)
            return
            
        key = self.concept_listbox.get(sel[0])
        
        # Ignore clicks on Headers or Spacers
        if key.startswith("---") or key == "":
            self.concept_listbox.selection_clear(0, 'end')
            self._toggle_tuner(False)
            return
        
        # Handle click on missing anchor (+ prefix) - add it to ontology
        if key.startswith("+ "):
            anchor_name = key[2:]  # Remove "+ " prefix
            self.data["ontology"][anchor_name] = {"weight": 1.0, "note": f"ELEM: Added from anchors"}
            self._filter_concepts()
            self.status_label.config(text=f"Added anchor: {anchor_name}")
            return
            
        data = self.data["ontology"].get(key, {})
        
        self._toggle_tuner(True)
        self.current_concept_key = key
        
        self.weight_var.set(data.get("weight", 1.0))
        self.note_var.set(data.get("note", ""))
        
        self._populate_list(self.snd_list, data.get("add_sounds", []))
        self._populate_list(self.shp_list, data.get("add_shapes", []))
        self._populate_list(self.rul_list, data.get("add_rules", []))
        self._populate_list(self.spl_list, data.get("add_spelling", []))

    # --- STANDARD METHODS (Unchanged but included for safety) ---
    def _create_property_list(self, notebook, title, source_key, hint_text=None):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        if hint_text: ttk.Label(frame, text=hint_text, foreground="#555").pack(anchor='w', padx=5, pady=2)
        lb = tk.Listbox(frame); lb.pack(fill='both', expand=True, padx=5, pady=2)
        btn_frame = ttk.Frame(frame); btn_frame.pack(fill='x', padx=5, pady=5)
        
        if source_key:
            input_var = tk.StringVar()
            entry = ttk.Combobox(btn_frame, textvariable=input_var, state="readonly")
            def update_values():
                keys = [k for k in self.data.get(source_key, {}).keys() if k != "desc"]
                entry['values'] = sorted(keys)
            entry.bind('<Button-1>', lambda e: update_values())
        else:
            entry = ttk.Entry(btn_frame)
        entry.pack(side='left', fill='x', expand=True)
        
        def add_item():
            val = entry.get().strip()
            if val:
                lb.insert('end', val)
                if hasattr(entry, 'delete'): entry.delete(0, 'end')
                else: entry.set('')
                self._save_current()
        def del_item():
            sel = lb.curselection()
            if sel: lb.delete(sel[0]); self._save_current()
        if not source_key: entry.bind('<Return>', lambda e: add_item())
        ttk.Button(btn_frame, text="Add", command=add_item).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Del", command=del_item).pack(side='left', padx=2)
        return lb

    def _populate_list(self, lb, items):
        lb.delete(0, 'end')
        for i in items: lb.insert('end', i)

    def _save_current(self, event=None):
        if not hasattr(self, 'current_concept_key') or not self.current_concept_key: return
        key = self.current_concept_key
        try: w = float(self.weight_var.get())
        except: w = 1.0
        new_data = {
            "weight": w, "note": self.note_var.get(),
            "add_sounds": list(self.snd_list.get(0, 'end')),
            "add_shapes": list(self.shp_list.get(0, 'end')),
            "add_rules": list(self.rul_list.get(0, 'end')),
            "add_spelling": list(self.spl_list.get(0, 'end')),
        }
        self.data["ontology"][key] = {k: v for k, v in new_data.items() if v or k=='weight'}

    def _toggle_tuner(self, state):
        for child in self.tuner_frame.winfo_children():
            try: child.configure(state='normal' if state else 'disabled')
            except: pass

    def _add_concept(self):
        name = simpledialog.askstring("New Element", "Element Name (e.g. 'iron'):")
        if name and name != "desc" and name not in self.data["ontology"]:
            self.data["ontology"][name] = {"weight": 1.0}
            self._filter_concepts()

    def _del_concept(self):
        sel = self.concept_listbox.curselection()
        if sel:
            key = self.concept_listbox.get(sel[0])
            if key in self.data["ontology"]:
                del self.data["ontology"][key]
                self._filter_concepts()
                self._toggle_tuner(False)

    def _build_definitions_tab(self):
        """Build definitions tab with paned interface for phonemes and morphology"""
        paned = ttk.PanedWindow(self.definitions_frame, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # LEFT: Category list
        left = ttk.Frame(paned, width=180)
        paned.add(left, weight=1)
        
        ttk.Label(left, text="Categories", font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=2)
        self.def_list = tk.Listbox(left, exportselection=False)
        self.def_list.pack(fill='both', expand=True, padx=5, pady=2)
        self.def_list.bind('<<ListboxSelect>>', self._on_def_select)
        
        # Add/remove category buttons
        def_btn_frame = ttk.Frame(left)
        def_btn_frame.pack(fill='x', padx=5, pady=5)
        self.new_def_entry = ttk.Entry(def_btn_frame, width=12)
        self.new_def_entry.pack(side='left', padx=2)
        ttk.Button(def_btn_frame, text="+", width=3, command=self._add_def_category).pack(side='left', padx=2)
        ttk.Button(def_btn_frame, text="-", width=3, command=self._del_def_category).pack(side='left', padx=2)
        
        # RIGHT: Context-sensitive editor
        right = ttk.Frame(paned)
        paned.add(right, weight=3)
        
        self.def_editor_frame = ttk.Frame(right)
        self.def_editor_frame.pack(fill='both', expand=True)
        
        # Placeholder label
        self.def_placeholder = ttk.Label(self.def_editor_frame, text="Select a category to edit", foreground='gray')
        self.def_placeholder.pack(pady=50)
        
        self.cur_def_key = None
        self._refresh_definitions()
    
    def _refresh_definitions(self):
        """Refresh the definitions category list"""
        self.def_list.delete(0, 'end')
        for k in self.data.get("definitions", {}):
            if k != "desc":
                self.def_list.insert('end', k)
    
    def _on_def_select(self, event=None):
        """Handle category selection - show appropriate editor"""
        sel = self.def_list.curselection()
        if not sel:
            return
        key = self.def_list.get(sel[0])
        self.cur_def_key = key
        value = self.data.get("definitions", {}).get(key)
        
        # Clear editor frame
        for child in self.def_editor_frame.winfo_children():
            child.destroy()
        
        if key == "morphology" and isinstance(value, dict):
            self._build_morphology_editor(value)
        elif isinstance(value, list):
            self._build_phoneme_list_editor(key, value)
        elif isinstance(value, dict):
            self._build_morphology_editor(value)
        else:
            ttk.Label(self.def_editor_frame, text=f"Unknown format for '{key}'").pack(pady=20)
    
    def _build_phoneme_list_editor(self, key, items):
        """Build editor for simple phoneme list (e.g., C, V, Stops)"""
        ttk.Label(self.def_editor_frame, text=f"Phonemes: {key}", font=('Arial', 12, 'bold')).pack(anchor='w', padx=5, pady=5)
        
        # Listbox for items
        list_frame = ttk.Frame(self.def_editor_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        for item in items:
            listbox.insert('end', item)
        
        # Entry + buttons
        entry_frame = ttk.Frame(self.def_editor_frame)
        entry_frame.pack(fill='x', padx=5, pady=5)
        
        entry = ttk.Entry(entry_frame, width=20)
        entry.pack(side='left', padx=5)
        
        def add_item():
            val = entry.get().strip()
            if val:
                listbox.insert('end', val)
                entry.delete(0, 'end')
                self._save_phoneme_list(key, listbox)
        
        def del_item():
            sel = listbox.curselection()
            if sel:
                listbox.delete(sel[0])
                self._save_phoneme_list(key, listbox)
        
        entry.bind('<Return>', lambda e: add_item())
        ttk.Button(entry_frame, text="Add", command=add_item).pack(side='left', padx=2)
        ttk.Button(entry_frame, text="Remove", command=del_item).pack(side='left', padx=2)
    
    def _save_phoneme_list(self, key, listbox):
        """Save phoneme list back to data"""
        items = [listbox.get(i) for i in range(listbox.size())]
        self.data["definitions"][key] = items
    
    def _build_morphology_editor(self, morph_dict):
        """Build editor for morphology dict (grammar suffixes)"""
        ttk.Label(self.def_editor_frame, text="Morphology (Grammar Suffixes)", font=('Arial', 12, 'bold')).pack(anchor='w', padx=5, pady=5)
        
        # Treeview for morphology entries
        columns = ("Type", "Anchor", "Shape", "Note")
        tree = ttk.Treeview(self.def_editor_frame, columns=columns, show='headings', height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != "Note" else 200)
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Populate
        for mtype, mdata in morph_dict.items():
            if mtype == "desc" or not isinstance(mdata, dict):
                continue
            tree.insert('', 'end', iid=mtype, values=(
                mtype,
                mdata.get("anchor", ""),
                mdata.get("shape", ""),
                mdata.get("note", "")
            ))
        
        # Entry fields for editing
        edit_frame = ttk.LabelFrame(self.def_editor_frame, text="Edit Entry", padding=5)
        edit_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(edit_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=2)
        type_ent = ttk.Entry(edit_frame, width=15)
        type_ent.grid(row=0, column=1, padx=2)
        
        ttk.Label(edit_frame, text="Anchor:").grid(row=0, column=2, sticky='w', padx=2)
        anchor_ent = ttk.Entry(edit_frame, width=15)
        anchor_ent.grid(row=0, column=3, padx=2)
        
        ttk.Label(edit_frame, text="Shape:").grid(row=1, column=0, sticky='w', padx=2)
        shape_ent = ttk.Entry(edit_frame, width=15)
        shape_ent.grid(row=1, column=1, padx=2)
        
        ttk.Label(edit_frame, text="Note:").grid(row=1, column=2, sticky='w', padx=2)
        note_ent = ttk.Entry(edit_frame, width=30)
        note_ent.grid(row=1, column=3, padx=2)
        
        def on_select(e):
            sel = tree.selection()
            if sel:
                vals = tree.item(sel[0])['values']
                type_ent.delete(0, 'end'); type_ent.insert(0, vals[0])
                anchor_ent.delete(0, 'end'); anchor_ent.insert(0, vals[1])
                shape_ent.delete(0, 'end'); shape_ent.insert(0, vals[2])
                note_ent.delete(0, 'end'); note_ent.insert(0, vals[3])
        
        tree.bind('<<TreeviewSelect>>', on_select)
        
        def add_or_update():
            mtype = type_ent.get().strip()
            if not mtype:
                return
            entry = {
                "anchor": anchor_ent.get().strip(),
                "shape": shape_ent.get().strip(),
                "note": note_ent.get().strip()
            }
            # Update data
            if "morphology" not in self.data["definitions"]:
                self.data["definitions"]["morphology"] = {}
            self.data["definitions"]["morphology"][mtype] = entry
            # Update tree
            if tree.exists(mtype):
                tree.item(mtype, values=(mtype, entry["anchor"], entry["shape"], entry["note"]))
            else:
                tree.insert('', 'end', iid=mtype, values=(mtype, entry["anchor"], entry["shape"], entry["note"]))
        
        def delete_entry():
            sel = tree.selection()
            if sel:
                mtype = sel[0]
                tree.delete(mtype)
                if "morphology" in self.data["definitions"] and mtype in self.data["definitions"]["morphology"]:
                    del self.data["definitions"]["morphology"][mtype]
        
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=5)
        ttk.Button(btn_frame, text="Add/Update", command=add_or_update).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete", command=delete_entry).pack(side='left', padx=5)
    
    def _add_def_category(self):
        """Add a new definition category"""
        name = self.new_def_entry.get().strip()
        if not name or name == "desc":
            return
        if name in self.data.get("definitions", {}):
            messagebox.showwarning("Exists", f"Category '{name}' already exists.")
            return
        # Default to empty list (phoneme category)
        self.data["definitions"][name] = []
        self._refresh_definitions()
        self.new_def_entry.delete(0, 'end')
    
    def _del_def_category(self):
        """Delete selected definition category"""
        sel = self.def_list.curselection()
        if not sel:
            return
        key = self.def_list.get(sel[0])
        if key == "morphology":
            if not messagebox.askyesno("Confirm", "Delete entire morphology section?"):
                return
        if key in self.data.get("definitions", {}):
            del self.data["definitions"][key]
        self._refresh_definitions()
        # Clear editor
        for child in self.def_editor_frame.winfo_children():
            child.destroy()
        self.def_placeholder = ttk.Label(self.def_editor_frame, text="Select a category to edit", foreground='gray')
        self.def_placeholder.pack(pady=50)

    def _build_constraints_tab(self):
        # ... (Same as previous version) ...
        columns = ("Label", "Pattern")
        tree = ttk.Treeview(self.constraints_frame, columns=columns, show='headings')
        tree.heading("Label", text="Label"); tree.heading("Pattern", text="Regex")
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        frame = ttk.Frame(self.constraints_frame); frame.pack(fill='x', padx=5, pady=5)
        k_ent = ttk.Entry(frame, width=15); k_ent.pack(side='left', padx=5)
        v_ent = ttk.Entry(frame); v_ent.pack(side='left', fill='x', expand=True, padx=5)
        def refresh():
            tree.delete(*tree.get_children())
            for k, v in self.data.get("constraints", {}).items():
                if k!="desc": tree.insert('', 'end', values=(k, v["pattern"] if isinstance(v, dict) else v))
        def add():
            k, v = k_ent.get().strip(), v_ent.get()
            if k: self.data["constraints"][k] = {"pattern": v}; refresh()
        def delete():
            sel = tree.selection()
            if sel: del self.data["constraints"][tree.item(sel[0])['values'][0]]; refresh()
        ttk.Button(frame, text="Add/Update", command=add).pack(side='left')
        ttk.Button(frame, text="Delete", command=delete).pack(side='left', padx=5)
        self._refresh_constraints = refresh

    def _build_orthography_tab(self):
        # ... (Same as previous version) ...
        paned = ttk.PanedWindow(self.ortho_frame, orient=tk.HORIZONTAL); paned.pack(fill='both', expand=True)
        left = ttk.Frame(paned, width=150); paned.add(left)
        self.ortho_list = tk.Listbox(left); self.ortho_list.pack(fill='both', expand=True)
        right = ttk.Frame(paned); paned.add(right)
        self.ortho_tree = ttk.Treeview(right, columns=("F","T"), show='headings')
        self.ortho_tree.heading("F", text="From"); self.ortho_tree.heading("T", text="To")
        self.ortho_tree.pack(fill='both', expand=True, padx=5, pady=5)
        in_frame = ttk.Frame(right); in_frame.pack(fill='x')
        f_ent = ttk.Entry(in_frame, width=10); f_ent.pack(side='left', padx=2)
        t_ent = ttk.Entry(in_frame, width=10); t_ent.pack(side='left', padx=2)
        self.cur_orth = None
        def ref_rules(e=None):
            sel = self.ortho_list.curselection()
            if not sel: return
            key = self.ortho_list.get(sel[0])
            self.cur_orth = key; self.ortho_tree.delete(*self.ortho_tree.get_children())
            for r in self.data["orthography"].get(key, []): self.ortho_tree.insert('','end',values=(r.get("from"), r.get("to")))
        self.ortho_list.bind('<<ListboxSelect>>', ref_rules)
        def add_r():
            if self.cur_orth: 
                d = self.data["orthography"]
                if not isinstance(d[self.cur_orth], list): d[self.cur_orth] = []
                d[self.cur_orth].append({"from":f_ent.get(), "to":t_ent.get()}); ref_rules()
        def add_g():
            n = simpledialog.askstring("New", "Name:"); 
            if n: self.data["orthography"][n] = []; self._refresh_ortho_list()
        ttk.Button(in_frame, text="Add", command=add_r).pack(side='left')
        ttk.Button(left, text="+ Group", command=add_g).pack(fill='x')
        def ref_l():
            self.ortho_list.delete(0,'end')
            for k in self.data.get("orthography",{}): 
                if k!="desc": self.ortho_list.insert('end', k)
        self._refresh_ortho_list = ref_l

    # --- FILE OPS ---
    def open_file(self):
        fn = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if fn: self.load_file(fn)
    
    def load_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: 
                self.data = json.load(f)
            self.root.title(f"Ontology Tuner - {os.path.basename(filename)}")
            self._filter_concepts()
            if hasattr(self, '_refresh_definitions'): self._refresh_definitions()
            if hasattr(self, '_refresh_constraints'): self._refresh_constraints()
            if hasattr(self, '_refresh_ortho_list'): self._refresh_ortho_list()
            if hasattr(self, 'status_label'): self.status_label.config(text=f"Loaded {filename}")
        except Exception as e: 
            messagebox.showerror("Error", f"Failed: {e}")
    
    def save_file(self):
        """Save to language-specific file"""
        self._save_current()
        file_path = get_template_file(self.language_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f: 
                json.dump(self.data, f, indent=2)
            self.status_label.config(text=f"Saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {e}")
    
    def save_as_file(self):
        """Save with file dialog"""
        self._save_current()
        fn = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=os.path.basename(get_template_file(self.language_name))
        )
        if fn:
            try:
                with open(fn, 'w', encoding='utf-8') as f: 
                    json.dump(self.data, f, indent=2)
                self.status_label.config(text=f"Saved to {os.path.basename(fn)}")
                messagebox.showinfo("Saved", f"Written to {fn}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving: {e}")

def main():
    parser = argparse.ArgumentParser(description='Conlang Template Editor')
    parser.add_argument('--language', help='Name of language to edit', default="default")
    args = parser.parse_args()
    
    root = tk.Tk()
    app = ConlangEditor(root, args.language)
    root.mainloop()

if __name__ == "__main__":
    main()