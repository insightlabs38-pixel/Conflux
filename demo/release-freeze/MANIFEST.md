# Release rehearsal data freeze

This PostgreSQL and object-store snapshot was taken on 2026-09-27 from the disposable offline release stack after the lifecycle rehearsal. It contains the official synthetic fixture, seeded acceptance identities, and rehearsal events. Use it only in a disposable stack: `scripts/restore demo/release-freeze` replaces that stack's database and object-store state.

Rehearsed event: `f73490c0-f2d8-40bd-b058-d0a883fa9243`  
Finalized project: `a68c4383-3153-4e24-b7b5-728bd1638b60`  
Submission receipt: `0620900e-c56e-4259-b550-7549064e94e3`  
Judge ballot: `d90102ce-9591-4eac-a561-7a07401e0b92`  
Published award: `7e951ed4-65ed-4371-b98f-c39a38106704`

SHA-256:

```text
a711b9fb8650b4373c371f6651de28af934cd5fb4a3b2c44ff8d2ef4be516438  db.dump
e9a642e2f061d0e47327dad961e70387fb4d50ae3a4958d0fb3e7c513c04abf2  objectstore.tar.gz
```

`scripts/rehearse-demo.py` repeats the API path on a seeded test stack and prints fresh IDs. It writes new records, so use the frozen snapshot for the stable demo.
