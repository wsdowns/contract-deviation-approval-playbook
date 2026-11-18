# Build scripts

These scripts show how the documents were produced. The documents in `../contracts/` are the authoritative copies. The DoA matrix is built with `tools/doa_matrix.py` at the repository root.

- `lakeshore/build.js`: generates the Lakeshore Health SaaS Agreement with the `docx` npm package (`npm install`, then `node build.js out.docx`).
- `acme/clean.py` and `acme/split.py`: the main pass that converted the Common Paper agreement into ACME's SaaS Agreement by editing the unpacked document XML. A few later edits (header band, footer, Section 8.4) were made by hand, so these scripts do not reproduce the final file on their own.
