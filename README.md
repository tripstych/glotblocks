# Ontological Word Generator

This workspace includes a simple engine to generate words for a constructed language using an "additive blender" of concepts.

## Files
- `conlang_template.json`: Configuration with `definitions`, `constraints`, `orthography`, and `ontology`.
- `conlang_engine.py`: Python module implementing `ConlangEngine` with a test runner.

## Quick Start
1. Ensure Python 3.8+ is installed.
2. Run the engine:

```bash
python conlang_engine.py
```

It will load `conlang_template.json` and print 5 test words for the tags `fire` and `noun`.

## Notes
- Constraints are treated as forbidden regexes: if a word matches an enabled pattern, it is rejected.
- Sound pools are weighted by concept `weight`. Definitions referenced in `add_sounds` are expanded into their respective slot pools.
- Literal phonemes in `add_sounds` are added to matching definition pools (if found) or to a generic `any` pool used by all slots.
- Orthography rules are applied in the order of the aggregated `add_spelling` keys after a word passes constraints.
