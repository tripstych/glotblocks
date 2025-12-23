# GlotBlocks Enhancement Integration Guide

This guide explains how to integrate the new process visualization and live preview features into your GlotBlocks project.

## 📊 Feature 1: Visual Process Flow Diagram

**File:** `glotblocks_process_flow.html`

### What It Does
An interactive, animated HTML page that visualizes the entire word generation process with:
- 5 step-by-step explanations
- Visual examples and animations
- Color-coded sections
- Responsive design
- No dependencies (pure HTML/CSS)

### How to Use

#### Option A: Standalone Reference
1. Add the HTML file to your repository at `docs/process_flow.html`
2. Link to it from your main README:
   ```markdown
   ## 🔍 How It Works
   Check out our [interactive process visualization](docs/process_flow.html)
   ```
3. Users can open it directly in a browser

#### Option B: Embed in Your GUI
Add a "How It Works" button to your main launcher:

```python
# In main.py
def show_process_visualization(self):
    """Open the process visualization in browser"""
    import webbrowser
    import os
    
    html_path = os.path.join(os.path.dirname(__file__), 'docs', 'process_flow.html')
    webbrowser.open('file://' + os.path.abspath(html_path))

# Add button to your UI
help_button = ttk.Button(
    main_frame,
    text="📖 How GlotBlocks Works",
    command=self.show_process_visualization
)
help_button.pack(pady=5)
```

#### Option C: Deploy as GitHub Page
1. Add to your repo at `docs/index.html`
2. Enable GitHub Pages in repository settings → Pages → Source: `main` branch `/docs` folder
3. Link will be: `https://tripstych.github.io/glotblocks/`

### Customization
The HTML uses CSS variables for colors. To match your branding:

```css
:root {
    --accent-primary: #00d9ff;     /* Change to your primary color */
    --accent-secondary: #ff6b9d;   /* Change to your secondary color */
    --accent-tertiary: #ffd93d;    /* Change to your tertiary color */
}
```

---

## 🔬 Feature 2: Live Preview Panel

**File:** `conlang_live_preview.py`

### What It Does
A reusable Tkinter widget that:
- Generates sample words in real-time
- Shows step-by-step breakdown of the process
- Explains which anchors influenced each sound
- Displays probability calculations
- Shows constraint checking
- Reveals orthography and morphology rules
- Provides quick example buttons

### Integration Steps

#### Step 1: Add the Module
Copy `conlang_live_preview.py` to your project root directory.

#### Step 2: Integrate into Anchors Editor

```python
# In conlang_edit_anchors.py

from conlang_live_preview import LivePreviewPanel

class AnchorsEditor:
    def __init__(self, parent):
        # ... existing code ...
        
        # Add a preview panel
        self.create_preview_panel()
    
    def create_preview_panel(self):
        """Add live preview to the editor"""
        # Create a new tab or frame
        preview_frame = ttk.Frame(self.notebook)  # or wherever you want it
        self.notebook.add(preview_frame, text="Live Preview")
        
        # Create the preview panel
        self.preview = LivePreviewPanel(
            preview_frame,
            engine=self.engine,  # your ConlangEngine instance
            template=self.template,
            anchors=self.anchors
        )
        self.preview.pack(fill='both', expand=True, padx=10, pady=10)
    
    def on_anchors_changed(self):
        """Called when user modifies anchors"""
        # ... existing code ...
        
        # Update preview with new data
        self.preview.update_data(anchors=self.get_current_anchors())
```

#### Step 3: Integrate into Templates Editor

```python
# In conlang_edit_templates.py

from conlang_live_preview import LivePreviewPanel

class TemplatesEditor:
    def __init__(self, parent):
        # ... existing code ...
        
        # Add preview panel (same as above)
        self.create_preview_panel()
    
    def on_template_changed(self):
        """Called when user modifies template"""
        # ... existing code ...
        
        # Update preview
        self.preview.update_data(template=self.get_current_template())
```

#### Step 4: Connect to Your Engine

Replace the mock functions in `LivePreviewPanel` with actual engine calls:

```python
# In conlang_live_preview.py, replace mock functions:

def _mock_get_weights(self, word: str) -> Dict[str, float]:
    """Get actual semantic weights from your engine"""
    if self.engine:
        return self.engine.analyze_concept(word)
    # fallback to mock for demo
    return {'fire': 0.5, 'water': 0.5}

def _mock_get_sound_pools(self, weights: Dict) -> Dict[str, List[str]]:
    """Get actual sound pools from template"""
    if self.template and self.anchors:
        return self.engine.build_sound_pools(weights, self.template, self.anchors)
    # fallback
    return {'consonants': ['k', 't'], 'vowels': ['a', 'i']}

# ... and so on for other mock functions
```

#### Step 5: Standalone Demo Mode

The module can run standalone for testing:

```bash
python conlang_live_preview.py
```

This creates a demo window you can use to test without the full app.

---

## 🎨 UI Placement Recommendations

### Option 1: Tabbed Interface
Add "Live Preview" as a tab in editors:
```
Anchors Editor
├─ Edit Anchors (tab)
├─ Manage Categories (tab)
└─ Live Preview (tab) ← NEW
```

### Option 2: Side Panel
Split the editor window:
```
┌─────────────┬──────────────┐
│             │              │
│  Edit       │  Live        │
│  Anchors    │  Preview     │
│             │              │
└─────────────┴──────────────┘
```

### Option 3: Popup Window
Add a button "🔍 Test Generation" that opens preview in new window

### Option 4: Bottom Panel
Keep editor on top, preview always visible below

---

## 🔌 Advanced Integration: Real Engine Connection

Here's how to fully connect the preview to your actual engine:

```python
# In conlang_live_preview.py

class LivePreviewPanel:
    def _show_generation_process(self, word: str, manual_weights: Optional[Dict] = None):
        """Use actual engine for generation"""
        
        if not self.engine:
            self.show_error("Engine not initialized")
            return
        
        out = self.output_text
        out.delete('1.0', tk.END)
        
        # Step 1: Get real weights from engine
        if manual_weights:
            weights = manual_weights
        else:
            # Use your engine's semantic analyzer
            from your_semantic_module import analyze_word
            weights = analyze_word(word, self.anchors)
        
        # Display weights...
        out.insert(tk.END, "STEP 1: Conceptual Analysis\n", 'step')
        # ... show weights ...
        
        # Step 2: Build real sound pools
        sound_pools = self.engine.get_sound_pools_for_weights(
            weights, 
            self.template
        )
        
        # Step 3: Generate with actual engine
        result = self.engine.generate_word_detailed(
            weights=weights,
            template=self.template,
            anchors=self.anchors,
            verbose=True  # Add this flag to get detailed info
        )
        
        # Display result breakdown
        # result should contain:
        # - syllables with component info
        # - constraint checks
        # - transformations applied
        # - final word
        
        # ... format and display ...
```

---

## 📝 Quick Start Checklist

- [ ] Add `glotblocks_process_flow.html` to `docs/` folder
- [ ] Link from README.md
- [ ] Add `conlang_live_preview.py` to project root
- [ ] Import LivePreviewPanel in editors
- [ ] Create preview panel instances
- [ ] Connect to engine (replace mock functions)
- [ ] Test with sample words
- [ ] Add help tooltips explaining features
- [ ] Deploy process flow as GitHub Page (optional)

---

## 🎯 Benefits for Users

1. **Process Flow Diagram**
   - Understand the big picture
   - See how data flows through system
   - Beautiful visual aid for documentation
   - Shareable link for teaching others

2. **Live Preview**
   - Instant feedback on changes
   - Learn by experimentation
   - Debug why words sound certain ways
   - Understand anchor/sound relationships
   - See probabilities and weights in action

---

## 🐛 Troubleshooting

**Preview not showing data:**
- Check that engine, template, and anchors are passed correctly
- Verify `update_data()` is called when data changes

**Mock data showing instead of real:**
- Implement actual engine integration
- Replace all `_mock_*` functions with real calls

**UI looks broken:**
- Ensure tkinter fonts are available
- Check that ttk themed widgets are supported
- Test on target platform

**Performance issues:**
- Cache sound pool calculations
- Debounce preview updates
- Show loading indicator for slow operations

---

## 💡 Future Enhancements

Ideas for extending these features:

1. **Animated Transitions**: Show sounds "blending" visually
2. **Sound Comparison**: Generate multiple words side-by-side
3. **Export Report**: Save generation breakdown as PDF
4. **Probability Visualization**: Charts showing anchor weights
5. **Interactive Flow**: Click steps in diagram to jump to that editor
6. **Version Comparison**: Compare words before/after template changes
7. **Batch Preview**: Generate 10 words at once with stats

---

## 📚 Additional Resources

- Put process flow diagram in your docs for onboarding
- Create video walkthrough showing live preview in action
- Add tooltips in UI explaining each step
- Include sample template that showcases all features

---

## Questions?

If you need help integrating or want to customize these features, feel free to ask! The code is well-commented and designed to be modular and extensible.
