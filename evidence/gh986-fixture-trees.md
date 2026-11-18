# gh986 fixture trees: the quote-app collapse (#988)

Rule: owner ruling 2026-11-18 #986 (no spec criterion). Schema: `.agents/skills/eval-cases/references/schema.md`, Fixtures.

## Collapse

Measured (`diff -r` of the four dirs on origin/main ee42108a): quote-app-inline has no `src/app/pricing.py`, the others
do; seams-ok differs from seams-bad only in `tests/test_quote.py`. Basing the family on the member with fewest files
needs no removal, so the schema has none:

- quote-app-inline: whole tree (the shared base, 11 files, `.githooks/pre-commit` 100755).
- quote-app: base quote-app-inline; overlay AGENTS.md, pyproject.toml, src/app/cli.py, src/app/pricing.py, tests/test_cli.py.
- quote-app-seams-bad: base quote-app; overlay src/app/cli.py, src/app/pricing.py, tests/test_cli.py, tests/test_quote.py.
- quote-app-seams-ok: base quote-app-seams-bad (a chain of 3); overlay tests/test_quote.py.

28 duplicated files removed. Each materialized tree's `uv.lock` (quote-app-inline's) passes `uv sync --locked --offline`.

## Proof: --trees on main's evals and on the head diff empty

```
mkdir /tmp/gh988-main && git archive origin/main evals | tar -x -C /tmp/gh988-main   # origin/main ee42108a
scripts/check-evals --trees /tmp/gh988-main/evals > /tmp/gh988-main.trees           # exit 0
scripts/check-evals --trees > /tmp/gh988-head.trees                                   # exit 0
diff /tmp/gh988-main.trees /tmp/gh988-head.trees && echo EMPTY                        # EMPTY
scripts/check-evals                                                                   # evals: ok (11 suites, 489 cases), exit 0
```

On main every fixture is a whole dir, so its hashes are over the raw dirs (the independent baseline); on the head the
three based quote-app fixtures go through the materializer. Sensitivity: `chmod -x` on quote-app-inline's
`.githooks/pre-commit` changes all five quote-app lines (restored after).

The quote-app family's lines (both lists):

```
role-transcripts reviewer-seam-shallow-unagreed fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-shallow-unagreed head ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
role-transcripts reviewer-seam-listed-deep-clear fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-listed-deep-clear head 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
role-transcripts implementer-deepen-first fixture 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
```

## #989: every remaining fixture collapsed

Built by a scratch script (/tmp/gh986-collapse/, not committed): each fixture's materialized tree on main measured
(path, kind, bytes); each fixture's base is the fixture whose tree's paths are a subset of its own (no removal) and
leaves the fewest overlay files; since a base's paths are a subset, the choice per fixture is independent and has no
cycle. The fixture's own files equal to its base's tree were deleted and `.eval-fixture.json` written; then the
materialized trees were asserted equal to main's. Two choices by hand over the per-fixture minimum:

- docs-rules-restated on docs-rules and docs-rules-pointers on docs-rules-restated (not the reverse): 8 overlay
  files instead of 9, and no README.md held by both docs-rules and docs-rules-restated.
- python-app stays whole: `tests/lib/qa.sh` copies `evals/fixtures/python-app` raw into a scratch evals dir (not a
  fixture reader through the materializer), so it cannot name a base (see Leftovers).

CI's loop (`uv sync --locked --project <dir>` per `evals/fixtures/*/uv.lock`) builds the dir's own project, so a based
fixture whose overlay keeps a `uv.lock` (python-app-pydantic, python-app-tiers) keeps its package's
`src/app/__init__.py` (empty) too: without it hatchling refused the build (measured: `Unable to determine which files
to ship`). Every remaining `uv.lock` (6) sits beside its `pyproject.toml` and passes that loop offline; every
materialized tree with a `uv.lock` (35) passes `uv sync --locked --offline`.

Families and chains (`fixture  base  files on main  own files at head`; `-` a whole tree):

```
docs-rules-comment-restated     docs-rules-skill                10    3
docs-rules-count                docs-rules                       8    2
docs-rules-pointers             docs-rules-restated              9    3
docs-rules-prose-duty           docs-rules                       8    2
docs-rules-restated             docs-rules                       9    5
docs-rules-skill-restated       docs-rules-comment-restated     10    1
docs-rules-skill                docs-rules                       9    1
docs-rules                      -                                8    8
kit-mini                        -                               18   18
lane-mini                       py-mini                         17   12
lane-reports                    lane-mini                       21    6
py-mini                         -                                7    7
py-review-seams                 py-mini                         11    5
python-app-config-check         python-app                      12    3
python-app-exact-check          python-app                      12    2
python-app-no-verify            python-app                      11    2
python-app-noprint              python-app                      11    1
python-app-proxy-check          python-app                      12    2
python-app-pydantic-team        python-app-pydantic             11    3
python-app-pydantic             python-app                      11    6
python-app-refactor-folded      python-app-refactor             11    2
python-app-refactor-review      python-app-refactor             19    9
python-app-refactor             python-app                      11    4
python-app-semver-pre           python-app-semver               12    2
python-app-semver               python-app                      12    3
python-app-shout-cli            python-app-shout                11    2
python-app-shout-tagged         python-app-shout-cli            12    3
python-app-shout                python-app                      11    3
python-app-skill-evals          python-app-skill                17    6
python-app-skill                python-app                      13    3
python-app-spec                 python-app                      12    1
python-app-test-scan            python-app-shout-cli            12    1
python-app-tiers                py-mini                         11    8
python-app-verify-drift         python-app-verify               15    2
python-app-verify-live          python-app-verify               18    7
python-app-verify               python-app-no-verify            15    5
python-app-yaml-names           python-app                      12    3
python-app-yaml-reader-crew     python-app-yaml-names           12    2
python-app-yaml-reader-quoted   python-app-yaml-names           12    2
python-app-yaml-reader          python-app-yaml-names           12    1
python-app                      -                               11   11
quote-app-inline                -                               11   11
quote-app-seams-bad             quote-app                       13    4
quote-app-seams-ok              quote-app-seams-bad             13    1
quote-app                       quote-app-inline                12    5
rules-restated-sites            docs-rules-restated             11    7
shape-brownfield                shape-mini                      14    3
shape-mini                      py-mini                         13    7
slug-tiers                      -                               12   12
tally-tiers                     -                               13   13
ts-mini                         -                               12   12
ts-pnpm-store-shared            ts-pnpm-store                   13    3
ts-pnpm-store                   -                               12   12
weather-replay                  python-app                      12    4
```

Under evals/fixtures: main (origin/main ee42108a) 657 files, 24955 lines; head 311 files, 10501 lines (the #988
pilot's quote-app 28 files included; #989 alone: 632 files to 311).

### Leftovers: same path and bytes held by two fixture dirs' own files

12 (path, bytes) held twice or more, 23 copies over one (the list below: count, path, size, holders). None is a
fixture and its own base tree; each needs a base that is no member of the family, or a fixture with two bases:

- python-app vs py-mini (5: .gitignore, src/app/__init__.py, cli.py, core.py, tests/test_cli.py): py-mini's paths are
  a subset of python-app's, so python-app on py-mini removes them, but `tests/lib/qa.sh:170` copies python-app raw
  (a tests change: out of this ticket's scope, reported).
- the python template's files across families (.github/workflows/check.yml in 5, .gitignore in 5, mise.toml in 4,
  uv.lock 42062B in 3, .githooks/pre-commit and justfile in 2): python-app, quote-app-inline, python-app-tiers,
  slug-tiers, tally-tiers, weather-replay each lack a path another holds (core.py vs rates.py, .githooks vs
  mise.toml, src/app vs src/slugger vs src/tally), so a shared base would be a new non-case fixture holding only the
  template's files.
- src/app/__init__.py (0B) in python-app-pydantic and python-app-tiers: kept for CI's per-dir sync (above).
- docs/specs/hello.spec.html in python-app-spec and python-app-shout-tagged: shout-tagged's chain is via shout-cli;
  basing it on python-app-spec instead duplicates shout-cli's cli.py and core.py (2 for 1).
- tests/test_cli.py 682B in quote-app-inline and quote-app-seams-bad: the #988 quote-app family, not in scope.

```
own files: 266 dup (path,bytes) keys: 12 extra copies: 23
  5 .github/workflows/check.yml [254B] python-app python-app-tiers quote-app-inline slug-tiers tally-tiers
  5 .gitignore [88B] py-mini python-app quote-app-inline slug-tiers tally-tiers
  4 mise.toml [193B] python-app-tiers slug-tiers tally-tiers weather-replay
  4 src/app/__init__.py [0B] py-mini python-app python-app-pydantic python-app-tiers
  3 uv.lock [42062B] python-app python-app-tiers quote-app-inline
  2 .githooks/pre-commit [83B] python-app quote-app-inline
  2 docs/specs/hello.spec.html [746B] python-app-shout-tagged python-app-spec
  2 justfile [900B] python-app quote-app-inline
  2 src/app/cli.py [881B] py-mini python-app
  2 src/app/core.py [308B] py-mini python-app
  2 tests/test_cli.py [950B] py-mini python-app
  2 tests/test_cli.py [682B] quote-app-inline quote-app-seams-bad
```

### Proof: --trees on main's evals and on the head diff empty

```
mkdir /tmp/gh989-main && git archive origin/main evals | tar -x -C /tmp/gh989-main   # origin/main ee42108a
scripts/check-evals --trees /tmp/gh989-main/evals > /tmp/gh989-main.trees           # exit 0, 372 lines
scripts/check-evals --trees > /tmp/gh989-head.trees                                   # exit 0, 372 lines
diff /tmp/gh989-main.trees /tmp/gh989-head.trees && echo EMPTY                        # EMPTY
sha256sum /tmp/gh989-*.trees                                                          # both fce30d4c933c06ac...6b33
scripts/check-evals                                                                   # evals: ok (11 suites, 489 cases), exit 0
```

Both lists are the Main list and Head list below, byte for byte (the pilot's head list equals them too). Every
fixture dir's tree, a case's or not, through the same materializer on main's archive and on the head, also diffed
empty (54 dirs):

```
docs-rules 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
docs-rules-comment-restated 4a67f75baab2ef5ea72e0b57937eff3923639efa1cb33e3ed914ea5c74ab2a75
docs-rules-count 9ecd9fd27bf99038e05fc3916a4b8185fc622b9dde2f20a71bd8e0ddd1212a91
docs-rules-pointers 6884c8ac3f304107430e6d2add72a1e3e2bae399e212e123a1a1eaf4860aa547
docs-rules-prose-duty 0a7feb3ac3a8360031c55168574800c4275f81c9ec21ef551adbea2bda75511b
docs-rules-restated 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
docs-rules-skill 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
docs-rules-skill-restated 4f8fbeda194627c5bab45e040a2285d9a1e735c75c27ce6712042f47c76c22c0
kit-mini 5bda838e3669ab5e05bc720542119d40286e8c1422a8a94d5ce9c976234b3c42
lane-mini a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
lane-reports 85060cfd3157b5b83397d9140e543d3093446f90d1eacd222b019b32cd3349f8
py-mini e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
py-review-seams 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
python-app 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
python-app-config-check e67fee2b9f987a20ccaca236688964b1147d6baae35630c4f8596ee97c7aeb1a
python-app-exact-check d21c3b72099041ed423ea2e548ce0c665beeb07ca25553ceb648dd8c985248fc
python-app-no-verify 25b4d7f6676efb12db4b6d0ab40fa038b6c16db6997b2aa4e2356bfd4a04bfc9
python-app-noprint 4c7bd10e296030efe032e0b7592ec12f29beafdedc059a3925c3f39ce95c05c3
python-app-proxy-check ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
python-app-pydantic 053627210c5d50575fdc8eb3138918b33e8743785b0fb6f941db6de52f5bc18d
python-app-pydantic-team 3290d892df908d433df9a9b4d4c4be6951aea424fd79df4e2d63465f40fc4b85
python-app-refactor dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
python-app-refactor-folded 89821450529972a5b4640e77b674f9b1f34e53b152032132b1c4f05f3e28048f
python-app-refactor-review f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
python-app-semver 1c2f107180c2b36137c097f4b2bba41219108163183f14e7074f49d1b5c81455
python-app-semver-pre cc613b68ec97f5ec77c94a493ae89f4a6c1eeb03acf5c9edec8ba09e19e38721
python-app-shout b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
python-app-shout-cli cec75972860bf251fdc5c425cf5eac3428aefa37341b29066474ca1d86fd2fec
python-app-shout-tagged ff0d7e546cfda4db14902a3142404614ccfd2c0bdfecbc8e35d8524856a92cd2
python-app-skill 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
python-app-skill-evals 529f5a1a5f3878355b4afab170ac5f7027657891f5822c5f4ee8da5ee476b3a6
python-app-spec e55b7a0db2269bd4e18b955943065a6576690f342025e2e708c045532e656657
python-app-test-scan b3da95bddba3345dcbefee5e37b6433bf35d0cee52b99e95455611bfe9492cb2
python-app-tiers d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
python-app-verify ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
python-app-verify-drift 98760158690733a058258eabee0cbe8353f5fc8a4fbb95ae6c3c01575310496b
python-app-verify-live b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
python-app-yaml-names db3ddd04f2745c5f0b419a6e1672e86fabcbc7c65c1d377c501378d42a6ec64f
python-app-yaml-reader cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
python-app-yaml-reader-crew ca2e1f06f2664353a5d3a8abb86ad91eb04a90cfe145387613ab6109068bc888
python-app-yaml-reader-quoted 6c942d9599f0b8afef8b9a9e913f82c866d22b9bbcf0d0b93de16c1999513f99
quote-app 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
quote-app-inline 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
quote-app-seams-bad ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
quote-app-seams-ok 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
rules-restated-sites 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
shape-brownfield 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shape-mini 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
slug-tiers 8fdd2ad8d67c63138c417e64b98705c04a3573ccd2928188b871a4aa9ec93dbf
tally-tiers d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
ts-mini 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
ts-pnpm-store 4e84f7841dbd713ba0a2ed79312ba2e57bc26fcd4ef1cb50ec840c104ad9557b
ts-pnpm-store-shared befe08107fe9a4c76f8fe9849c08c072c9b624a8af254bb8814beebbc3f7cc66
weather-replay 1d9dc73deb7a60ad337ed8e9addfafc36bfe9b8dfdec3f3683acec0ea433cabc
```

Sensitivity: `chmod -x evals/fixtures/python-app/.githooks/pre-commit` changes 83 lines of the head list (every case on
python-app or a fixture based on it); restored, the list is main's again.

## Main list (origin/main ee42108a evals)

```
history implementer-ts-toml-at-scale fixture history kit@0f4f1bad2c7caf593a6a2e7c1e18c9f1617238f1
isolation reach-live-state fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
isolation reach-other-repos fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
ladder corrector-fuzzy-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-fact-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-coupling-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-secret-grep fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-exec-bit fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-test-vs-check fixture 4c7bd10e296030efe032e0b7592ec12f29beafdedc059a3925c3f39ce95c05c3
ladder reviewer-proxy-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-check head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder reviewer-exact-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-exact-check head d21c3b72099041ed423ea2e548ce0c665beeb07ca25553ceb648dd8c985248fc
ladder reviewer-product-command-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-product-command-check head e67fee2b9f987a20ccaca236688964b1147d6baae35630c4f8596ee97c7aeb1a
ladder reviewer-no-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-no-check head cec75972860bf251fdc5c425cf5eac3428aefa37341b29066474ca1d86fd2fec
ladder reviewer-test-is-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-test-is-check head b3da95bddba3345dcbefee5e37b6433bf35d0cee52b99e95455611bfe9492cb2
ladder reviewer-owner-lines fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-lines head 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
ladder reviewer-owner-pointers fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-pointers head 6884c8ac3f304107430e6d2add72a1e3e2bae399e212e123a1a1eaf4860aa547
ladder reviewer-owner-none fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-none head 9ecd9fd27bf99038e05fc3916a4b8185fc622b9dde2f20a71bd8e0ddd1212a91
ladder reviewer-comment-restatement-note fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-comment-restatement-note head 4a67f75baab2ef5ea72e0b57937eff3923639efa1cb33e3ed914ea5c74ab2a75
ladder reviewer-skill-restatement-blocks fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-skill-restatement-blocks head 4f8fbeda194627c5bab45e040a2285d9a1e735c75c27ce6712042f47c76c22c0
ladder corrector-template-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-kit-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder implementer-owned-rule fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts implementer-python-ticket fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts implementer-skill-ticket fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts implementer-verify-pass fixture 98760158690733a058258eabee0cbe8353f5fc8a4fbb95ae6c3c01575310496b
role-transcripts implementer-verify-create fixture 25b4d7f6676efb12db4b6d0ab40fa038b6c16db6997b2aa4e2356bfd4a04bfc9
role-transcripts implementer-verify-kit fixture 5bda838e3669ab5e05bc720542119d40286e8c1422a8a94d5ce9c976234b3c42
role-transcripts corrector-repeated-class fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts corrector-repo-skill-rule fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts reviewer-test-quality fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-test-quality head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts reviewer-criterion-test-adequacy fixture e55b7a0db2269bd4e18b955943065a6576690f342025e2e708c045532e656657
role-transcripts reviewer-criterion-test-adequacy head ff0d7e546cfda4db14902a3142404614ccfd2c0bdfecbc8e35d8524856a92cd2
role-transcripts qc-judge-demo-path fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts qc-judge-no-reviewer-skills fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts director-file-parent fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts corrector-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts qc-judge-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts implementer-verify-map-current fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts corrector-evidence-field fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts reviewer-reinvented-parser fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-reinvented-parser head db3ddd04f2745c5f0b419a6e1672e86fabcbc7c65c1d377c501378d42a6ec64f
role-transcripts reviewer-prose-duty-blocks fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts reviewer-prose-duty-blocks head 0a7feb3ac3a8360031c55168574800c4275f81c9ec21ef551adbea2bda75511b
role-transcripts implementer-library-web fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts director-merge-report-post-merge fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts shaper-code-ask-shapes-spec fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts dir-spawns-shaper fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts shaper-library-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-wording-proof fixture 529f5a1a5f3878355b4afab170ac5f7027657891f5822c5f4ee8da5ee476b3a6
role-transcripts shaper-table-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-hands-off-on-fast fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
role-transcripts implementer-hands-off-on-fast-heldout fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
role-transcripts implementer-hands-off-on-fast-heldout-2 fixture 8fdd2ad8d67c63138c417e64b98705c04a3573ccd2928188b871a4aa9ec93dbf
role-transcripts implementer-missing-recording-heldout fixture 1d9dc73deb7a60ad337ed8e9addfafc36bfe9b8dfdec3f3683acec0ea433cabc
role-transcripts prior-art-extends fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends head 6c942d9599f0b8afef8b9a9e913f82c866d22b9bbcf0d0b93de16c1999513f99
role-transcripts prior-art-extends-stated fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends-stated head ca2e1f06f2664353a5d3a8abb86ad91eb04a90cfe145387613ab6109068bc888
role-transcripts prior-art-extends-held-out fixture 1c2f107180c2b36137c097f4b2bba41219108163183f14e7074f49d1b5c81455
role-transcripts prior-art-extends-held-out head cc613b68ec97f5ec77c94a493ae89f4a6c1eeb03acf5c9edec8ba09e19e38721
role-transcripts reviewer-unvalidated-edge-ts fixture 4e84f7841dbd713ba0a2ed79312ba2e57bc26fcd4ef1cb50ec840c104ad9557b
role-transcripts reviewer-unvalidated-edge-ts head befe08107fe9a4c76f8fe9849c08c072c9b624a8af254bb8814beebbc3f7cc66
role-transcripts reviewer-unvalidated-edge-py fixture 053627210c5d50575fdc8eb3138918b33e8743785b0fb6f941db6de52f5bc18d
role-transcripts reviewer-unvalidated-edge-py head 3290d892df908d433df9a9b4d4c4be6951aea424fd79df4e2d63465f40fc4b85
role-transcripts implementer-refactor-ticket fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts supervisor-refactor-lane fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff head 89821450529972a5b4640e77b674f9b1f34e53b152032132b1c4f05f3e28048f
role-transcripts reviewer-seam-shallow-unagreed fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-shallow-unagreed head ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
role-transcripts reviewer-seam-listed-deep-clear fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-listed-deep-clear head 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
role-transcripts implementer-deepen-first fixture 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
shaper-repair repair-moment-bye fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-verbose fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-emoji fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-inner-space fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-from fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-owner fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-formal fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-adr fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-typo fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers impl-prove-json-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-empty-name-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-read-only fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-test-command fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-lowercase-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-rename-json-key fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-list-callers fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-explain-term fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers blast-radius-keep-whitespace fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-editorconfig fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-changelog fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-show-last fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-leave-uncommitted fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-file-issue fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-pr-status fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-local-branches fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-draft-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-open-draft fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-near-commit-msg fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-ticket-scope fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-near-todo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-shout-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-two-tickets fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-already-done fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-estimate fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-port-env fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-env-file fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-near-python-env fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-near-readme-typo fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-add-zod fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-lock-sync fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-near-python-dep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pnpm-near-test-script fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pull-origin-main fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-upstream-moved fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-log fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-new-branch fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-name-length fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-ruff-config fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-agents-typo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers tdd-shout-flag fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-tab-in-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-run-suite fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-miss-count-tests fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-precise-type fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-near-python-hints fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-near-node-version fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-evalcases-skill-sections fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-new-repo-skill fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-evalcases-near-read-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-near-use-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers sup-commit-pr-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-last-touch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-pr-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-close-issue fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-status-file fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-draft-comment fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-merge-head fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-diff-stat fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-pr-number fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghissues-file-ticket fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-tell-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-spawn-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-read-handoffs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-lane-field fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-build-criterion fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-docstring-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-lane-record fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-draft-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-refresh-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-ahead-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-local-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-break-spec fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-slice-criteria fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-mark-done fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-poke-idle fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-relay-merge fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-lane-wait fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-count-findings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-file-parent fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-main-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-built fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-owner-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-review-state fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-near-handoff-time fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-parent-children fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-near-tickets-md fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-remove-scratch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-agents-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-show-last fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-owner-twice fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-repeat-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-one-bug fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-repeated-instruction fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-prose-ignored fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-quote-rule fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-add-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-tighten-agents fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-new-skill fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-headings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-code-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-classes fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-review-comments fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-verdict-checks fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers corrector-eval-cases-should fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-should-heldout fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-pytest fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-field-or-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-review-shout-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-times-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-count-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-fetch-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-pr-threads fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-local-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-class-tag fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-plain fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-json fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-list-ids fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-app-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-tdd-shout-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-would-catch fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-count-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-run-suite fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers impl-createverify-no-harness fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-run-once fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-list-skills fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-audit fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-drift fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-define fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-json fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers dir-lever-status-by-hand fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-steps fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-test-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-lane-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-finding-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-handoff-stamp fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-goal-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-call-sites fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-rename fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-which-function fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-add-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-again fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-event-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-one-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-verify-sha fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-record-merge-ask fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-set-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-finding-logged fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-prior-art-again fixture 85060cfd3157b5b83397d9140e543d3093446f90d1eacd222b019b32cd3349f8
skill-triggers cor-lever-restated-sites fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-restated-comments fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-near-one-pointer fixture 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
skill-triggers cor-lever-near-owner fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers dir-encode-route-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-waiting-reminders fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-first-handoff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-planned fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-brief-demo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-free-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-last-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-blocked fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-encode-release-duty fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-forgotten-tests fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-near-imports fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-encode-near-entry fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-browser-rendered-banner fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-screenshot fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-selector fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-html-grep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-reproduce-render fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-visible-paragraphs fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-headless fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-readme-link fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers reflector-reflect-lane-gh5 fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-lane-held fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-quote fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers shaper-sharpen-languages fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-shout-code fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-history fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-farewell fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-correction fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-rate-limit fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-config fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-anchor fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-guest fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-team fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-define fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-glossary-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-clock-seam fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-greeter-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-wording fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-error-text fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-tangled fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-review fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-new-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-flag fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers impl-design-seam fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-phrasebook fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-bugfix fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-rename fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-design-seam fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-phrasebook fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-bugfix fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-rename fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers impl-kit-ts-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers shaper-repair-multi-name fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-lang fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-clean-repo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-clean-version fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-question-exit fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-question-json fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers gw-herdr-send-test-list fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-director-ticket-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-which-pane fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-json-greeting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-measure-dirs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-gate-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-diff-files fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-refactor-fold-goodbye fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-split-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-cut-fold fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-brief-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-refactor-fold fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-name-check fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-wave fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-inner-space fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers sup-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-principles-one-result fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-one-printer fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-retire fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-shout fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
```

## Head list (the #988 head and the #989 head: the same bytes)

```
history implementer-ts-toml-at-scale fixture history kit@0f4f1bad2c7caf593a6a2e7c1e18c9f1617238f1
isolation reach-live-state fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
isolation reach-other-repos fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
ladder corrector-fuzzy-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-fact-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-coupling-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-secret-grep fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-exec-bit fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-test-vs-check fixture 4c7bd10e296030efe032e0b7592ec12f29beafdedc059a3925c3f39ce95c05c3
ladder reviewer-proxy-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-check head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder reviewer-exact-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-exact-check head d21c3b72099041ed423ea2e548ce0c665beeb07ca25553ceb648dd8c985248fc
ladder reviewer-product-command-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-product-command-check head e67fee2b9f987a20ccaca236688964b1147d6baae35630c4f8596ee97c7aeb1a
ladder reviewer-no-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-no-check head cec75972860bf251fdc5c425cf5eac3428aefa37341b29066474ca1d86fd2fec
ladder reviewer-test-is-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-test-is-check head b3da95bddba3345dcbefee5e37b6433bf35d0cee52b99e95455611bfe9492cb2
ladder reviewer-owner-lines fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-lines head 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
ladder reviewer-owner-pointers fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-pointers head 6884c8ac3f304107430e6d2add72a1e3e2bae399e212e123a1a1eaf4860aa547
ladder reviewer-owner-none fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-none head 9ecd9fd27bf99038e05fc3916a4b8185fc622b9dde2f20a71bd8e0ddd1212a91
ladder reviewer-comment-restatement-note fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-comment-restatement-note head 4a67f75baab2ef5ea72e0b57937eff3923639efa1cb33e3ed914ea5c74ab2a75
ladder reviewer-skill-restatement-blocks fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-skill-restatement-blocks head 4f8fbeda194627c5bab45e040a2285d9a1e735c75c27ce6712042f47c76c22c0
ladder corrector-template-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-kit-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder implementer-owned-rule fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts implementer-python-ticket fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts implementer-skill-ticket fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts implementer-verify-pass fixture 98760158690733a058258eabee0cbe8353f5fc8a4fbb95ae6c3c01575310496b
role-transcripts implementer-verify-create fixture 25b4d7f6676efb12db4b6d0ab40fa038b6c16db6997b2aa4e2356bfd4a04bfc9
role-transcripts implementer-verify-kit fixture 5bda838e3669ab5e05bc720542119d40286e8c1422a8a94d5ce9c976234b3c42
role-transcripts corrector-repeated-class fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts corrector-repo-skill-rule fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts reviewer-test-quality fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-test-quality head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts reviewer-criterion-test-adequacy fixture e55b7a0db2269bd4e18b955943065a6576690f342025e2e708c045532e656657
role-transcripts reviewer-criterion-test-adequacy head ff0d7e546cfda4db14902a3142404614ccfd2c0bdfecbc8e35d8524856a92cd2
role-transcripts qc-judge-demo-path fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts qc-judge-no-reviewer-skills fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts director-file-parent fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts corrector-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts qc-judge-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts implementer-verify-map-current fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts corrector-evidence-field fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts reviewer-reinvented-parser fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-reinvented-parser head db3ddd04f2745c5f0b419a6e1672e86fabcbc7c65c1d377c501378d42a6ec64f
role-transcripts reviewer-prose-duty-blocks fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts reviewer-prose-duty-blocks head 0a7feb3ac3a8360031c55168574800c4275f81c9ec21ef551adbea2bda75511b
role-transcripts implementer-library-web fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts director-merge-report-post-merge fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts shaper-code-ask-shapes-spec fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts dir-spawns-shaper fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts shaper-library-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-wording-proof fixture 529f5a1a5f3878355b4afab170ac5f7027657891f5822c5f4ee8da5ee476b3a6
role-transcripts shaper-table-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-hands-off-on-fast fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
role-transcripts implementer-hands-off-on-fast-heldout fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
role-transcripts implementer-hands-off-on-fast-heldout-2 fixture 8fdd2ad8d67c63138c417e64b98705c04a3573ccd2928188b871a4aa9ec93dbf
role-transcripts implementer-missing-recording-heldout fixture 1d9dc73deb7a60ad337ed8e9addfafc36bfe9b8dfdec3f3683acec0ea433cabc
role-transcripts prior-art-extends fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends head 6c942d9599f0b8afef8b9a9e913f82c866d22b9bbcf0d0b93de16c1999513f99
role-transcripts prior-art-extends-stated fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends-stated head ca2e1f06f2664353a5d3a8abb86ad91eb04a90cfe145387613ab6109068bc888
role-transcripts prior-art-extends-held-out fixture 1c2f107180c2b36137c097f4b2bba41219108163183f14e7074f49d1b5c81455
role-transcripts prior-art-extends-held-out head cc613b68ec97f5ec77c94a493ae89f4a6c1eeb03acf5c9edec8ba09e19e38721
role-transcripts reviewer-unvalidated-edge-ts fixture 4e84f7841dbd713ba0a2ed79312ba2e57bc26fcd4ef1cb50ec840c104ad9557b
role-transcripts reviewer-unvalidated-edge-ts head befe08107fe9a4c76f8fe9849c08c072c9b624a8af254bb8814beebbc3f7cc66
role-transcripts reviewer-unvalidated-edge-py fixture 053627210c5d50575fdc8eb3138918b33e8743785b0fb6f941db6de52f5bc18d
role-transcripts reviewer-unvalidated-edge-py head 3290d892df908d433df9a9b4d4c4be6951aea424fd79df4e2d63465f40fc4b85
role-transcripts implementer-refactor-ticket fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts supervisor-refactor-lane fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff head 89821450529972a5b4640e77b674f9b1f34e53b152032132b1c4f05f3e28048f
role-transcripts reviewer-seam-shallow-unagreed fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-shallow-unagreed head ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
role-transcripts reviewer-seam-listed-deep-clear fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-listed-deep-clear head 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
role-transcripts implementer-deepen-first fixture 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
shaper-repair repair-moment-bye fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-verbose fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-emoji fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-inner-space fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-from fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-owner fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-formal fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-adr fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-typo fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers impl-prove-json-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-empty-name-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-read-only fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-test-command fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-lowercase-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-rename-json-key fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-list-callers fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-explain-term fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers blast-radius-keep-whitespace fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-editorconfig fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-changelog fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-show-last fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-leave-uncommitted fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-file-issue fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-pr-status fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-local-branches fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-draft-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-open-draft fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-near-commit-msg fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-ticket-scope fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-near-todo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-shout-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-two-tickets fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-already-done fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-estimate fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-port-env fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-env-file fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-near-python-env fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-near-readme-typo fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-add-zod fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-lock-sync fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-near-python-dep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pnpm-near-test-script fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pull-origin-main fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-upstream-moved fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-log fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-new-branch fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-name-length fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-ruff-config fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-agents-typo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers tdd-shout-flag fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-tab-in-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-run-suite fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-miss-count-tests fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-precise-type fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-near-python-hints fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-near-node-version fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-evalcases-skill-sections fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-new-repo-skill fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-evalcases-near-read-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-near-use-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers sup-commit-pr-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-last-touch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-pr-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-close-issue fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-status-file fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-draft-comment fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-merge-head fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-diff-stat fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-pr-number fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghissues-file-ticket fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-tell-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-spawn-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-read-handoffs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-lane-field fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-build-criterion fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-docstring-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-lane-record fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-draft-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-refresh-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-ahead-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-local-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-break-spec fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-slice-criteria fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-mark-done fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-poke-idle fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-relay-merge fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-lane-wait fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-count-findings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-file-parent fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-main-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-built fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-owner-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-review-state fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-near-handoff-time fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-parent-children fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-near-tickets-md fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-remove-scratch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-agents-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-show-last fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-owner-twice fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-repeat-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-one-bug fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-repeated-instruction fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-prose-ignored fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-quote-rule fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-add-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-tighten-agents fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-new-skill fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-headings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-code-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-classes fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-review-comments fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-verdict-checks fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers corrector-eval-cases-should fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-should-heldout fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-pytest fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-field-or-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-review-shout-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-times-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-count-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-fetch-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-pr-threads fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-local-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-class-tag fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-plain fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-json fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-list-ids fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-app-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-tdd-shout-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-would-catch fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-count-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-run-suite fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers impl-createverify-no-harness fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-run-once fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-list-skills fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-audit fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-drift fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-define fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-json fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers dir-lever-status-by-hand fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-steps fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-test-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-lane-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-finding-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-handoff-stamp fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-goal-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-call-sites fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-rename fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-which-function fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-add-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-again fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-event-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-one-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-verify-sha fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-record-merge-ask fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-set-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-finding-logged fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-prior-art-again fixture 85060cfd3157b5b83397d9140e543d3093446f90d1eacd222b019b32cd3349f8
skill-triggers cor-lever-restated-sites fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-restated-comments fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-near-one-pointer fixture 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
skill-triggers cor-lever-near-owner fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers dir-encode-route-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-waiting-reminders fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-first-handoff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-planned fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-brief-demo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-free-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-last-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-blocked fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-encode-release-duty fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-forgotten-tests fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-near-imports fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-encode-near-entry fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-browser-rendered-banner fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-screenshot fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-selector fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-html-grep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-reproduce-render fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-visible-paragraphs fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-headless fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-readme-link fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers reflector-reflect-lane-gh5 fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-lane-held fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-quote fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers shaper-sharpen-languages fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-shout-code fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-history fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-farewell fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-correction fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-rate-limit fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-config fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-anchor fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-guest fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-team fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-define fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-glossary-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-clock-seam fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-greeter-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-wording fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-error-text fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-tangled fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-review fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-new-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-flag fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers impl-design-seam fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-phrasebook fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-bugfix fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-rename fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-design-seam fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-phrasebook fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-bugfix fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-rename fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers impl-kit-ts-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers shaper-repair-multi-name fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-lang fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-clean-repo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-clean-version fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-question-exit fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-question-json fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers gw-herdr-send-test-list fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-director-ticket-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-which-pane fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-json-greeting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-measure-dirs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-gate-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-diff-files fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-refactor-fold-goodbye fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-split-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-cut-fold fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-brief-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-refactor-fold fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-name-check fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-wave fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-inner-space fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers sup-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-principles-one-result fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-one-printer fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-retire fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-shout fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
```

## #990: check-evals refuses a fixture file its base supplies

Rule: schema.md, Fixtures (No base duplicate). Owner ruling 2026-11-18 #986.

### Red proof: a real past whole copy

python-app-shout-cli's whole tree from origin/main (ee42108a) laid back over dc11b3cd's evals, its `.eval-fixture.json` (base python-app-shout) kept. The two `src/app/__init__.py` lines are dc11b3cd's own leftovers, deleted in this commit once CI syncs the materialized trees (below).

```
$ s=/tmp/gh990-red; mkdir $s; git archive dc11b3cd evals evidence | tar -x -C $s
$ git archive ee42108a evals/fixtures/python-app-shout-cli | tar -x -C $s
$ scripts/check-evals $s/evals; echo "exit=$?"
check-evals: fixtures/python-app-pydantic/src/app/__init__.py: field base: the same file base python-app supplies (fixtures/python-app/src/app/__init__.py); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/.gitignore: field base: the same file base python-app-shout supplies (fixtures/python-app/.gitignore); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/AGENTS.md: field base: the same file base python-app-shout supplies (fixtures/python-app/AGENTS.md); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/justfile: field base: the same file base python-app-shout supplies (fixtures/python-app/justfile); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/pyproject.toml: field base: the same file base python-app-shout supplies (fixtures/python-app/pyproject.toml); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/uv.lock: field base: the same file base python-app-shout supplies (fixtures/python-app/uv.lock); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/.github/workflows/check.yml: field base: the same file base python-app-shout supplies (fixtures/python-app/.github/workflows/check.yml); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/src/app/__init__.py: field base: the same file base python-app-shout supplies (fixtures/python-app/src/app/__init__.py); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/src/app/cli.py: field base: the same file base python-app-shout supplies (fixtures/python-app-shout/src/app/cli.py); delete it: the base supplies it
check-evals: fixtures/python-app-shout-cli/.githooks/pre-commit: field base: the same file base python-app-shout supplies (fixtures/python-app/.githooks/pre-commit); delete it: the base supplies it
check-evals: fixtures/python-app-tiers/src/app/__init__.py: field base: the same file base py-mini supplies (fixtures/py-mini/src/app/__init__.py); delete it: the base supplies it
check-evals: 11 problem(s) above; fix the case (check-evals --help lists the shape)
exit=1
```

tests/test_cli.py and src/app/core.py, which differ from the base, pass.

### The two empty `__init__.py`: CI syncs the materialized trees

dc11b3cd kept python-app-pydantic's and python-app-tiers' empty `src/app/__init__.py` because CI synced each raw `evals/fixtures/*/uv.lock` dir. CI now syncs each tree `check-evals --export` writes (one materializer, `fixture_tree`); the box and gate sync no raw fixture dir (octo-feather-qa syncs the materialized case repo). With both files deleted:

- `check-evals --trees` on `git archive origin/main evals` vs head: diff empty, 372 lines, sha256 fce30d4c.
- `check-evals --export /tmp/gh990-export`: 54 trees; CI's loop with `--offline` over the 35 with a `uv.lock`: 35 synced, 0 failed. The raw dirs python-app-pydantic and python-app-tiers: uv sync exit 1 (hatchling build failure), as expected.
- `scripts/check-evals` on head: `evals: ok (11 suites, 489 cases)`, exit 0.

## #991: #882's lane-shout fixtures on bases

Rule: schema.md, Fixtures. Owner ruling 2026-11-18 #986. Lane gh986-991 merged origin/main 16798024 (PR #882) as merge commit 1a852f35, no conflict.

### Readers

#882's `head.then` and `branches` (schema.md, Case) commit their trees in octo-feather-qa's `fixture_copy` through `fixture_src`, which calls `fixture_tree`: no raw copytree of evals/fixtures remains. check-evals reads the tree the agent sees (`seen_tree`, a then entry's included) through `read_tree`. `--export` writes every fixture dir, so it covers then and branches trees already. `--trees` covered fixture and head only: extended (2df0b2e2) to a line per `head.then[i]` and `branches[i]`, seam on #991 comment 6990897244, test tests/qa-fixture-base.sh.

`--trees` on `git archive 16798024 evals`: unextended (d8e59dec's check-evals) 417 lines, sha256 a36156c0; extended 427, sha256 902ebb01; diff only these 10 added lines:

```
supervisor-delegation repair-result-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated branches[1] 0b47f53e703a20f8cac4f91339e6c150abeb3c3bc7d14079d47a36ea4b5367f6
supervisor-delegation merge-ask-on-lane-pr head.then[0] 80eabb1c091108d44ee4dab5fd915d8c974f943efc1a3629c8a23b86a4459e3b
supervisor-delegation worker-repair-integrated branches[0] b52cd8b49c4e44001a9493bf930c1dff5addea56af2e26efcf6731518c1304e3
supervisor-general-worker diagnosis-diff-goes-to-implementer branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-general-worker reviewed-implementer-result-integrated branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker reviewed-implementer-result-integrated branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
```

### Collapse

Script /tmp/gh986-collapse-991/apply.py (measure.py: within the lane-shout family only, cross-family is #1007; each fixture's cheapest base whose paths its tree holds, no removal). lane-shout-main, -conflict and -wip hold the same paths; any root among them costs 17 own files in all, so the root is lane-shout-main (the main tree), with -wip on it, -conflict and -qc-fixed on -wip, -ready on -wip-log (same cost as -conflict, its lane predecessor). Overlays, each fixture's own files:

```
lane-shout-main          (root, whole: 13 files)
lane-shout-base       -> lane-shout-main:        mise.toml
lane-shout-wip        -> lane-shout-main:        src/app/cli.py, src/app/core.py, tests/test_cli.py
lane-shout-conflict   -> lane-shout-wip:         tests/test_cli.py
lane-shout-wip-log    -> lane-shout-wip:         notes/gh12.handoffs.jsonl
lane-shout-ready      -> lane-shout-wip-log:     docs/specs/hello.status.json, evidence/2026-11-13-gh12-qc.md, notes/gh12.handoffs.jsonl, tests/test_cli.py
lane-shout-qc-fixed   -> lane-shout-wip:         mise.toml, tests/test_cli.py
lane-shout-qc-red     -> lane-shout-qc-fixed:    src/app/cli.py, tests/test_cli.py
lane-shout-qc-red-lane -> lane-shout-qc-red:     evidence/2026-11-17-gh12-qc.md
lane-shout-qc-repaired -> lane-shout-qc-red-lane: src/app/cli.py, tests/test_cli.py
lane-shout-general-diff -> lane-shout-qc-red:    src/app/cli.py, tests/test_shout_plain.py
lane-shout-names      -> lane-shout-base:        tests/test_names.py
lane-shout-merged     -> lane-shout-qc-fixed:    tests/test_names.py
lane-shout-integrated -> lane-shout-qc-fixed:    docs/specs/hello.status.json, tests/test_names.py
```

Counts (git ls-files, wc -l):

- evals/fixtures: main 16798024 866 files, 32194 lines; head 367 files, 11466 lines.
- lane-shout-*: main 200 files, 7189 lines; head 49 files (13 of them `.eval-fixture.json`), 915 lines.

### Proof

- `check-evals --trees` on `git archive 16798024 evals` vs head: diff empty, 427 lines each, sha256 902ebb01. The 24 lane-shout cases hold 49 of those lines (fixture, head, head.then, branches), each the same hash before and after.
- `scripts/check-evals` on head: `evals: ok (17 suites, 517 cases)`, exit 0 (base duplicate refusal included).
- `check-evals --export`: 70 trees; `uv sync --locked --offline` in each of the 49 holding a `uv.lock` (the 14 lane-shout among them): 49 synced, 0 failed.

### Main list (16798024 evals, extended --trees)

```
history implementer-ts-toml-at-scale fixture history kit@0f4f1bad2c7caf593a6a2e7c1e18c9f1617238f1
isolation reach-live-state fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
isolation reach-other-repos fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
ladder corrector-fuzzy-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-fact-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-coupling-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-secret-grep fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-exec-bit fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-test-vs-check fixture 4c7bd10e296030efe032e0b7592ec12f29beafdedc059a3925c3f39ce95c05c3
ladder reviewer-proxy-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-check head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder reviewer-exact-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-exact-check head d21c3b72099041ed423ea2e548ce0c665beeb07ca25553ceb648dd8c985248fc
ladder reviewer-product-command-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-product-command-check head e67fee2b9f987a20ccaca236688964b1147d6baae35630c4f8596ee97c7aeb1a
ladder reviewer-no-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-no-check head cec75972860bf251fdc5c425cf5eac3428aefa37341b29066474ca1d86fd2fec
ladder reviewer-test-is-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-test-is-check head b3da95bddba3345dcbefee5e37b6433bf35d0cee52b99e95455611bfe9492cb2
ladder reviewer-owner-lines fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-lines head 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
ladder reviewer-owner-pointers fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-pointers head 6884c8ac3f304107430e6d2add72a1e3e2bae399e212e123a1a1eaf4860aa547
ladder reviewer-owner-none fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-none head 9ecd9fd27bf99038e05fc3916a4b8185fc622b9dde2f20a71bd8e0ddd1212a91
ladder reviewer-comment-restatement-note fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-comment-restatement-note head 4a67f75baab2ef5ea72e0b57937eff3923639efa1cb33e3ed914ea5c74ab2a75
ladder reviewer-skill-restatement-blocks fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-skill-restatement-blocks head 4f8fbeda194627c5bab45e040a2285d9a1e735c75c27ce6712042f47c76c22c0
ladder corrector-template-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-kit-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder implementer-owned-rule fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts implementer-python-ticket fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts implementer-skill-ticket fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts implementer-verify-pass fixture 98760158690733a058258eabee0cbe8353f5fc8a4fbb95ae6c3c01575310496b
role-transcripts implementer-verify-create fixture 25b4d7f6676efb12db4b6d0ab40fa038b6c16db6997b2aa4e2356bfd4a04bfc9
role-transcripts implementer-verify-kit fixture 5bda838e3669ab5e05bc720542119d40286e8c1422a8a94d5ce9c976234b3c42
role-transcripts corrector-repeated-class fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts corrector-repo-skill-rule fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts reviewer-test-quality fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-test-quality head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts reviewer-criterion-test-adequacy fixture e55b7a0db2269bd4e18b955943065a6576690f342025e2e708c045532e656657
role-transcripts reviewer-criterion-test-adequacy head ff0d7e546cfda4db14902a3142404614ccfd2c0bdfecbc8e35d8524856a92cd2
role-transcripts qc-judge-demo-path fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts qc-judge-no-reviewer-skills fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts director-file-parent fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts corrector-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts qc-judge-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts implementer-verify-map-current fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts corrector-evidence-field fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts reviewer-reinvented-parser fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-reinvented-parser head db3ddd04f2745c5f0b419a6e1672e86fabcbc7c65c1d377c501378d42a6ec64f
role-transcripts reviewer-prose-duty-blocks fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts reviewer-prose-duty-blocks head 0a7feb3ac3a8360031c55168574800c4275f81c9ec21ef551adbea2bda75511b
role-transcripts implementer-library-web fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts director-merge-report-post-merge fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts shaper-code-ask-shapes-spec fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts dir-spawns-shaper fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts shaper-library-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-wording-proof fixture 529f5a1a5f3878355b4afab170ac5f7027657891f5822c5f4ee8da5ee476b3a6
role-transcripts shaper-table-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-hands-off-on-fast fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
role-transcripts implementer-hands-off-on-fast-heldout fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
role-transcripts implementer-hands-off-on-fast-heldout-2 fixture 8fdd2ad8d67c63138c417e64b98705c04a3573ccd2928188b871a4aa9ec93dbf
role-transcripts implementer-missing-recording-heldout fixture 1d9dc73deb7a60ad337ed8e9addfafc36bfe9b8dfdec3f3683acec0ea433cabc
role-transcripts prior-art-extends fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends head 6c942d9599f0b8afef8b9a9e913f82c866d22b9bbcf0d0b93de16c1999513f99
role-transcripts prior-art-extends-stated fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends-stated head ca2e1f06f2664353a5d3a8abb86ad91eb04a90cfe145387613ab6109068bc888
role-transcripts prior-art-extends-held-out fixture 1c2f107180c2b36137c097f4b2bba41219108163183f14e7074f49d1b5c81455
role-transcripts prior-art-extends-held-out head cc613b68ec97f5ec77c94a493ae89f4a6c1eeb03acf5c9edec8ba09e19e38721
role-transcripts reviewer-unvalidated-edge-ts fixture 4e84f7841dbd713ba0a2ed79312ba2e57bc26fcd4ef1cb50ec840c104ad9557b
role-transcripts reviewer-unvalidated-edge-ts head befe08107fe9a4c76f8fe9849c08c072c9b624a8af254bb8814beebbc3f7cc66
role-transcripts reviewer-unvalidated-edge-py fixture 053627210c5d50575fdc8eb3138918b33e8743785b0fb6f941db6de52f5bc18d
role-transcripts reviewer-unvalidated-edge-py head 3290d892df908d433df9a9b4d4c4be6951aea424fd79df4e2d63465f40fc4b85
role-transcripts implementer-refactor-ticket fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts supervisor-refactor-lane fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff head 89821450529972a5b4640e77b674f9b1f34e53b152032132b1c4f05f3e28048f
role-transcripts reviewer-seam-shallow-unagreed fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-shallow-unagreed head ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
role-transcripts reviewer-seam-listed-deep-clear fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-listed-deep-clear head 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
role-transcripts implementer-deepen-first fixture 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
shaper-repair repair-moment-bye fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-verbose fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-emoji fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-inner-space fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-from fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-owner fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-formal fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-adr fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-typo fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers impl-prove-json-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-empty-name-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-read-only fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-test-command fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-lowercase-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-rename-json-key fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-list-callers fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-explain-term fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers blast-radius-keep-whitespace fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-editorconfig fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-changelog fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-show-last fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-leave-uncommitted fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-file-issue fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-pr-status fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-local-branches fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-draft-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-open-draft fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-near-commit-msg fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-ticket-scope fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-near-todo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-shout-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-two-tickets fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-already-done fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-estimate fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-port-env fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-env-file fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-near-python-env fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-near-readme-typo fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-add-zod fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-lock-sync fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-near-python-dep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pnpm-near-test-script fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pull-origin-main fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-upstream-moved fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-log fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-new-branch fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-name-length fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-ruff-config fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-agents-typo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers tdd-shout-flag fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-tab-in-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-run-suite fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-miss-count-tests fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-precise-type fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-near-python-hints fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-near-node-version fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-evalcases-skill-sections fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-new-repo-skill fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-evalcases-near-read-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-near-use-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers sup-commit-pr-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-last-touch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-pr-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-close-issue fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-status-file fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-draft-comment fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-merge-head fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-diff-stat fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-pr-number fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghissues-file-ticket fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-tell-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-spawn-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-read-handoffs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-lane-field fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-build-criterion fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-docstring-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-lane-record fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-draft-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-refresh-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-ahead-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-local-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-break-spec fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-slice-criteria fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-mark-done fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-poke-idle fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-relay-merge fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-lane-wait fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-count-findings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-file-parent fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-main-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-built fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-owner-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-review-state fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-near-handoff-time fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-parent-children fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-near-tickets-md fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-remove-scratch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-agents-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-show-last fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-owner-twice fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-repeat-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-one-bug fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-repeated-instruction fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-prose-ignored fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-quote-rule fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-add-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-tighten-agents fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-new-skill fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-headings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-code-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-classes fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-review-comments fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-verdict-checks fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers corrector-eval-cases-should fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-should-heldout fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-pytest fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-field-or-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-review-shout-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-times-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-count-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-fetch-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-pr-threads fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-local-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-class-tag fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-plain fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-json fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-list-ids fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-app-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-tdd-shout-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-would-catch fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-count-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-run-suite fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers impl-createverify-no-harness fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-run-once fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-list-skills fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-audit fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-drift fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-define fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-json fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers dir-lever-status-by-hand fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-steps fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-test-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-lane-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-finding-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-handoff-stamp fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-goal-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-call-sites fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-rename fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-which-function fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-add-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-again fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-event-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-one-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-verify-sha fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-record-merge-ask fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-set-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-finding-logged fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-prior-art-again fixture 85060cfd3157b5b83397d9140e543d3093446f90d1eacd222b019b32cd3349f8
skill-triggers cor-lever-restated-sites fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-restated-comments fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-near-one-pointer fixture 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
skill-triggers cor-lever-near-owner fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers dir-encode-route-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-waiting-reminders fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-first-handoff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-planned fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-brief-demo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-free-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-last-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-blocked fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-encode-release-duty fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-forgotten-tests fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-near-imports fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-encode-near-entry fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-browser-rendered-banner fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-screenshot fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-selector fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-html-grep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-reproduce-render fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-visible-paragraphs fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-headless fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-readme-link fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers reflector-reflect-lane-gh5 fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-lane-held fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-quote fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers shaper-sharpen-languages fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-shout-code fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-history fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-farewell fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-correction fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-rate-limit fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-config fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-anchor fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-guest fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-team fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-define fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-glossary-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-clock-seam fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-greeter-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-wording fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-error-text fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-tangled fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-review fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-new-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-flag fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers impl-design-seam fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-phrasebook fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-bugfix fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-rename fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-design-seam fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-phrasebook fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-bugfix fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-rename fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers impl-kit-ts-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers shaper-repair-multi-name fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-lang fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-clean-repo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-clean-version fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-question-exit fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-question-json fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers gw-herdr-send-test-list fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-director-ticket-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-which-pane fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-json-greeting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-measure-dirs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-gate-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-diff-files fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-refactor-fold-goodbye fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-split-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-cut-fold fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-brief-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-refactor-fold fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-name-check fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-wave fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-inner-space fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers sup-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-principles-one-result fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-one-printer fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-retire fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-shout fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
supervisor-autonomy local-repair-and-ready-work fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy local-repair-and-ready-work head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy worker-blocked-local-not-escalated fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy worker-blocked-local-not-escalated head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy spec-conflict-and-local-repair fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy spec-conflict-and-local-repair head ae158303e444c64de75e8559a91a59377ffe71deb199b483ce2c0fde28699cce
supervisor-autonomy owner-access-blocker-and-ready-work fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy owner-access-blocker-and-ready-work head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy owner-access-blocker-message fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy owner-access-blocker-message head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-delegation qc-failure-delegates-repair fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation qc-failure-brief-review fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation repair-result-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation repair-result-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated fixture a3bdf23231065ec1b73605438e6b1ab053d567e8dd6d0a6e760eb9d4ccb30251
supervisor-delegation two-results-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated branches[1] 0b47f53e703a20f8cac4f91339e6c150abeb3c3bc7d14079d47a36ea4b5367f6
supervisor-delegation owner-need-reaches-director fixture 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation implementer-repairs-qc-failure fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation implementer-repairs-qc-failure head adaebdff6d2d2941775769bc6fe2068419047879bc8798696899ed6bdd7c9ac2
supervisor-delegation merge-ask-on-lane-pr fixture a3bdf23231065ec1b73605438e6b1ab053d567e8dd6d0a6e760eb9d4ccb30251
supervisor-delegation merge-ask-on-lane-pr head 866733792dea0ed2a3352fbda300f5355e6fce86bc0fb1042f66bce12ba97623
supervisor-delegation merge-ask-on-lane-pr head.then[0] 80eabb1c091108d44ee4dab5fd915d8c974f943efc1a3629c8a23b86a4459e3b
supervisor-delegation worker-repair-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation worker-repair-integrated head adaebdff6d2d2941775769bc6fe2068419047879bc8798696899ed6bdd7c9ac2
supervisor-delegation worker-repair-integrated branches[0] b52cd8b49c4e44001a9493bf930c1dff5addea56af2e26efcf6731518c1304e3
supervisor-fresh-worker closed-assignment-fresh-worker fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker closed-assignment-fresh-worker head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker serial-assignment-split fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker serial-assignment-split head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker independent-ready-split fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker independent-ready-split head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker one-worker-limit fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker one-worker-limit head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-general-worker diagnosis-diff-goes-to-implementer fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker diagnosis-diff-goes-to-implementer branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker implementer-result-integrated-not-candidate branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-general-worker reviewed-implementer-result-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker reviewed-implementer-result-integrated branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker reviewed-implementer-result-integrated branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-general-worker cleanup-result-consumed fixture 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-notifications routine-results-no-director fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications routine-results-no-director head 3ea7e6ea934603a4d373d9948e58637adb1c2e72f3f8bbf3c35c3f8fabd26d8b
supervisor-notifications merge-ready-only-merge-ask fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications merge-ready-only-merge-ask head cbb8cdc4799d4100caf358695c2c8d39ba723fb789634d09e7c0bd0830cce912
supervisor-notifications owner-blocker-reaches-director fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications owner-blocker-reaches-director head 3ea7e6ea934603a4d373d9948e58637adb1c2e72f3f8bbf3c35c3f8fabd26d8b
supervisor-notifications gh785-ended-worker-replay fixture 45115ee94d31fa3a1a4c4a608cd9caae2c24d19d6402a6802382a797a5ae9006
supervisor-notifications gh785-ended-worker-replay head 78ffa79f477d6811cf857fae0997e3b91dff7f19c26399d12d60123e7dbe4b0a
worker-uncertain-send queued-timeout-sent-once fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
worker-uncertain-send reviewer-queued-timeout-sent-once fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
worker-uncertain-send reviewer-queued-timeout-sent-once head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
worker-uncertain-send blocked-refusal-sent-again fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
```

### Head list

```
history implementer-ts-toml-at-scale fixture history kit@0f4f1bad2c7caf593a6a2e7c1e18c9f1617238f1
isolation reach-live-state fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
isolation reach-other-repos fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
ladder corrector-fuzzy-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-fact-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-coupling-lesson fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-secret-grep fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-exec-bit fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder implementer-test-vs-check fixture 4c7bd10e296030efe032e0b7592ec12f29beafdedc059a3925c3f39ce95c05c3
ladder reviewer-proxy-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-check head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder reviewer-exact-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-exact-check head d21c3b72099041ed423ea2e548ce0c665beeb07ca25553ceb648dd8c985248fc
ladder reviewer-product-command-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-product-command-check head e67fee2b9f987a20ccaca236688964b1147d6baae35630c4f8596ee97c7aeb1a
ladder reviewer-no-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-no-check head cec75972860bf251fdc5c425cf5eac3428aefa37341b29066474ca1d86fd2fec
ladder reviewer-test-is-check fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-test-is-check head b3da95bddba3345dcbefee5e37b6433bf35d0cee52b99e95455611bfe9492cb2
ladder reviewer-owner-lines fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-lines head 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
ladder reviewer-owner-pointers fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-pointers head 6884c8ac3f304107430e6d2add72a1e3e2bae399e212e123a1a1eaf4860aa547
ladder reviewer-owner-none fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
ladder reviewer-owner-none head 9ecd9fd27bf99038e05fc3916a4b8185fc622b9dde2f20a71bd8e0ddd1212a91
ladder reviewer-comment-restatement-note fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-comment-restatement-note head 4a67f75baab2ef5ea72e0b57937eff3923639efa1cb33e3ed914ea5c74ab2a75
ladder reviewer-skill-restatement-blocks fixture 2416b2f44c0503eb6e9068475a4c813170899ff7c5a1893d2c78db25ea59e199
ladder reviewer-skill-restatement-blocks head 4f8fbeda194627c5bab45e040a2285d9a1e735c75c27ce6712042f47c76c22c0
ladder corrector-template-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder corrector-kit-route fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
ladder reviewer-proxy-blocks head ed34838b729d1dae714dbbf8cc7ddadbc1f15414ab4f5755a8fce7f4eb0a26b4
ladder implementer-owned-rule fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts implementer-python-ticket fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts implementer-skill-ticket fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts implementer-verify-pass fixture 98760158690733a058258eabee0cbe8353f5fc8a4fbb95ae6c3c01575310496b
role-transcripts implementer-verify-create fixture 25b4d7f6676efb12db4b6d0ab40fa038b6c16db6997b2aa4e2356bfd4a04bfc9
role-transcripts implementer-verify-kit fixture 5bda838e3669ab5e05bc720542119d40286e8c1422a8a94d5ce9c976234b3c42
role-transcripts corrector-repeated-class fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts corrector-repo-skill-rule fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
role-transcripts reviewer-test-quality fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-test-quality head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts reviewer-criterion-test-adequacy fixture e55b7a0db2269bd4e18b955943065a6576690f342025e2e708c045532e656657
role-transcripts reviewer-criterion-test-adequacy head ff0d7e546cfda4db14902a3142404614ccfd2c0bdfecbc8e35d8524856a92cd2
role-transcripts qc-judge-demo-path fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts qc-judge-no-reviewer-skills fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts director-file-parent fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts supervisor-publish-lane head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
role-transcripts corrector-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts qc-judge-drives-app fixture ecbaf21628b0ffeb71424f1c934f09eac1f78fe81255dcb464bb63635e9568a6
role-transcripts implementer-verify-map-current fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts corrector-evidence-field fixture b07834f342cef09f832ab2e64f40e71447f31b2e0af1ad9998956c0919c5ea8c
role-transcripts reviewer-reinvented-parser fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts reviewer-reinvented-parser head db3ddd04f2745c5f0b419a6e1672e86fabcbc7c65c1d377c501378d42a6ec64f
role-transcripts reviewer-prose-duty-blocks fixture 72c9a02629c3ac0e5aa37d51d587a16d1df81f726965c9a49f4c2a86fc948ad7
role-transcripts reviewer-prose-duty-blocks head 0a7feb3ac3a8360031c55168574800c4275f81c9ec21ef551adbea2bda75511b
role-transcripts implementer-library-web fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts director-merge-report-post-merge fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
role-transcripts shaper-code-ask-shapes-spec fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts dir-spawns-shaper fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts shaper-library-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-wording-proof fixture 529f5a1a5f3878355b4afab170ac5f7027657891f5822c5f4ee8da5ee476b3a6
role-transcripts shaper-table-ask-web fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
role-transcripts implementer-hands-off-on-fast fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
role-transcripts implementer-hands-off-on-fast-heldout fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
role-transcripts implementer-hands-off-on-fast-heldout-2 fixture 8fdd2ad8d67c63138c417e64b98705c04a3573ccd2928188b871a4aa9ec93dbf
role-transcripts implementer-missing-recording-heldout fixture 1d9dc73deb7a60ad337ed8e9addfafc36bfe9b8dfdec3f3683acec0ea433cabc
role-transcripts prior-art-extends fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends head 6c942d9599f0b8afef8b9a9e913f82c866d22b9bbcf0d0b93de16c1999513f99
role-transcripts prior-art-extends-stated fixture cb8c44ed3a5a788d838fcc457f2245a2272807ba411a1b75816b037c4bbdf1f5
role-transcripts prior-art-extends-stated head ca2e1f06f2664353a5d3a8abb86ad91eb04a90cfe145387613ab6109068bc888
role-transcripts prior-art-extends-held-out fixture 1c2f107180c2b36137c097f4b2bba41219108163183f14e7074f49d1b5c81455
role-transcripts prior-art-extends-held-out head cc613b68ec97f5ec77c94a493ae89f4a6c1eeb03acf5c9edec8ba09e19e38721
role-transcripts reviewer-unvalidated-edge-ts fixture 4e84f7841dbd713ba0a2ed79312ba2e57bc26fcd4ef1cb50ec840c104ad9557b
role-transcripts reviewer-unvalidated-edge-ts head befe08107fe9a4c76f8fe9849c08c072c9b624a8af254bb8814beebbc3f7cc66
role-transcripts reviewer-unvalidated-edge-py fixture 053627210c5d50575fdc8eb3138918b33e8743785b0fb6f941db6de52f5bc18d
role-transcripts reviewer-unvalidated-edge-py head 3290d892df908d433df9a9b4d4c4be6951aea424fd79df4e2d63465f40fc4b85
role-transcripts implementer-refactor-ticket fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts supervisor-refactor-lane fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
role-transcripts reviewer-refactor-diff head 89821450529972a5b4640e77b674f9b1f34e53b152032132b1c4f05f3e28048f
role-transcripts reviewer-seam-shallow-unagreed fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-shallow-unagreed head ade6af22bc706a06ab8eab689124d3dd026ab0affae07889a0fad1253cbe6482
role-transcripts reviewer-seam-listed-deep-clear fixture 04c2ffbdffd34cc0d2f8e1f515e6c1f5ba1b392403f53fd95166552dab928dc8
role-transcripts reviewer-seam-listed-deep-clear head 23dd7dfb45ecd9e77066f844390af37fa245c6745c15f086c027c1a71146beae
role-transcripts implementer-deepen-first fixture 91f8d9fd8815dc8aec213136222e0966582f54cd4d428f6d15c7c6facb129f6b
shaper-repair repair-moment-bye fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-verbose fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-emoji fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-inner-space fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-from fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-owner fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-clean-formal fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
shaper-repair repair-moment-near-question-adr fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
shaper-repair repair-moment-near-typo fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers impl-prove-json-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-empty-name-claim fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-read-only fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-prove-near-test-command fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-lowercase-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-rename-json-key fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-list-callers fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-blast-near-explain-term fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers blast-radius-keep-whitespace fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-editorconfig fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-changelog fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-show-last fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-commit-near-leave-uncommitted fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-file-issue fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-pr-status fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-local-branches fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-github-near-draft-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-open-draft fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghpr-near-commit-msg fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-ticket-scope fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ghissues-near-todo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-shout-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-two-tickets fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-already-done fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-implement-near-estimate fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-port-env fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-env-file fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-nodejs-near-python-env fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-nodejs-near-readme-typo fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-add-zod fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-lock-sync fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pnpm-near-python-dep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pnpm-near-test-script fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-pull-origin-main fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-upstream-moved fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-log fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-pull-near-new-branch fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-name-length fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-ruff-config fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-agents-typo fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-python-near-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers tdd-shout-flag fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-tab-in-name fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-run-suite fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers tdd-near-miss-count-tests fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-precise-type fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-shout fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-ts-near-python-hints fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-ts-near-node-version fixture 00ad05051d163260491f74d2b50ad6b22a7d64bdd3ead407b1b8d57d7d0cf2c8
skill-triggers impl-evalcases-skill-sections fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-new-repo-skill fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-evalcases-near-read-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-evalcases-near-use-skill fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers sup-commit-pr-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-last-touch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-pr-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-close-issue fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-status-file fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-github-near-draft-comment fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-merge-head fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-diff-stat fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghpr-near-pr-number fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-ghissues-file-ticket fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-tell-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-spawn-worker fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-read-handoffs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-herdr-near-lane-field fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-build-criterion fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-docstring-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-implspec-near-lane-record fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-draft-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-refresh-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-ahead-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-push-near-local-body fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-break-spec fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-slice-criteria fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-tickets-near-mark-done fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-poke-idle fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-relay-merge fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-lane-wait fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-herdr-near-count-findings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-file-parent fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-main-ci fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-built fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-github-near-owner-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-review-state fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghpr-near-handoff-time fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-parent-children fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-ghissues-near-tickets-md fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-remove-scratch fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-agents-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-show-last fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-commit-near-draft-msg fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-owner-twice fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-repeat-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-correct-near-one-bug fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-repeated-instruction fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-prose-ignored fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-quote-rule fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-encode-near-add-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-tighten-agents fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-new-skill fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-headings fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-writing-near-code-typo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-classes fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-github-near-call-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-review-comments fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-ghpr-verdict-checks fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers corrector-eval-cases-should fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-should-heldout fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-pytest fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers corrector-eval-cases-near-field-or-text fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-review-shout-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-times-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-count-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-review-near-summarize fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-fetch-pr fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-pr-threads fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-local-diff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-github-near-class-tag fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-plain fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-greet-json fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-list-ids fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers qc-prove-near-app-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers rev-tdd-shout-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-would-catch fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-count-tests fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers rev-tdd-near-run-suite fixture b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
skill-triggers impl-createverify-no-harness fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-ticket fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-run-once fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-createverify-near-list-skills fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-audit fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-drift fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-define fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-maintainverify-near-json fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers dir-lever-status-by-hand fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-steps fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-test-command fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-lane-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-finding-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-handoff-stamp fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-goal-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-call-sites fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-rename fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-which-function fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers cor-lever-near-add-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-teardown-again fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-event-lines fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-one-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-lever-near-verify-sha fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-record-merge-ask fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-set-waiting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-near-finding-logged fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-lever-prior-art-again fixture 85060cfd3157b5b83397d9140e543d3093446f90d1eacd222b019b32cd3349f8
skill-triggers cor-lever-restated-sites fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-restated-comments fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers cor-lever-near-one-pointer fixture 232ef16fcc9009dbabcdeff9f60f41db391ecd105ba4cce60fcba1c5ea03957b
skill-triggers cor-lever-near-owner fixture 692ca884722f9c0573efdf0109141b2ec632487e091a160e9e42fbde516319df
skill-triggers dir-encode-route-ruling fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-waiting-reminders fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-first-handoff fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers dir-encode-near-planned fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-brief-demo fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-free-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-last-class fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers sup-encode-near-blocked fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-encode-release-duty fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-forgotten-tests fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-encode-near-imports fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-encode-near-entry fixture 95b754bd264695387bf4b9b8f4ef55c9f755e8c90d7faf3d997962957fdf876d
skill-triggers impl-browser-rendered-banner fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-screenshot fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-selector fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-browser-near-html-grep fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-reproduce-render fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-visible-paragraphs fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-headless fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers cor-browser-near-readme-link fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers reflector-reflect-lane-gh5 fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-lane-held fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers reflector-reflect-near-quote fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers shaper-sharpen-languages fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-shout-code fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-sharpen-near-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-history fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-farewell fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grill-docs-near-correction fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-rate-limit fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-config fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-question fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-grilling-near-anchor fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-guest fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-team fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-define fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-domain-near-glossary-typo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-clock-seam fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-greeter-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-wording fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-design-near-error-text fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-tangled fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-review fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-new-module fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-arch-near-flag fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers impl-design-seam fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-phrasebook fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-bugfix fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers impl-design-near-rename fixture e69b3fe04dc4ded096d4a619e67bd3c2631afa8f97a616fabac923c2de7175d5
skill-triggers rev-design-seam fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-phrasebook fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-bugfix fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers rev-design-near-rename fixture 082e73c5e12adfa8b222a3faf07721b9b78e21361bc5c0920f1a181ee848feab
skill-triggers impl-kit-ts-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-near-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-check-roles-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-contract-json-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-toml-doctor-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-py-near-resume-delays-a430 fixture history kit@a430da77962ca266f3746dcb54a414ed5869e0f1
skill-triggers impl-kit-ts-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-ts-near-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-check-roles-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-contract-json-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-toml-doctor-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers impl-kit-py-near-resume-delays-x153 fixture history kit@153a76d60620e30b181390ec83fc8611e938bbdb
skill-triggers shaper-repair-multi-name fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-lang fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-clean-repo fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-clean-version fixture 507acf1fa91256de9f1241c06ac57e318657d725a217acd5b14f6d6e6c259405
skill-triggers shaper-repair-near-question-exit fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers shaper-repair-near-question-json fixture 83ef4203225e185203c82a3024d74bb0c52f9139a50ae995709ceeef9647632b
skill-triggers gw-herdr-send-test-list fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-director-ticket-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-which-pane fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-herdr-near-handoff-count fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-json-greeting fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-measure-dirs fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-gate-line fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers gw-prove-near-diff-files fixture a530c7a9fdeba454f531adc5e56647f85644213cbc1bfbe242778d1f1e08d64a
skill-triggers impl-refactor-fold-goodbye fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-split-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers impl-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers impl-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-cut-fold fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-brief-count fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-refactor-near-wave fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-refactor-near-binary fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-refactor-fold fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-name-check fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-wave fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-refactor-near-inner-space fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers sup-principles-one-result fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-trace-json fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers sup-principles-near-retire fixture dbfec0c47da21b853beaf50886c5417978187f46142b36d9aa8e2ec526d4a3b7
skill-triggers sup-principles-near-lines fixture d9422279ba2766846561d1414e61b45847703582a62f4742aa3fd148c5741e9b
skill-triggers rev-principles-one-result fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-one-printer fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-retire fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
skill-triggers rev-principles-near-shout fixture f8b3a556a46ca7b575ba499343f73e93cefda1343c7a552abd8fbe63c425ffdf
supervisor-autonomy local-repair-and-ready-work fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy local-repair-and-ready-work head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy worker-blocked-local-not-escalated fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy worker-blocked-local-not-escalated head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy spec-conflict-and-local-repair fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy spec-conflict-and-local-repair head ae158303e444c64de75e8559a91a59377ffe71deb199b483ce2c0fde28699cce
supervisor-autonomy owner-access-blocker-and-ready-work fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy owner-access-blocker-and-ready-work head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-autonomy owner-access-blocker-message fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-autonomy owner-access-blocker-message head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-delegation qc-failure-delegates-repair fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation qc-failure-brief-review fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation repair-result-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation repair-result-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated fixture a3bdf23231065ec1b73605438e6b1ab053d567e8dd6d0a6e760eb9d4ccb30251
supervisor-delegation two-results-integrated branches[0] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation two-results-integrated branches[1] 0b47f53e703a20f8cac4f91339e6c150abeb3c3bc7d14079d47a36ea4b5367f6
supervisor-delegation owner-need-reaches-director fixture 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-delegation implementer-repairs-qc-failure fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation implementer-repairs-qc-failure head adaebdff6d2d2941775769bc6fe2068419047879bc8798696899ed6bdd7c9ac2
supervisor-delegation merge-ask-on-lane-pr fixture a3bdf23231065ec1b73605438e6b1ab053d567e8dd6d0a6e760eb9d4ccb30251
supervisor-delegation merge-ask-on-lane-pr head 866733792dea0ed2a3352fbda300f5355e6fce86bc0fb1042f66bce12ba97623
supervisor-delegation merge-ask-on-lane-pr head.then[0] 80eabb1c091108d44ee4dab5fd915d8c974f943efc1a3629c8a23b86a4459e3b
supervisor-delegation worker-repair-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-delegation worker-repair-integrated head adaebdff6d2d2941775769bc6fe2068419047879bc8798696899ed6bdd7c9ac2
supervisor-delegation worker-repair-integrated branches[0] b52cd8b49c4e44001a9493bf930c1dff5addea56af2e26efcf6731518c1304e3
supervisor-fresh-worker closed-assignment-fresh-worker fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker closed-assignment-fresh-worker head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker serial-assignment-split fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker serial-assignment-split head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker independent-ready-split fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker independent-ready-split head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-fresh-worker one-worker-limit fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-fresh-worker one-worker-limit head 8562217eef2b09d0454cc6f4bb227eeb1694aeac657a0602c3c4f6c85de5cc36
supervisor-general-worker diagnosis-diff-goes-to-implementer fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker diagnosis-diff-goes-to-implementer branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker implementer-result-integrated-not-candidate branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker implementer-result-integrated-not-candidate branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-general-worker reviewed-implementer-result-integrated fixture f16b82da0ffb0cc1e56fa266e6b6f5e68329d473082a68b627716c70e45cc025
supervisor-general-worker reviewed-implementer-result-integrated branches[0] 3391c5fb2cc9c9d7e8d3e4b82961a0784847bafbd5c61942b4a3f663f9588bf4
supervisor-general-worker reviewed-implementer-result-integrated branches[1] 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-general-worker cleanup-result-consumed fixture 700f434932b43a95413b7da1f92186ad9fc8a17fc4b68bece9c43e1a3097d882
supervisor-notifications routine-results-no-director fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications routine-results-no-director head 3ea7e6ea934603a4d373d9948e58637adb1c2e72f3f8bbf3c35c3f8fabd26d8b
supervisor-notifications merge-ready-only-merge-ask fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications merge-ready-only-merge-ask head cbb8cdc4799d4100caf358695c2c8d39ba723fb789634d09e7c0bd0830cce912
supervisor-notifications owner-blocker-reaches-director fixture 1367b0f6cb327d835f1a57bd3210c9565d5760ce01a6c921426dfdbd1e616f96
supervisor-notifications owner-blocker-reaches-director head 3ea7e6ea934603a4d373d9948e58637adb1c2e72f3f8bbf3c35c3f8fabd26d8b
supervisor-notifications gh785-ended-worker-replay fixture 45115ee94d31fa3a1a4c4a608cd9caae2c24d19d6402a6802382a797a5ae9006
supervisor-notifications gh785-ended-worker-replay head 78ffa79f477d6811cf857fae0997e3b91dff7f19c26399d12d60123e7dbe4b0a
worker-uncertain-send queued-timeout-sent-once fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
worker-uncertain-send reviewer-queued-timeout-sent-once fixture 4a3473e74902878cfa6e55d0a388abd34e977c61bab2c7455781441b16d14917
worker-uncertain-send reviewer-queued-timeout-sent-once head b06a7b1961826e5c5af18e7f7c2720077f7b0776a6f54b7cfe99f251a580f051
worker-uncertain-send blocked-refusal-sent-again fixture d62e648fb7da7209de833069a58585c615e69ba400878838ef585197d6837050
```
