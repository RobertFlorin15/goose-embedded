# Pinned Goose compiler adaptation

`0001-scalar-v0-validator.patch` applies only to Goose commit
335fddc13dc74666398ffe160ec8a8f2958329d0. It adds an opt-in source/type validator
and codegen invariants. **It does not adapt runtime startup or make MCU firmware.**
`manifest.json` records the patch digest and expected modified/new file digests.

Prepare a new disposable source tree with tools/prepare_scalar_compiler.py;
never patch the clean .cache/goose reference in place. The helper refuses an
existing destination, modified/wrong-pin upstream, or mismatched patch/manifest;
extracts git archive; applies the patch with Git discovery stopped at the parent
of the destination; and verifies resulting file hashes. Patch additions are checked with
`git apply --check --whitespace=error`; .gitattributes exempts the literal diff
file from whitespace checks on its required context-line prefixes. It writes provenance
metadata only after verification. No downloads/builds occur in this helper.
Failure can leave the new destination incomplete; choose a new disposable path
for a corrected attempt instead of reusing it without inspection.

Maintainers changing this patch should apply it to a disposable checkout at the
pin, edit/rebuild/test there, regenerate the diff (including the added header),
then update manifest digests and rerun preparation/reproduction and validator
tests. Review the resulting patch; a digest is an integrity check, not a security
signature or proof of correctness. Do not hand-edit an ignored checkout and omit
the corresponding tracked patch.

Modified upstream files: src/ast.h (default-off parse policy), src/parser.h
(early directive rejection), src/main.cpp (CLI/pipeline/output integration).
Added src/scalar_profile.h holds source and checked-AST allowlists and call-cycle
validation. Modified files have Goose Embedded change notices. Runtime files,
codegen implementation, and upstream library/typechecking semantics are unchanged.

Upstream source: https://github.com/aardappel/goose at the pin above. Goose's root
license is Apache-2.0; its full unmodified text accompanies this derivative patch
as LICENSE.upstream. Existing upstream comments/context remain in the diff.
No root NOTICE file was present at this pin. Compiler third-party sources and
binaries are not vendored/distributed here. This does not select a license for
all original Goose Embedded project files or clear a future binary distribution.

## Scalar runtime patch (ABI 1)

0002-scalar-v0-runtime.patch applies after 0001. runtime-manifest.json records
its dependency on the first patch and the final seven compiler/runtime file
hashes. Preparation now selects both patches by default into
.cache/goose-scalar-runtime; --validator-only retains the historical first stage.
No existing destination or clean reference checkout is overwritten.

The new canonical src/runtime/runtime_scalar.h is embedded through upstream
--gen-runtime-header. Scalar codegen chooses that section alone and emits a
zero-region lifecycle. Checked i32 rules match the upstream widened arithmetic
rules; failures require ge_scalar_v0_panic_v1. Export symbols beginning with
ge_scalar_v0_ are reserved in profile mode. No default platform hook is supplied.

The desktop runtime sections and their hash are deliberately unchanged: the
independent scalar section is excluded from RuntimeVersion's desktop hash and
uses its own ABI marker/versioned hook. Matching desktop programs/runtime
objects therefore retain their original version contract. When editing the
canonical scalar header, regenerate runtime_inline.h with the patched compiler,
rebuild, refresh patch 0002 and its manifest, and verify generator idempotence.
