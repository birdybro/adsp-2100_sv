# Reference provenance and local cache

`manifest.yaml` is JSON-compatible YAML so validation requires only Python's
standard library. Each record states exact-device applicability, authority,
redistribution status, confidence, and whether a local copy may be committed.

The words have deliberately narrow meanings:

- `acquired`: the configured local file was fetched, validated, and its SHA-256
  is recorded;
- `identified`: a source or target is known, but no checksum-verified local
  artifact has been acquired;
- `unavailable`: attempted access failed or is not lawful/possible;
- `superseded`: retained for provenance but replaced by a better revision.

`authority_level` ranks the nature of the source; it does not assert that every
statement in a family manual applies to the original device. Applicability
still has to be established at the cited page or section.

## Safe workflow

```sh
python3 scripts/fetch_references.py --update-manifest
python3 scripts/verify_reference_hashes.py
python3 scripts/report_missing_references.py
python3 scripts/fetch_mame_source.py
```

The fetcher:

- only processes records with `download.enabled`;
- limits response size and requires HTTP 200;
- checks declared content types;
- rejects HTML masquerading as PDF;
- uses a temporary file and verifies SHA-256 before replacement;
- never executes downloads;
- skips already valid files unless `--refresh` is given.

All downloads are written beneath gitignored `reference_cache/`. A hash update
only fills a previously empty digest; it never normalizes an unexpected new
digest into the manifest.

`fetch_mame_source.py` creates a sparse, detached checkout containing the
ADSP-21xx CPU and Hard Drivin' machine sources at commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`. It verifies an existing checkout
instead of advancing it. The checkout is a license-preserving differential
reference and is never imported into project-authored model or RTL.

## Cross-software applicability boundary

The cached `ADI-2101-CROSS-1990` record is a 1989 First Edition ADSP-2101
programming reference despite the archive filename's 1990 label. Its System
Builder section explicitly says that `.ADSP2101` distinguishes a 2101 system
and that omission selects ADSP-2100. This is useful contemporary evidence for
toolchain discovery, but its ADSP-2101 instruction chapter and opcode appendix
do not establish original-device legality. The exact original ADSP-2100
Cross-Software manual remains an open acquisition target.

The exact-device `ADI-2100-EMULATOR-TARGET` is also unavailable. Contemporary
ADI literature identifies the manual, but neither the official legacy index
nor the searched archival directory exposes a lawful copy. Its possible pin
trace or external-instrumentation material is an evidence target for OQ-023
and OQ-024, not evidence by title alone.

## Original 2100/2100A boundary

`ADI-DATABOOK-1989` is a hash-pinned, gitignored scan of an original ADI
databook containing the joint ADSP-2100/ADSP-2100A data sheet. Printed p. 2-19
explicitly establishes pin/code compatibility and identical documented
architectures and instruction sets, while distinguishing speed grades and
electrical/timing specifications. It does not close undocumented mask fixes,
errata, or power-up signatures.

## Citing sources

Architecture documents cite a reference ID plus publication/revision and the
manual's printed page/section/table/figure. PDF page numbers are added only as
navigation aids because scans often have front-matter offsets. MAME citations
use the pinned commit, path, and line range. Atari schematics use drawing
number, revision, and sheet.

Do not reproduce extended manual prose. Add concise technical paraphrases and
precise locations.
