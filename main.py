import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import threading
import queue
import json
from conlang_language_paths import list_languages, get_language_dir, get_dictionary_file

class ConlangLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Conlang Tools Launcher")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # Get script directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize queue for thread-safe GUI updates
        self.msg_queue = queue.Queue()
        self.root.after(100, self.check_queue)
        
        # Title
        title_label = ttk.Label(root, text="Conlang Tools", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=15)
        
        # Language Name Input
        lang_frame = ttk.Frame(root)
        lang_frame.pack(fill="x", padx=20, pady=5)

        ttk.Label(lang_frame, text="Language:").pack(side="left", padx=5)
        self.language_var = tk.StringVar(value="default")
        
        # Combobox with existing languages + ability to type new ones
        existing_langs = list_languages()
        if "default" not in existing_langs:
            existing_langs.insert(0, "default")
        self.language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                           values=existing_langs, width=18)
        self.language_combo.pack(side="left", padx=5)
        
        # Refresh button to update language list
        ttk.Button(lang_frame, text="↻", width=2, 
                   command=self.refresh_languages).pack(side="left")
        
        # Editors Section
        editor_frame = ttk.LabelFrame(root, text="Editors", padding=10)
        editor_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Button(editor_frame, text="✨ Language Wizard", command=self.launch_wizard, width=25).pack(pady=3)
        ttk.Button(editor_frame, text="Edit Anchors", command=self.launch_edit_anchors, width=25).pack(pady=3)
        ttk.Button(editor_frame, text="Edit Templates", command=self.launch_edit_templates, width=25).pack(pady=3)
        
        # Build Status
        self.status_var = tk.StringVar(value="-Build Status-")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=5, pady=5)
        
        # Seed Input (for Build Dictionaries)
        seed_frame = ttk.Frame(root)
        seed_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(seed_frame, text="*Seed:").pack(side="left", padx=5)
        self.seed_var = tk.StringVar(value="42")
        seed_entry = ttk.Entry(seed_frame, textvariable=self.seed_var, width=10)
        seed_entry.pack(side="left", padx=5)
        ttk.Button(seed_frame, text="Random", width=7, command=self.randomize_seed).pack(side="left", padx=2)
        
        # Build Section
        build_frame = ttk.LabelFrame(root, text="Build Tools", padding=10)
        build_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Button(build_frame, text="*Build Data", command=self.launch_build_data, width=25).pack(pady=3)
        ttk.Button(build_frame, text="Build Dictionaries", command=self.launch_build_dictionaries, width=25).pack(pady=3)
        ttk.Label(build_frame, text="*Build Data takes a while").pack(side="left", padx=5)
        
        # Utilities Section
        util_frame = ttk.LabelFrame(root, text="Utilities", padding=10)
        util_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Button(util_frame, text="Interactive Translator", command=self.open_translator_window, width=25).pack(pady=3)
        
        # Translator instance (lazy loaded)
        self.translator = None
        
        # Status bar

    def run_script(self, script_name, pass_language=False):
        script_path = os.path.join(self.script_dir, script_name)
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found: {script_name}")
            return
        
        self.status_var.set(f"Launching {script_name}...")
        self.root.update()
        
        try:
            cmd = [sys.executable, script_path]
            if pass_language:
                language = self.language_var.get().strip() or "default"
                cmd.extend(["--language", language])
            subprocess.Popen(cmd, cwd=self.script_dir)
            self.status_var.set(f"Launched {script_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {script_name}:\n{e}")
            self.status_var.set("Error launching script")

    def launch_wizard(self):
        """Launch wizard and refresh language list when it closes"""
        script_path = os.path.join(self.script_dir, "conlang_template_wizard.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Wizard script not found")
            return
        
        self.status_var.set("Launching wizard...")
        self.root.update()
        
        language = self.language_var.get().strip() or "NewLanguage"
        cmd = [sys.executable, script_path, "--language", language]
        
        def run_and_refresh():
            try:
                proc = subprocess.Popen(cmd, cwd=self.script_dir)
                proc.wait()  # Wait for wizard to close
                # Refresh language list on main thread
                self.root.after(100, self.refresh_languages)
            except Exception as e:
                print(f"Wizard error: {e}")
        
        # Run in background thread so UI stays responsive
        import threading
        thread = threading.Thread(target=run_and_refresh, daemon=True)
        thread.start()
        self.status_var.set("Wizard opened")

    def launch_edit_anchors(self):
        self.run_script("conlang_edit_anchors.py", pass_language=True)

    def launch_edit_templates(self):
        self.run_script("conlang_edit_templates.py", pass_language=True)

    def launch_build_data(self):
        script_path = os.path.join(self.script_dir, "conlang_build_data.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Script not found: conlang_build_data.py")
            return
        
        language = self.language_var.get().strip() or "default"
        output_file = get_language_dir(language)  # For status display
        
        # Reset counter file
        counter_path = os.path.join(self.script_dir, ".tmp.counter")
        try:
            with open(counter_path, 'w') as f:
                f.write("0")
        except:
            pass
        
        self.status_var.set("Building data...")
        self.root.update()
        
        # Start monitoring thread
        self.start_monitoring_thread(output_file)
        
        try:
            cmd = [sys.executable, script_path, "--language", language]
            subprocess.Popen(cmd, cwd=self.script_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch build:\n{e}")
            self.status_var.set("Error")

    def launch_build_dictionaries(self):
        script_path = os.path.join(self.script_dir, "conlang_build_dictionaries.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Script not found: conlang_build_dictionaries.py")
            return
        
        language = self.language_var.get().strip() or "default"
        
        self.status_var.set("Building dictionary...")
        self.root.update()
        
        try:
            cmd = [sys.executable, script_path, "--language", language]
            # Add seed argument
            seed_str = self.seed_var.get().strip()
            if seed_str:
                try:
                    seed_val = int(seed_str)
                    cmd.extend(["--seed", str(seed_val)])
                except ValueError:
                    pass  # Ignore invalid seed values
            
            def run_and_notify():
                proc = subprocess.Popen(cmd, cwd=self.script_dir)
                proc.wait()
                self.msg_queue.put("Dictionary build finished")
            
            threading.Thread(target=run_and_notify, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch build:\n{e}")
            self.status_var.set("Error")

    def randomize_seed(self):
        """Generate a random seed value"""
        import random
        self.seed_var.set(str(random.randint(1, 999999)))
    
    def refresh_languages(self):
        """Refresh the language dropdown with available languages"""
        existing_langs = list_languages()
        if "default" not in existing_langs:
            existing_langs.insert(0, "default")
        self.language_combo['values'] = existing_langs
        self.status_var.set(f"Found {len(existing_langs)} languages")
    
    def load_translator(self):
        """Load the translator if not already loaded"""
        if self.translator is not None:
            return True
        
        language = self.language_var.get().strip() or "default"
        lexicon_path = get_dictionary_file(language)
        
        if not os.path.exists(lexicon_path):
            messagebox.showerror("Error", f"Dictionary not found: {lexicon_path}\nPlease build the dictionary first.")
            return False
        
        try:
            from conlang_translate import ConlangTranslator
            from conlang_language_paths import get_suffixes_file
            suffix_path = get_suffixes_file(language)
            self.translator = ConlangTranslator.from_json(lexicon_path, suffix_file=suffix_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load translator:\n{e}")
            return False
    
    def open_translator_window(self):
        """Open the interactive translator window"""
        if not self.load_translator():
            return
        
        # Create new window
        trans_win = tk.Toplevel(self.root)
        trans_win.title("Interactive Translator")
        trans_win.geometry("600x300")
        trans_win.resizable(True, True)
        
        # Input section
        input_frame = ttk.LabelFrame(trans_win, text="English Input", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        input_text = ttk.Entry(input_frame, font=("Consolas", 11))
        input_text.pack(fill="x", expand=False)
        
        # Buttons
        btn_frame = ttk.Frame(trans_win)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        def do_translate():
            text = input_text.get().strip()
            if not text:
                return
            try:
                result = self.translator.translate_sentence(text)
                output_text.config(state=tk.NORMAL)
                output_text.delete("1.0", tk.END)
                output_text.insert("1.0", result)
                output_text.config(state=tk.DISABLED)
                input_text.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Translation failed:\n{e}")
        
        def clear_output():
            output_text.config(state=tk.NORMAL)
            output_text.delete("1.0", tk.END)
            output_text.config(state=tk.DISABLED)
        
        def reload_dict():
            self.translator = None
            if self.load_translator():
                self.status_var.set("Dictionary reloaded")
        
        ttk.Button(btn_frame, text="Translate", command=do_translate, width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", command=clear_output, width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reload Dictionary", command=reload_dict, width=15).pack(side="right", padx=5)
        
        # Bind Enter key to translate
        input_text.bind("<Return>", lambda e: do_translate())
        
        # Output section
        output_frame = ttk.LabelFrame(trans_win, text="Translation Output", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        output_text = scrolledtext.ScrolledText(output_frame, height=2, wrap=tk.WORD, font=("Consolas", 11), state=tk.DISABLED)
        output_text.pack(fill="both", expand=True)
        
        # Word count label
        word_count = len(self.translator.lexicon)
        ttk.Label(trans_win, text=f"Dictionary: {word_count} words loaded").pack(pady=5)
        
        input_text.focus_set()
    
    def start_monitoring_thread(self, output_file=None):
        """Start the monitoring thread for build progress"""
        self.output_file = output_file
        threading.Thread(target=self.monitor_counter_file, daemon=True).start()
    
    def monitor_counter_file(self):
        """Monitor .tmp.counter file for build progress"""
        import time
        counter_path = os.path.join(self.script_dir, ".tmp.counter")
        time.sleep(2)
        while True:
            try:
                if os.path.exists(counter_path):
                    with open(counter_path, 'r') as f:
                        lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if last_line == "done":
                            if hasattr(self, 'output_file') and self.output_file:
                                txt_file = self.output_file.replace('.json', '.txt')
                                msg = f"Built {self.output_file} and {txt_file}"
                            else:
                                msg = "Completed!"
                            self.msg_queue.put(msg)
                            break
                        else:
                            self.msg_queue.put(f"Processing: {last_line}")
                time.sleep(1)
            except:
                time.sleep(1)
    
    def check_queue(self):
        """Check queue for messages from monitoring thread"""
        try:
            while True:
                message = self.msg_queue.get_nowait()
                self.status_var.set(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

def main():
    root = tk.Tk()
    app = ConlangLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
