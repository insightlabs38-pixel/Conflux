# Repository Structure — Created Only After Kickoff

```text
conflux/
├── .dogfood.toml
├── acceptance-report.txt
├── docker-compose.yml
├── README.md
├── ARCHITECTURE.md
├── DATA-MODEL.md
├── JUDGING.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── Makefile
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
├── src/
│   ├── api/
│   │   ├── config/
│   │   ├── core/
│   │   ├── accounts/
│   │   ├── workspaces/
│   │   ├── events/
│   │   ├── participation/
│   │   ├── stages/
│   │   ├── policies/
│   │   ├── forms/
│   │   ├── artifacts/
│   │   ├── projects/
│   │   ├── evaluations/
│   │   ├── awards/
│   │   ├── presentation/
│   │   ├── community/
│   │   ├── communications/
│   │   ├── integrations/
│   │   ├── audit/
│   │   └── jobs/
│   ├── web/
│   │   ├── app/
│   │   ├── features/
│   │   ├── public/
│   │   ├── components/
│   │   ├── blocks/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── styles/
│   ├── embed/
│   └── packages/
├── tests/
│   ├── acceptance/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   ├── properties/
│   └── compatibility/
├── loadtests/
├── fixtures/
├── examples/
├── scripts/
├── docs/
└── .github/workflows/
```

The final naming may be adjusted by BOOT-B00, but the required root filenames and `src/`/`tests/` contract are fixed.
