"""The split's tables (ticket #1333, design: #1274 comment 7232729794, sections 1 to 3).

Read by split.py (the codemod) and check.py (the machine checks). A def of the hub the MODULE_OF table lacks is
placed by split.py's rule (split.place) and printed.
"""

# Module names: the design's lane_tickets, lane_reflect and lane_report are lane_ticketing, lane_reflection and
# lane_reporting here: tests/gate/kit holds test modules of the design's names, which tests import by bare name and
# pytest's pythonpath and basedpyright's extraPaths would resolve to scripts/ (supervisor call, #1333).
# Section 1, the cut: each module's defs, as the design's table lists them (at main 95353ff3).
CUT = {
    "lane_cli": "Refuse Unchecked lanes_dir state_dir lane_name pr_number take_repo no_traceback q reflect_module",
    "lane_reflection": "sha256 director_source_args cmd_archive unreflect rollback reflect_lane reflect_director "
                    "file_corrections cmd_intake cmd_reflect",
    "lane_review": "owner_lines cmd_fields cmd_verdict review_rounds merge_resolution cmd_resolution post_comment "
                   "qa_module calibration cmd_judge",
    "merge_ask": "cmd_merge_ask pr_commits",
    "ci_start": "cmd_ci_start workflow_jobs ci_full_run",
    "lane_ticketing": "rule_why_not Anchors specs_dir spec_anchors criteria_items structure check_body skills_named "
                    "skills_rule_since by_change implementer_offered skills_fails creates_why_not gate_free_module "
                    "created not_demo Surface program_words script_arg invocation strip_subst cmd_tickets cmd_done "
                    "cmd_ticket iso_time ticket_notes cmd_seam handoff_module cmd_skills skills_check",
    "pi_sessions": "sessions_dir skill_operand shell_reads tool_reads call_names SessionReach session_reach",
    "lane_reporting": "spend_lane spend_line spend_time spend_record openrouter_key openrouter_usage cmd_spend "
                   "herdr_agents pending_gates check_results owner_caught director_reflection RoleReach skill_reach "
                   "ReportSources report_lane cmd_report",
    "post_merge": "show_line run_routine cmd_stale take_opt pm_show pm_wait cmd_post_merge merge_lane merge_allowed "
                  "cmd_merge cmd_archive_lane archive_waits pm_unit_start pm_unit_run",
    "start_lane": "cmd_start",
}
MODULE_OF = {name: mod for mod, names in CUT.items() for name in names.split()}

# Modules that exist before the split (owner decision 1: the entry goes where its logic is). Their code keeps its
# format check: code moved into them is formatted by ruff and carries line noqa only (supervisor ruling, #1333).
EXISTING = ("post_merge", "merge_ask", "start_lane")
NEW = ("lane_cli", "lane_ticketing", "lane_reporting", "lane_review", "lane_reflection", "pi_sessions", "ci_start")

# Moved from an existing module into lane_cli (design section 1: lane_cli holds `kit_install` from post_merge.py).
FROM_EXISTING = {"kit_install": ("post_merge", "lane_cli")}

# Section 3, launch path: these run Path(__file__).resolve() as the command.
LAUNCH = ("pm_unit_start", "pm_unit_run", "cmd_post_merge")
LAUNCH_FROM = "Path(__file__).resolve()"
LAUNCH_TO = 'Path(__file__).resolve().parent / "octo-feather-lane"'

# Section 3, the hub's own docstring: these read __doc__; the help is lane_cli.help_doc() (section 2).
DOC_READERS = ("cmd_start",)

# Section 2, help: each chunk of the hub's docstring by the line it starts with, its owning module and its name, in
# today's order. A chunk runs to the next one's first line.
HELP = [
    ("octo-feather-lane: lane bookkeeping", "lane_cli", "header"),
    ("  octo-feather-lane archive NAME ", "lane_reflection", "archive"),
    ("  octo-feather-lane reflect NAME ", "lane_reflection", "reflect"),
    ("Archive of a merged lane ", "post_merge", "archive-merged"),
    ("  octo-feather-lane verdict PR HEAD", "lane_review", "verdict-usage"),
    ("  octo-feather-lane merge-ask PR ", "merge_ask", "merge-ask-usage"),
    ("  octo-feather-lane ci-start PR ", "ci_start", "ci-start-usage"),
    ("  octo-feather-lane judge PR QUESTION", "lane_review", "judge"),
    ("`merge-ask` reads through ", "merge_ask", "merge-ask"),
    ("  octo-feather-lane tickets PARENT ", "lane_ticketing", "tickets"),
    ("  octo-feather-lane spend          the spend", "lane_reporting", "spend"),
    ("  octo-feather-lane intake ", "lane_reflection", "intake"),
    ("  octo-feather-lane report ", "lane_reporting", "report"),
    ("  octo-feather-lane merge PR HEAD", "post_merge", "merge"),
    ("  octo-feather-lane start TICKET", "start_lane", "start"),
    ("One subcommand per function", "lane_cli", "footer"),
]

# The justfile's install-check loads the lane script by path for kit_install (design section 3: read it from
# lane_cli.py). One line, exact text.
JUSTFILE_FROM = ('iu.spec_from_loader("octo_feather_lane", im.SourceFileLoader("octo_feather_lane", '
                 'os.path.join(root, "scripts", "octo-feather-lane")))')
JUSTFILE_TO = ('iu.spec_from_loader("lane_cli", im.SourceFileLoader("lane_cli", '
               'os.path.join(root, "scripts", "lane_cli.py")))')

# Defs another module imports whose hub annotations leave part of their type unknown (bare generics, an unannotated
# parameter): read as `NAME = cast(TYPE, MODULE.NAME)`, TYPE the hub's own annotations with Unknown written Any, so the
# importer types them as the hub did (no reportUnknownVariableType on an import the hub did not need).
TYPED = {
    "no_traceback": "Callable[[Any], Callable[[list[str]], int]]",
    "herdr_agents": "Callable[[], list[dict[Any, Any]]]",
    "report_lane": "Callable[[Path, list[dict[Any, Any]] | None, str | None, Any, list[str], list[Any], ReportSources], "
                   "list[str]]",
}

# post_merge.py's docstring interface list names kit_install(), which moves to lane_cli.py: that line says where it
# now lives (a stale interface list is reader load). Exact text, once.
PM_DOC_FROM = """    kit_install(), top(), git_here(*args), records(lanes), now(): the install step 3 moves, the
        director's checkout, git in the current directory, the records' dir, a record's time.
"""
PM_DOC_TO = """    kit_install() (lane_cli.py's, imported here), top(), git_here(*args), records(lanes), now():
        the install step 3 moves, the director's checkout, git in the current directory, the
        records' dir, a record's time.
"""
