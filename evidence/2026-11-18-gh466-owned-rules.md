# gh466 / #640: a role step owns its role duty

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch .agents/skills/commit/SKILL.md
Removed: nothing deleted; incident: lane gh593 blocked agents/shaper.md step 3 twice as restating roles `#acceptance-shaper-repair` (finding lines 2026-11-06T06:17:31Z, 06:56:43Z), false by owner ruling 2026-11-06.

Suite: evals/owned-rules (cases and grading: its suite.json). Base: ee42108a.

## Runs

- Smoke 20261118T190043Z-b637e2 (1 run, head 93439b81): reviewer-role-step-own-duty FAIL both kits; the head dropped the worker.md restatement and blocked only on a fixture criterion that duplicated AGENTS.md (fixture fixed, 82741171). reviewer-role-restates-skill PASS both.
- 20261118T191648Z-33762c (3 runs, head 82741171): reviewer-role-step-own-duty base 0/3 (each run: `Owner:` docs/specs/roles.md `restated: agents/worker.md`, `Verdict: blocking`), head 2/3; the failed head run blocked only as `prose-duty` (the step was a mechanical changelog duty) and named the role-duty exception for the duplicated-rule. Case caused it: the train fixture's step is now a judgment duty (ask the supervisor before breaking a command's output). reviewer-role-restates-skill (held-out) base 2/3, head 3/3.
- 20261118T203026Z-bd8a26 (3 runs, head 97d487f9): unreliable, worktrees removed mid-run (#1011); rerun whole as 7fc8e4.
- 20261118T214141Z-7fc8e4 (3 runs, head 60beaa66, no sandbox failure): reviewer-role-step-own-duty base 0/3, head 3/3; reviewer-role-restates-skill (held-out) base 3/3, head 2/3 (failing head run blocks the duplicated rule and writes `Owners: none`, reading the fixture AGENTS.md's owner list as ADR or AGENTS.md only).
- 20261118T204137Z-027c43 (3 runs, head 97d487f9, no sandbox failure): reviewer-role-step-own-duty base 0/3 (each blocks with `Owner:` docs/specs/roles.md `restated: agents/worker.md`), head 3/3 (`Verdict: clear`).
- 20261118T204818Z-3087a4 (1 run): reviewer-role-restates-skill base PASS, head FAIL (`Owner:` field without the skill line).

## check-owner-field (#466)

The writer search was skipped: of the eval runs of implementer-help-owned-rule (20261118T190043Z-b637e2, 20261118T191648Z-33762c), every failing run on both kits never opened the code-review skill and wrote no column-0 Owner field. The real reports below show the same. `scripts/check-owner-field` refuses a branch commit, from the check's own commit on, whose message carries no Owner field. It forces the declaration; it cannot tell whether the search ran or whether a restatement remains.

Proof (tests/gate/kit/owner_field.py, run as `python3 tests/gate/kit/owner_field.py <scenario>`): the message of real commit 6391de1b (lane gh906, #977, its writer's report also without the field) after the check is refused, naming the commit and the fix; an older lane commit, before the main merge that brought the check, passes with the notice line; `git commit --amend` adding `Owners: none`, and `git rebase -i --rebase-merges <sha>^` with `reword` on an older commit, each turn it green.

## Writer reports without the Owner field (#466 lanes)

Source: Pi sessions ~/.pi/agent/sessions/<dir>/<file>.jsonl of implementer and corrector panes on the lanes of the 144 duplicated-rule finding lines; each session's last `herdr-say --parent` call (over 200 chars) read by `octo-feather-lane fields -`. Sessions: 254. Owner lines: 90. `Owners: none`: 80. No Owner field at all ('report names no owned rule'): 74. Malformed: 10. The 84 without a usable field:

- gh118 --home-exedev-src-octo-feather-gh118-corrector--/2026-10-23T02-27-05-933Z_4a4e551d-f4e7-470b-ad44-16f8151544f6.jsonl (Corrector): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w1--/2026-10-23T21-56-53-764Z_75059a3c-58f7-4784-a501-18af6f35068c.jsonl (Implementer): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w2--/2026-10-23T22-25-30-935Z_4011e38e-f4c5-4893-9c79-d146978dabd3.jsonl (Implementer): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w2--/2026-10-24T03-23-26-074Z_6bff019e-c8a2-4aaa-b7d6-6935ff3433b5.jsonl (Implementer): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w2--/2026-10-24T04-18-33-591Z_c340d671-e708-4a06-8c53-b8b035334841.jsonl (Implementer): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w3--/2026-10-23T22-33-36-376Z_6c7f40b3-5047-4b05-bdd1-f8233a73052e.jsonl (Implementer): no Owner field
- gh121 --home-exedev-src-octo-feather-gh121-w4--/2026-10-23T23-18-15-630Z_4c03de4b-0155-4191-8731-68c3ea00f3ab.jsonl (Implementer): no Owner field
- gh127 --home-exedev-src-octo-feather-gh127-w405--/2026-10-29T17-55-00-536Z_d7d37b23-ea0d-4845-967f-2c24850cf75d.jsonl (Implementer): no Owner field
- gh127 --home-exedev-src-octo-feather-gh127-w410--/2026-10-29T19-36-35-208Z_5bc6cf6c-fddd-4111-89c6-2b1300862261.jsonl (Implementer): no Owner field
- gh136 --home-exedev-src-octo-feather-gh136-w178--/2026-10-26T19-01-26-833Z_64bbaa60-f3d1-43f8-9ddb-08cf553c60f7.jsonl (Implementer): no Owner field
- gh136 --home-exedev-src-octo-feather-gh136-w243b--/2026-10-27T23-38-32-232Z_edd222ef-d22f-4930-9624-8a815835adc1.jsonl (Implementer): no Owner field
- gh149 --home-exedev-src-octo-feather-gh149-w185--/2026-10-26T22-28-46-529Z_5fa207c5-6220-4e70-afae-57fb91d30dc8.jsonl (Implementer): malformed
- gh149 --home-exedev-src-octo-feather-gh149-w189--/2026-10-27T20-36-30-654Z_d03fd31b-536d-4021-81a9-36343ea0414d.jsonl (Implementer): malformed
- gh149 --home-exedev-src-octo-feather-gh149-w189--/2026-10-27T23-47-23-654Z_6b68467d-a3db-4880-9e97-496dfc6e1539.jsonl (Implementer): malformed
- gh157 --home-exedev-src-octo-feather-gh157-corrector--/2026-10-25T01-00-27-882Z_7a4c65fe-48c8-4d3a-8151-dcbab2de0a47.jsonl (Corrector): no Owner field
- gh167 --home-exedev-src-octo-feather-gh167-w172--/2026-10-26T21-59-56-978Z_b85847b9-7d60-4d25-b88b-d99890c2ae7b.jsonl (Implementer): malformed
- gh167 --home-exedev-src-octo-feather-gh167-w173--/2026-10-27T06-42-26-581Z_9fb87017-073e-4a4c-83f6-9f3ccd8ba6f5.jsonl (Implementer): no Owner field
- gh203 --home-exedev-src-octo-feather-gh203-w240--/2026-10-27T22-10-43-539Z_797c445e-38b5-4397-adfc-76a203a34882.jsonl (Implementer): no Owner field
- gh206 --home-exedev-src-octo-feather-gh206-w397--/2026-10-29T17-43-36-815Z_4a91a9d0-3207-47e4-a426-877ca91ec277.jsonl (Implementer): no Owner field
- gh206 --home-exedev-src-octo-feather-gh206-w399--/2026-10-29T18-27-35-413Z_bcbbef50-6371-47c0-8b81-4e3d5a0953e1.jsonl (Implementer): malformed
- gh225 --home-exedev-src-octo-feather-gh225-w244--/2026-10-27T21-38-34-110Z_4fd66cb7-2afa-46c7-a6dd-99b85b534fa1.jsonl (Corrector): no Owner field
- gh256 --home-exedev-src-octo-feather-gh256-w262--/2026-10-28T02-51-22-201Z_45c839ad-24e2-425f-9602-dbe717c2f37b.jsonl (Implementer): no Owner field
- gh256 --home-exedev-src-octo-feather-gh256-w263--/2026-10-28T02-52-05-067Z_83495b8a-264f-4b56-beef-6a003d755393.jsonl (Implementer): no Owner field
- gh261 --home-exedev-src-octo-feather-gh261-w362--/2026-10-29T04-48-34-187Z_bde431c3-93ad-478a-a05a-53af8efb1411.jsonl (Corrector): no Owner field
- gh269 --home-exedev-src-octo-feather-gh269-w269--/2026-10-28T02-35-57-548Z_b1e99592-92f7-4696-8a58-bd23886dcc4d.jsonl (Corrector): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-w459--/2026-10-30T00-18-04-661Z_3b1b7ea9-3c3e-4142-b62b-187e800813b2.jsonl (Implementer): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-w460--/2026-10-30T04-48-09-026Z_ab88ba1d-4fba-4954-8014-1ea22f87c7fc.jsonl (Implementer): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-w461--/2026-10-30T05-32-24-027Z_1e14ac16-2fad-4e49-93e5-37a02ca4b0dd.jsonl (Implementer): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-wfix--/2026-10-30T08-17-33-014Z_b67154fa-4fa2-479e-b486-4e56ec7bfa07.jsonl (Implementer): malformed
- gh422 --home-exedev-src-octo-feather-gh422-wfix--/2026-10-30T15-41-22-981Z_ee7b4739-f06e-4444-a9bc-d40ef7a0d8bd.jsonl (Implementer): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-wfix--/2026-10-30T17-12-06-430Z_2306aa79-12d0-4e8d-ac43-46ed153ade76.jsonl (Implementer): no Owner field
- gh422 --home-exedev-src-octo-feather-gh422-wfix--/2026-10-30T17-45-49-907Z_3dc988fd-72f3-48bc-b871-8f728a4f7428.jsonl (Implementer): no Owner field
- gh436 --home-exedev-src-octo-feather-gh436-w437--/2026-10-29T21-43-28-278Z_0819eed0-d700-4b1f-a8df-c7776794151a.jsonl (Implementer): malformed
- gh479 --home-exedev-src-octo-feather-gh479-w532--/2026-11-04T15-50-28-454Z_349d94ff-46da-44e3-8905-ec0f66bacf94.jsonl (Implementer): no Owner field
- gh493 --home-exedev-src-octo-feather-gh493-impl--/2026-11-03T16-36-55-665Z_ef03ef19-25ea-4df4-899c-da1e52745dd9.jsonl (Implementer): no Owner field
- gh503 --home-exedev-src-octo-feather-gh503-explore--/2026-11-04T15-46-53-774Z_350986f2-a6cd-462f-bd1d-61e57d5d46fb.jsonl (Implementer): malformed
- gh503 --home-exedev-src-octo-feather-gh503-t1--/2026-11-04T16-02-13-158Z_da03a2fb-0bd2-4ddf-984a-d68dd5faf875.jsonl (Implementer): no Owner field
- gh503 --home-exedev-src-octo-feather-gh503-t3--/2026-11-04T18-38-20-670Z_79a90d65-0ffc-4392-98ba-82d78e11547c.jsonl (Implementer): no Owner field
- gh503 --home-exedev-src-octo-feather-gh503-t5--/2026-11-04T21-47-35-916Z_fd9eac89-c66a-49f2-bb23-4f2c8e6fdc0a.jsonl (Implementer): no Owner field
- gh503 --home-exedev-src-octo-feather-gh503-t6--/2026-11-05T03-08-05-528Z_7f0fbdce-99c6-4922-8533-05ee0cf45f87.jsonl (Implementer): no Owner field
- gh520 --home-exedev-src-octo-feather-gh520-w527--/2026-11-04T17-16-15-643Z_e35f8bbf-c639-4f06-b44e-41020abae00c.jsonl (Implementer): no Owner field
- gh520 --home-exedev-src-octo-feather-gh520-w527--/2026-11-04T21-30-25-489Z_f043c0e2-1910-4986-88b6-abcd1f1b90dc.jsonl (Implementer): no Owner field
- gh520 --home-exedev-src-octo-feather-gh520-w528--/2026-11-04T18-43-28-199Z_9a5b3b9c-d6f1-405b-baac-ad859fe17086.jsonl (Implementer): no Owner field
- gh520 --home-exedev-src-octo-feather-gh520-w529--/2026-11-04T18-03-55-323Z_a8d5609d-7304-480e-b9f2-2f10454a66d8.jsonl (Implementer): no Owner field
- gh520 --home-exedev-src-octo-feather-gh520-w529--/2026-11-04T18-46-39-233Z_ebfe496a-61e2-464e-ac1b-b6fdb195a0d1.jsonl (Implementer): no Owner field
- gh557 --home-exedev-src-octo-feather-gh557-w558--/2026-11-04T21-47-18-203Z_45d06535-bb04-4f9f-8a3b-4a2899d04601.jsonl (Implementer): no Owner field
- gh568 --home-exedev-src-octo-feather-gh568-corrector--/2026-11-06T01-24-25-346Z_1127b1aa-c216-4586-8593-8a5415481d83.jsonl (Corrector): no Owner field
- gh576 --home-exedev-src-octo-feather-gh576-w689--/2026-11-06T18-18-53-964Z_20492784-f09b-478c-8fb8-452c56d22f0b.jsonl (Implementer): no Owner field
- gh576 --home-exedev-src-octo-feather-gh576-w689--/2026-11-08T22-09-00-280Z_545b3c1e-dd86-4c50-9016-03515cf9d817.jsonl (Implementer): no Owner field
- gh577 --home-exedev-src-octo-feather-gh577-w606--/2026-11-05T20-52-44-998Z_6ad50e00-8735-4645-b5f2-7e3bb132fa51.jsonl (Implementer): no Owner field
- gh577 --home-exedev-src-octo-feather-gh577-w609--/2026-11-05T22-27-20-546Z_e06e4b9a-4466-46c3-a62f-c0564e8b9214.jsonl (Implementer): no Owner field
- gh577 --home-exedev-src-octo-feather-gh577-w610--/2026-11-05T22-27-25-445Z_6f9e8210-a53d-46a8-ad45-83775a0845ef.jsonl (Implementer): no Owner field
- gh577 --home-exedev-src-octo-feather-gh577-w611--/2026-11-05T22-42-43-646Z_c93b0b8a-bd14-4ac0-8eb2-2d6ee6947103.jsonl (Implementer): no Owner field
- gh586 --home-exedev-src-octo-feather-gh586-w591--/2026-11-05T21-13-50-668Z_d662929d-f7c4-46ed-bdbb-061c24ba94a0.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-673--/2026-11-06T17-34-27-661Z_6ed1fd9f-8f3a-4b86-b58c-00e18e68a369.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-676--/2026-11-06T22-33-17-483Z_f46e3678-d894-49d8-ab05-ee963bd4624d.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-679--/2026-11-06T22-33-22-879Z_4c9f1b74-1ce9-4303-997c-94d518065593.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-681--/2026-11-07T03-57-19-494Z_77f37081-03fd-44a0-ae4c-2c968660cb52.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-audit-main--/2026-11-12T17-07-19-084Z_aa745def-dfb0-4556-bdc3-7c470b6a327e.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-code-preserve--/2026-11-12T02-16-20-544Z_6c781e2d-e005-4c1a-bcb4-b727a112f03c.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-main77--/2026-11-08T23-42-11-823Z_b5b5aa12-c6f7-4a30-82c0-5cecd74f7922.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-native-consumer--/2026-11-12T02-03-43-805Z_d98985e9-b3b9-402d-ad53-d13b212d5bca.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-qa18--/2026-11-09T18-31-03-903Z_3b044a3d-c904-454a-bf92-725b02001a9e.jsonl (Implementer): no Owner field
- gh653 --home-exedev-src-octo-feather-gh653-semantic-a--/2026-11-09T03-58-29-207Z_443588e5-4b49-4e93-a586-7b5f13e310fe.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-874--/2026-11-13T09-42-22-835Z_55a0a45c-c387-4290-87df-14ffa69bc283.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-876--/2026-11-13T09-42-32-214Z_aa3dbae4-8721-487f-94f2-253efae684f9.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-878--/2026-11-13T09-42-42-229Z_73cf3c68-3a85-4f92-be99-142adc2fd456.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-883--/2026-11-13T10-38-52-015Z_da7ac9d5-23b3-4d03-b89c-4c2b81fba6dc.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-main2--/2026-11-17T01-28-21-363Z_7ef76302-80b1-4ee7-97a9-4834f9bae8c6.jsonl (Implementer): no Owner field
- gh840 --home-exedev-src-octo-feather-gh840-main3--/2026-11-17T22-29-05-256Z_7c1026b7-c8a7-42af-a47b-d302166f8389.jsonl (Implementer): malformed
- gh840 --home-exedev-src-octo-feather-gh840-round--/2026-11-18T03-00-09-976Z_ef165a7d-0d3b-4d2a-a3cb-1037aeb2f658.jsonl (Implementer): malformed
- gh851 --home-exedev-src-octo-feather-gh851-961--/2026-11-17T18-29-19-225Z_df1668f9-0afe-4b51-bb83-2d3cc3794dbf.jsonl (Implementer): no Owner field
- gh891 --home-exedev-src-octo-feather-gh891-893--/2026-11-13T21-50-07-237Z_8371125f-a272-4bd4-bfdc-c3f25802d7d9.jsonl (Implementer): no Owner field
- gh891 --home-exedev-src-octo-feather-gh891-895--/2026-11-13T22-46-54-351Z_a770909e-8715-44d9-ba6b-aaacd28c063b.jsonl (Implementer): no Owner field
- gh921 --home-exedev-src-octo-feather-gh921-926--/2026-11-17T01-18-17-286Z_4ebee916-bbed-4c84-b316-156e520b2fdf.jsonl (Implementer): no Owner field
- gh921 --home-exedev-src-octo-feather-gh921-927--/2026-11-17T02-26-31-750Z_8fea363b-bf1b-492f-9258-ef5152fd0d1b.jsonl (Implementer): no Owner field
- gh930 --home-exedev-src-octo-feather-gh930-933--/2026-11-17T03-08-32-485Z_690ab363-722f-4e91-a76f-89ccdf0a3be7.jsonl (Implementer): no Owner field
- gh930 --home-exedev-src-octo-feather-gh930-934--/2026-11-17T03-04-38-499Z_d6c35530-b7d1-4914-92cd-84f0552f1686.jsonl (Implementer): no Owner field
- gh930 --home-exedev-src-octo-feather-gh930-main--/2026-11-17T16-04-23-925Z_afa02c98-f8ce-4887-ae6d-aad03143e1db.jsonl (Implementer): no Owner field
- gh941 --home-exedev-src-octo-feather-gh941-951--/2026-11-17T15-48-20-493Z_3da81a67-9c4b-46fc-a3d9-495eb8579d2a.jsonl (Implementer): no Owner field
- gh941 --home-exedev-src-octo-feather-gh941-957--/2026-11-17T17-54-39-885Z_2dd6c862-a270-49c5-a566-d6b2b2c5229a.jsonl (Implementer): no Owner field
- gh941 --home-exedev-src-octo-feather-gh941-965--/2026-11-17T19-22-10-563Z_86a9c2cf-1042-49f0-b286-bac52379a0fe.jsonl (Implementer): no Owner field
- gh972 --home-exedev-src-octo-feather-gh972-974--/2026-11-18T04-06-40-924Z_2cd842a4-48d1-494f-a7ec-6c38d5c6fc28.jsonl (Implementer): no Owner field
- gh972 --home-exedev-src-octo-feather-gh972-975--/2026-11-18T04-06-46-887Z_a996f157-addf-4436-9c19-7837634a560b.jsonl (Implementer): no Owner field
