# Fast review site

Publication status (2026-09-06): registered, **not deployed**. The external Git
upload was denied by permission review because Joshua had not explicitly
authorized this payload/destination. No source upload, saved version or
deployment succeeded. Do not retry or use a different upload path without
explicit authorization. The local review is the completed deliverable.

The source remains the existing Python/static-HTML review architecture:
`scripts/gen_fast_review.py`, `../fast-review.html`, and the two
SVG assets. Do not scaffold a replacement app or publish the parent repository.

Build local and curated portable output:

```sh
python3 scripts/gen_fast_review.py --portable build/sonar-fast-site/dist
python3 scripts/check_fast_review.py
python3 scripts/check_fast_review.py build/sonar-fast-site/dist/index.html
```

The persistent `.openai/hosting.json` here identifies the existing owner-only
Site. The generator copies it into the isolated, ignored build checkout. Reuse
that project ID; never create another Site to refresh the review. Obtain a new
source credential when needed. Only the Site-owning agent publishes.

`build/sonar-fast-site/` is an isolated Git source checkout for publishing, not
the Sonar repository. It contains only the static output and hosting metadata.
Its static HTML/SVG and escaped source excerpts are the exact source
served by the Site, with no server/build dependency. No secrets, KiCad project,
private user notes or whole-repository archive belong in it.

The full engineering appendix is deliberately local. Source excerpts in the
hosted copy are inert text; paths within them refer to the local repository.
The web page is a dated snapshot, not live repository status. Refresh tests and
SHA256SUMS deliberately when design files change; never merely bless new hashes.

Joshua explicitly does not want to copy anything. The page is read-only, with
one immediate question and no forms, notes, JavaScript or export workflow.
All answers stay in the existing conversation. The old appendix's localStorage
is untouched. Browser visual QA was not requested; structural/link and stale
evidence tests are provided.
