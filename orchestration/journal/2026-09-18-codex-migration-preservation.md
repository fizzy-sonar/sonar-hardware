# Migration preservation — 2026-09-18

Joshua requested committing and pushing sonar-hardware before a clean laptop migration. T-028 tracks this administrative task.

The existing KiCad project edit only reorders used_designators; parsed JSON comparison confirmed no other semantic difference. Preserved in 1262ee4. git diff --check passed; scripts/check.sh exited 0, accepting existing baseline ERC/DRC violations. No new hardware or engineering signoff.

All ordinary local branches are ancestors of main. The configured public remote is fizzy-sonar/sonar-hardware. Automatic approval review rejected the upload of 124 prior local commits plus migration commits pending explicit approval to publish that history publicly. No push occurred. User was asked; next step is normal push and exact remote hash verification after approval. Ignored files, nested CAD history repositories and external backup remain outside this Git push.

## Public push approved and verified

Joshua explicitly approved the full-history public upload. Normal main push succeeded; live GitHub main matched e671a124582e7329e7c4d42b4d82b51b998509bb. T-028 is complete. This follow-up records closure and will also be pushed and verified. Ignored files and nested CAD history still require separate backup.
