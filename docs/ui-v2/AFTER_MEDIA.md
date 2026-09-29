# UIV2-B10 AFTER media inventory

Re-recorded by the existing scene/lifecycle harness (`tests/e2e/scenes.spec.ts`, `lifecycle.spec.ts`) after
`scripts/demo-reset`, against the rebuilt app image, in `make e2e-fast`. Scene identities and names match
[BASELINE_MEDIA.md](BASELINE_MEDIA.md) one to one; stills live in `docs/verification/UIV2-B10/scenes`.
Video clips are produced by the same harness (lifecycle/scenes record on demand) and stay in ignored
`artifacts/e2e-fast/*/results`; they are not committed.

| Scene still                         | Dimensions | SHA-256                                                            |
| ----------------------------------- | ---------- | ------------------------------------------------------------------ |
| 01-landing.png                      | 1280×2528  | `3c89c4755a74c7ac11b6238f0bf5c8a57ffc3f48d1a54c3f080c6aed572a81b8` |
| 02-gallery.png                      | 1280×3145  | `4006490de97a6688d34d994e58b5456fbee0b1b0b2cfdca4298603069aa08ac9` |
| 03-results.png                      | 1280×930   | `91f754eae5616f5828abde4686c9b0256c7135b431081e7a1cf86804723a783d` |
| 04-organizer-selector.png           | 1280×800   | `bf88f0521770c2d5351cab0e65969363551b40ed7a79b8815de0c70a12512e6b` |
| 04-organizer-workspace.png          | 1280×800   | `c7349775cb13cc83c9dea55146abd8271a405e2ef0df05fd783523e5e6cde143` |
| 05-judge-selector.png               | 1280×800   | `26223ff30fad9fd16e53e69bf5547a5a264458b0aa2e4959a9effc4bfb6577da` |
| 05-judge-workspace.png              | 1280×800   | `fbf435bbaf99b8b0ef48011aee4f9fd48a42d4b4110306f2fadb7a44e92c6074` |
| 06-participant-selector.png         | 1280×800   | `6c8b2983b6705b3c4c5fba82277c91f0ce936bae22e1a71455035e9673e68ee0` |
| 06-participant-workspace.png        | 1280×800   | `810cc4534ef5a0ae58aeffb7a024c6344861e83213aeacb41bfa0b965e95f89b` |
| 07-agenda.png                       | 1280×865   | `ced3b19aa0100d4cc590887483abd0707fa703e69781fe976203a250480b4e68` |
| 08-expo-map.png                     | 1280×800   | `958c88388a36857a1504c5141eee5a0bbb7529cc18d102665696c1d6c70cb4cb` |
| 09-api-explorer.png                 | 1280×1264  | `f89dc5bf79f7428e8666cd0bbbf458f5e8b6b7e2d3082065d92c7e43619ef0c3` |
| 10-signin.png                       | 1280×800   | `0553f25555479707a81f758e325342f4222475d1745eef5b3a47cf161bc6f314` |
| judge-artifact-inspector.png        | 340×735    | `69f1ee5cb70900482691f9d2ff60159f48ad6306a5acc738428a67b6f8ec01e4` |
| judge-route.png                     | 976×514    | `f9aa12dca109fb4c1c7657fd2a84924ba621afe567e87852e24278434484e06a` |
| judge-scoring.png                   | 1280×800   | `9f185980f8f8aab534e898a270f6c3a3ea76a48d4ca57745b964ca2e29300e86` |
| organizer-deliberation-overview.png | 711×127    | `4ed32e6b0a7ee19642aaedf8d17e51aca06587289b7566059047408797be8d0f` |
| organizer-deliberation.png          | 711×1189   | `b9c82dd6640fc2d5ee17a3cbf46fe232eb3e4960f86b60964f874f8ffa6e426a` |
| organizer-eligibility-overview.png  | 711×451    | `c115142b8805c3cc68fbaee7d1b92fc496460654cfcf6d5d536ad13bf6ab53a4` |
| organizer-eligibility.png           | 711×1168   | `9dc9be1e03ae79ae59b69133a02c5810b360fec587771f7032896c3ce7945ac1` |
| organizer-judging-logistics.png     | 711×1203   | `4452595b9eaeb61d68fd7dfac0d2729f0e9bf8ad91c406125a6e6b928c971ea9` |
| organizer-onsite.png                | 976×1596   | `9119ee6c8f428e5c36523a578c0bdb910af4213d2db53f4051b1aaffa462d3ce` |
| participant-remediation.png         | 711×384    | `95e92bb4886319322e380ba5bb824f5d94949f23ab70d589d9bf0a527ad7940b` |
| participant-submission-receipt.png  | 711×1291   | `be1de454d41e554859378c339212eb54d030c90cb8f47d3e699fc3a4b873d0e3` |
| public-project.png                  | 1280×1098  | `1da9f39957b1f62eb02dc95d26409908fa35c81e97885cec0331b62d8f452947` |
