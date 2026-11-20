# gh644 #1094: supervisor loads codebase-design and tdd

Run: `scripts/octo-feather-qa --suite skill-triggers --runs 3 --baseline main`, 8 supervisor cases.

| case | main | branch |
|---|---|---|
| sup-design-port-test | 0/3 (not offered) | 3/3 |
| sup-design-port-test-ho | 0/3 (not offered) | 3/3 |
| sup-tdd-port-test | 0/3 (not offered) | 3/3 |
| sup-tdd-port-test-ho | 0/3 (not offered) | 3/3 |
| sup-design-near-rename | 3/3 | 3/3 |
| sup-design-near-ho | 3/3 | 3/3 |
| sup-tdd-near-docs | 3/3 | 3/3 |
| sup-tdd-near-ho | 3/3 | 3/3 |

Demo: `scripts/octo-feather-qa --suite skill-triggers --case sup-design-port-test --case sup-tdd-port-test`: 2/2 passed.
