#!/usr/bin/env python3
"""Session boundaries, driven the way the hooks drive them.

Every fix to this bookkeeping so far was checked by reading, and every one of
them shipped a regression within a day. So nothing here inspects a function:
each test runs `archive-session.py` and `due.py` as processes, with a hook
event on stdin, against a vault built in a temporary folder. `HOME` is moved
there too, so `sweep()` sees the transcripts this file wrote and not the
machine's own.

    python3 -m unittest discover -s tests

No dependencies beyond the standard library.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ARCHIVE = SCRIPTS / "archive-session.py"
DUE = SCRIPTS / "due.py"


class Vault(unittest.TestCase):
    """A vault, a working folder and sessions writing transcripts into it."""

    def setUp(self) -> None:
        # Resolved: on macOS the temporary folder sits behind a symlink, and a
        # slot named from the event's cwd would not be the one a command
        # running in that folder looks up.
        self.root = Path(tempfile.mkdtemp(prefix="morf-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.home = self.root / "home"
        self.vault = self.root / "vault"
        self.work = self.root / "work" / "sample"
        self.projects = self.home / ".claude" / "projects" / "-work-sample"
        for path in (self.vault, self.work, self.projects):
            path.mkdir(parents=True)

    # ----- the machinery under test, run as the hooks run it -----

    def run_script(self, script: Path, *args: str, event: dict | None = None,
                   session: str = "") -> str:
        environment = dict(os.environ, HOME=str(self.home), MORF_HOME=str(self.vault))
        environment.pop("CLAUDE_CODE_SESSION_ID", None)
        if session:
            environment["CLAUDE_CODE_SESSION_ID"] = session
        done = subprocess.run([sys.executable, str(script), *args],
                              input=json.dumps(event or {}), text=True,
                              capture_output=True, env=environment,
                              cwd=str(self.work), check=False)
        self.assertEqual(done.returncode, 0, f"{script.name} failed: {done.stderr}")
        return done.stdout.strip()

    def start(self, session: str) -> str:
        """SessionStart, as the hook fires it on start, resume and compact."""
        return self.run_script(ARCHIVE, event={"session_id": session,
                                               "cwd": str(self.work),
                                               "transcript_path": str(self.transcript(session))})

    def end(self, session: str) -> None:
        """SessionEnd."""
        self.run_script(ARCHIVE, "--ended", event={"session_id": session,
                                                   "cwd": str(self.work)})

    def handoff(self, session: str) -> str:
        return self.run_script(ARCHIVE, "--handoff", session=session)

    def debts(self) -> str:
        return self.run_script(DUE, "--prompt", event={"cwd": str(self.work)})

    # ----- the conversation on disk -----

    def transcript(self, session: str) -> Path:
        return self.projects / f"{session}.jsonl"

    def write(self, session: str, lines: int) -> None:
        """Grows the session's transcript to `lines`, as Claude Code does."""
        path = self.transcript(session)
        held = path.read_text(encoding="utf-8").count("\n") if path.exists() else 0
        with path.open("a", encoding="utf-8") as handle:
            for number in range(held + 1, lines + 1):
                handle.write(json.dumps({"turn": number}) + "\n")

    def slug(self, session: str) -> str:
        return f"{date.today():%y%m%d}-{session[:4]}"

    def state(self) -> dict:
        key = str(self.work).strip("/").replace("/", "-")
        return json.loads((self.vault / "Memory" / ".state" / f"{key}.json")
                          .read_text(encoding="utf-8"))

    def mark_of(self, session: str) -> int:
        return self.state()["sessions"][self.slug(session)]["mark"]

    def observe(self, ref: str, project: str = "sample") -> None:
        """Writes the stretch up as an observation, citing it as its source."""
        inbox = self.vault / "Memory" / project / "L0.md"
        inbox.parent.mkdir(parents=True, exist_ok=True)
        with inbox.open("a", encoding="utf-8") as handle:
            handle.write(f"- hit:1 use:0 something happened ({ref})\n")


class ProgressSurvivesResume(Vault):
    """Defect: registering a session wrote its mark back to zero."""

    def test_mark_is_kept_across_a_resume(self) -> None:
        session = "aaaa1111-0000-0000-0000-000000000000"
        self.write(session, 100)
        self.start(session)
        self.assertEqual(self.handoff(session), f"s:{self.slug(session)}#1-100")
        self.assertEqual(self.mark_of(session), 100)

        self.start(session)                       # resume, or a compaction
        self.assertEqual(self.mark_of(session), 100,
                         "the resume wiped the mark /handoff had just written")

    def test_a_handed_off_stretch_is_not_owed_after_a_resume(self) -> None:
        """The incident: handed off at 634, back three hours later as a debt from 1."""
        session, later = ("aaaa2222-0000-0000-0000-000000000000",
                          "bbbb2222-0000-0000-0000-000000000000")
        self.write(session, 634)
        self.start(session)
        self.handoff(session)
        self.observe(f"s:{self.slug(session)}#1-634")

        self.write(session, 961)
        self.start(session)                       # the resume that wiped the mark
        self.end(session)
        self.write(later, 3)
        message = self.start(later)               # and the start that read the wiped mark

        self.assertNotIn("#1-961", message + self.debts(),
                         "the whole session was owed again from line 1")
        self.assertIn(f"s:{self.slug(session)}#635-961", message)

    def test_the_next_stretch_starts_after_the_mark(self) -> None:
        session = "aaaa3333-0000-0000-0000-000000000000"
        self.write(session, 634)
        self.start(session)
        self.handoff(session)
        self.write(session, 961)
        self.start(session)
        self.assertEqual(self.handoff(session), f"s:{self.slug(session)}#635-961")

    def test_a_new_session_in_the_slot_starts_at_zero(self) -> None:
        first, second = ("aaaa4444-0000-0000-0000-000000000000",
                         "bbbb4444-0000-0000-0000-000000000000")
        self.write(first, 50)
        self.start(first)
        self.handoff(first)
        self.write(second, 20)
        self.start(second)
        self.assertEqual(self.mark_of(second), 0)
        self.assertEqual(self.handoff(second), f"s:{self.slug(second)}#1-20")


class HandoffAnswersItsCaller(Vault):
    """Defect: /handoff answered for whatever session last touched the folder."""

    def test_each_session_gets_its_own_reference(self) -> None:
        first, second = ("cccc1111-0000-0000-0000-000000000000",
                         "dddd1111-0000-0000-0000-000000000000")
        self.write(first, 40)
        self.start(first)
        self.write(second, 15)
        self.start(second)                        # registered last, and used to win

        self.assertEqual(self.handoff(first), f"s:{self.slug(first)}#1-40")
        self.assertEqual(self.handoff(second), f"s:{self.slug(second)}#1-15")

    def test_the_second_session_does_not_bury_the_first(self) -> None:
        first, second = ("cccc2222-0000-0000-0000-000000000000",
                         "dddd2222-0000-0000-0000-000000000000")
        self.write(first, 40)
        self.start(first)
        self.handoff(first)
        self.write(second, 15)
        self.start(second)
        self.handoff(second)
        self.assertEqual(self.mark_of(first), 40)
        self.assertEqual(self.mark_of(second), 15)

    def test_a_running_session_is_not_reported_as_cut_short(self) -> None:
        first, second = ("cccc3333-0000-0000-0000-000000000000",
                         "dddd3333-0000-0000-0000-000000000000")
        self.write(first, 40)
        self.start(first)
        self.write(second, 5)
        message = self.start(second)
        self.assertNotIn("unprocessed", message,
                         "a session still writing its transcript was swept as dead")
        self.assertNotIn("handoff: the stretch", self.debts())

    def test_a_session_that_ended_is_swept_from_its_mark(self) -> None:
        first, second = ("cccc4444-0000-0000-0000-000000000000",
                         "dddd4444-0000-0000-0000-000000000000")
        self.write(first, 40)
        self.start(first)
        self.handoff(first)                       # mark 40
        self.write(first, 90)                     # and then it was killed
        self.end(first)

        message = self.start(second)
        self.assertIn(f"s:{self.slug(first)}#41-90", message)
        self.assertNotIn("#1-90", message)
        self.assertIn(f"s:{self.slug(first)}#41-90", self.debts())

    def test_a_silent_session_counts_as_ended_without_the_hook(self) -> None:
        """A hard stop never reaches SessionEnd; the sweep must still happen."""
        first, second = ("cccc5555-0000-0000-0000-000000000000",
                         "dddd5555-0000-0000-0000-000000000000")
        self.write(first, 30)
        self.start(first)
        stale = self.transcript(first)
        os.utime(stale, (0, 0))                   # untouched since the epoch

        self.assertIn(f"s:{self.slug(first)}#1-30", self.start(second))

    def test_two_dead_sessions_both_keep_their_stretch(self) -> None:
        first, second, third = ("cccc6666-0000-0000-0000-000000000000",
                                "dddd6666-0000-0000-0000-000000000000",
                                "eeee6666-0000-0000-0000-000000000000")
        for session, lines in ((first, 30), (second, 12)):
            self.write(session, lines)
            self.start(session)
            self.end(session)

        self.start(third)
        owed = self.debts()
        self.assertIn(f"s:{self.slug(first)}#1-30", owed)
        self.assertIn(f"s:{self.slug(second)}#1-12", owed)

    def test_a_handoff_with_nothing_new_hands_back_no_reference(self) -> None:
        session = "cccc7777-0000-0000-0000-000000000000"
        self.write(session, 20)
        self.start(session)
        self.handoff(session)
        self.assertNotIn("#", self.handoff(session), "an empty stretch was given a reference")
        self.assertEqual(self.mark_of(session), 20)

    def test_a_folder_with_no_session_says_so(self) -> None:
        self.assertIn("no registered session", self.handoff(""))

    def test_without_an_id_the_session_writing_now_is_the_caller(self) -> None:
        """The environment carries the id; where it does not, the file does."""
        quiet, busy = ("cccc8888-0000-0000-0000-000000000000",
                       "dddd8888-0000-0000-0000-000000000000")
        self.write(quiet, 40)
        self.start(quiet)
        self.write(busy, 15)
        self.start(busy)
        os.utime(self.transcript(quiet), (1, 1))
        os.utime(self.transcript(busy), (2, 2))

        self.assertEqual(self.handoff(session=""), f"s:{self.slug(busy)}#1-15")


class SessionsAreNotDays(Vault):
    """A conversation is one session however many dates it spans."""

    def test_a_resume_past_midnight_keeps_the_slug_and_the_mark(self) -> None:
        session = "7777aaaa-0000-0000-0000-000000000000"
        yesterday = "260101-7777"
        self.write(session, 80)
        key = str(self.work).strip("/").replace("/", "-")
        state = self.vault / "Memory" / ".state"
        state.mkdir(parents=True, exist_ok=True)
        (state / f"{key}.json").write_text(json.dumps({"sessions": {yesterday: {
            "transcript": str(self.transcript(session)), "mark": 55}}}), encoding="utf-8")

        self.start(session)                       # the same conversation, a new day
        held = self.state()["sessions"]
        self.assertEqual(list(held), [yesterday], "one conversation became two sessions")
        self.assertEqual(held[yesterday]["mark"], 55)
        self.assertEqual(self.handoff(session), f"s:{yesterday}#56-80")

    def test_an_end_for_a_session_that_never_registered_changes_nothing(self) -> None:
        session = "7777bbbb-0000-0000-0000-000000000000"
        self.write(session, 10)
        self.start(session)
        before = self.state()
        self.end("0000ffff-0000-0000-0000-000000000000")
        self.assertEqual(self.state(), before)


class WorkOnceDoneIsNotDoneAgain(Vault):
    """What the sweep leaves behind must not come back every session start."""

    def test_a_settled_stretch_stops_being_reported(self) -> None:
        first, second = ("6666aaaa-0000-0000-0000-000000000000",
                         "5555aaaa-0000-0000-0000-000000000000")
        self.write(first, 30)
        self.start(first)
        self.end(first)
        self.assertIn("unprocessed", self.start(second))
        self.assertIn("pending", json.dumps(self.state()))
        self.assertNotIn("unprocessed", self.start(second), "said twice for one stretch")

        self.observe(f"s:{self.slug(first)}#1-30")
        self.start(second)
        self.assertNotIn("pending", json.dumps(self.state()),
                         "the marker outlived the work it stood for")
        self.assertNotIn("archived and unread", self.debts())

    def test_a_transcript_is_not_copied_again_while_it_stays_the_same(self) -> None:
        first, second = ("6666bbbb-0000-0000-0000-000000000000",
                         "5555bbbb-0000-0000-0000-000000000000")
        self.write(first, 30)
        self.start(first)
        self.end(first)
        self.start(second)

        archived = self.vault / "Memory" / "Transcripts" / self.slug(first) / f"{first}.jsonl"
        archived.write_text("touched\n", encoding="utf-8")
        self.start(second)
        self.assertEqual(archived.read_text(encoding="utf-8"), "touched\n",
                         "an unchanged transcript was copied over again")

    def test_a_record_with_no_transcript_is_not_the_working_folder(self) -> None:
        """`Path("")` is the current folder, and its mtime is not a session's."""
        session = "6666cccc-0000-0000-0000-000000000000"
        self.run_script(ARCHIVE, event={"session_id": session, "cwd": str(self.work),
                                        "transcript_path": ""})
        self.assertIn("transcript not found", self.handoff(session))


class MemoryIsTheEvidence(Vault):
    """A stretch the memory already cites as a source has been read."""

    def test_a_cited_stretch_is_not_owed(self) -> None:
        first, second = ("ffff1111-0000-0000-0000-000000000000",
                         "99991111-0000-0000-0000-000000000000")
        self.write(first, 30)
        self.start(first)
        self.end(first)
        self.start(second)
        self.assertIn("archived and unread", self.debts())

        self.observe(f"s:{self.slug(first)}#1-30")
        self.assertNotIn("archived and unread", self.debts(),
                         "the debt stood for a stretch already written up")

    def test_only_the_uncited_remainder_is_owed(self) -> None:
        first, second = ("ffff2222-0000-0000-0000-000000000000",
                         "99992222-0000-0000-0000-000000000000")
        self.write(first, 90)
        self.start(first)
        self.end(first)
        self.start(second)
        self.observe(f"s:{self.slug(first)}#1-40")
        self.assertIn(f"s:{self.slug(first)}#41-90", self.debts())

    def test_a_stretch_written_up_under_another_project_counts(self) -> None:
        """A worktree is a project by folder name; its observations are not."""
        first, second = ("ffff4444-0000-0000-0000-000000000000",
                         "99994444-0000-0000-0000-000000000000")
        self.write(first, 30)
        self.start(first)
        self.end(first)
        self.start(second)
        self.observe(f"s:{self.slug(first)}#1-30", project="the-real-project")
        self.assertNotIn("archived and unread", self.debts())

    def test_a_marker_left_by_the_earlier_version_clears_the_same_way(self) -> None:
        session = "ffff3333-0000-0000-0000-000000000000"
        self.write(session, 25)
        self.start(session)
        key = str(self.work).strip("/").replace("/", "-")
        ref = f"s:{self.slug(session)}#1-25"
        (self.vault / "Memory" / ".state" / f"{key}.pending").write_text(ref, encoding="utf-8")
        self.assertIn(ref, self.debts())

        self.observe(ref)
        self.assertNotIn("archived and unread", self.debts())


class StateWrittenBeforeTheIndex(Vault):
    """A vault carried over from the version that kept one record per folder."""

    def legacy(self, session: str, mark: int) -> None:
        key = str(self.work).strip("/").replace("/", "-")
        state = self.vault / "Memory" / ".state"
        state.mkdir(parents=True, exist_ok=True)
        (state / f"{key}.json").write_text(json.dumps({
            "slug": self.slug(session), "transcript": str(self.transcript(session)),
            "mark": mark}), encoding="utf-8")

    def test_the_old_record_is_read_as_one_entry(self) -> None:
        session = "8888aaaa-0000-0000-0000-000000000000"
        self.write(session, 200)
        self.legacy(session, 120)
        self.assertEqual(self.handoff(session), f"s:{self.slug(session)}#121-200")

    def test_a_resume_keeps_the_old_mark(self) -> None:
        session = "8888bbbb-0000-0000-0000-000000000000"
        self.write(session, 200)
        self.legacy(session, 120)
        self.start(session)
        self.assertEqual(self.mark_of(session), 120)

    def test_the_top_level_keys_still_name_the_last_session(self) -> None:
        """`rules.py` reads the slug from there, and so does an older copy."""
        session = "8888cccc-0000-0000-0000-000000000000"
        self.write(session, 12)
        self.start(session)
        state = self.state()
        self.assertEqual(state["slug"], self.slug(session))
        self.assertEqual(state["transcript"], str(self.transcript(session)))
        self.handoff(session)
        self.assertEqual(self.state()["mark"], 12)


class AVerdictIsTheRecord(Vault):
    """Considered and declined closes the debt only once it is written down.

    It used to close on the upper level being newer than the lower one, and
    `score-memory.py` rewrites every scored level on every run — so the step
    the working order puts first discharged every consolidation debt in the
    store before a line had been looked at.
    """

    def levels(self, held: str, lifted: str, sessions: int = 1) -> tuple[Path, Path]:
        """An inbox citing a session the level above has never seen.

        `sessions` registers that many, because a cadence is counted in them:
        `L1 → L2` is owed only after five, so a one-session vault answers "no
        debt" whatever the levels hold, and a test built on it proves nothing.
        """
        for number in range(sessions):
            # The slug is the first four characters of the id, so a shared
            # prefix would register one session however many are started.
            session = f"{number:04d}abcd-0000-0000-0000-000000000000"
            self.write(session, 10)
            self.start(session)
        folder = self.vault / "Memory" / "sample"
        folder.mkdir(parents=True, exist_ok=True)
        inbox, above = folder / "L0.md", folder / "L1.md"
        inbox.write_text(f"---\nname: sample-L0\n---\n\n- hit:1 use:0 seen below ({held})\n",
                         encoding="utf-8")
        above.write_text(f"---\nname: sample-L1\n---\n\n- hit:3 use:1 lifted ({lifted})\n",
                         encoding="utf-8")
        return inbox, above

    def test_rescoring_does_not_discharge_the_debt(self) -> None:
        self.levels("s:260801-aaaa", "s:260801-bbbb")
        self.assertIn("L0 → L1", self.debts())
        self.run_script(SCRIPTS / "score-memory.py")
        self.assertIn("L0 → L1", self.debts(),
                      "recomputing the scores answered for a decision nobody made")

    def test_the_considered_line_discharges_it(self) -> None:
        _, above = self.levels("s:260801-aaaa", "s:260801-bbbb")
        self.assertIn("L0 → L1", self.debts())
        above.write_text(above.read_text(encoding="utf-8")
                         + "\n<!-- considered: s:260801-aaaa -->\n", encoding="utf-8")
        self.assertNotIn("L0 → L1", self.debts(),
                         "a weighed session was still reported as never lifted")

    def test_a_verdict_is_not_a_stretch_that_was_read(self) -> None:
        """The record lives in the files the stretch scan reads, so it is skipped.

        A range copied into it would pass for a stretch written up and clear a
        handoff debt nobody paid — the defect this whole mechanism replaces,
        arriving through the other door.
        """
        session = "ffff3333-0000-0000-0000-000000000000"
        self.write(session, 30)
        self.start(session)
        self.end(session)
        self.start("9999333a-0000-0000-0000-000000000000")
        self.assertIn("archived and unread", self.debts())

        folder = self.vault / "Memory" / "sample"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "L1.md").write_text(
            f"---\nname: sample-L1\n---\n\n<!-- considered: s:{self.slug(session)}#1-30 -->\n",
            encoding="utf-8")
        self.assertIn("archived and unread", self.debts(),
                      "a verdict passed for the stretch having been written up")

    def test_a_declined_session_does_not_climb_to_the_next_level(self) -> None:
        """What a level holds is what its lines cite, not what it looked at.

        The level above holds no line of its own here, so it has nothing to
        offer further up — and the debt that used to appear named a session
        no line up there carried, which left nothing to weigh.
        """
        _, above = self.levels("s:260801-aaaa", "s:260801-bbbb", sessions=8)
        self.assertIn("L0 → L1", self.debts())
        above.write_text("---\nname: sample-L1\n---\n\n"
                         "<!-- considered: s:260801-aaaa -->\n", encoding="utf-8")
        owed = self.debts()
        self.assertNotIn("L0 → L1", owed, "a weighed session was still owed below")
        self.assertNotIn("L1 → L2", owed,
                         "a decline was offered upward as material no line carries")

    def test_a_level_that_did_not_move_is_not_rewritten(self) -> None:
        _, above = self.levels("s:260801-aaaa", "s:260801-bbbb")
        self.run_script(SCRIPTS / "score-memory.py")     # writes the scores in
        settled = above.stat().st_mtime_ns
        self.run_script(SCRIPTS / "score-memory.py")     # nothing left to change
        self.assertEqual(above.stat().st_mtime_ns, settled,
                         "a file with nothing to write was written anyway")


if __name__ == "__main__":
    unittest.main()
