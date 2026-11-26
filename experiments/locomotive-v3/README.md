# Locomotive V3 — owner-accepted visual benchmark
Owner accepted the V3 visual sample on 2026-11-24 and requested permanent preservation of key files and documentation. This is an art benchmark for offline sprite creation, not a Factorio release. Original generator and verifier were copied verbatim; Git blob SHAs respectively 57f56748afda910f5a9c4917abc5e28a5d0b42ee and 9e11ba51b791f7dd844e4cf84f0fdf6c48022e9d. Baseline JSON files are exact copies of locally measured results. See ../../docs/QA_LOCOMOTIVE_CONCEPT_MODEL.md.

## Rebuild in an isolated copy
Use Python 3.13.5 and requirements.txt (versions from the local environment). On Linux provide Mesa/OpenGL and a virtual display if required. From this directory:
```sh
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=2 python loco_v3/build.py
python verify_rebuild.py
sha256sum -c accepted-assets.sha256
```
The historical verify.py contains a final V2/reference comparison step requiring prior V2 renders, source concept and DejaVu Sans. verify_rebuild.py runs its original geometry/roof checks without that optional comparison and additionally asserts baseline topology and texture. Generated qa.json is separate from the immutable baseline. The generator outputs three GLBs, the 4K livery texture and five renders. Never overwrite the original accepted files with a non-identical rebuild.

## Preservation status
Exact local GLBs and full archive remain in the conversation unless an exact hash-matching copy is committed under assets/. The source environment cannot reach github.com by Git (DNS failure); the connector accepts text, not a local binary path. The original archive Locomotive_v3_source_QA.zip SHA256 is 308325514d9f330f871b7e1d7ca11b29c0dfa8b6058730109a68918e564764d3. No original concept or V2 comparison binaries copied here. No byte-identity claim for a remote rebuild until its actual hashes are checked.
