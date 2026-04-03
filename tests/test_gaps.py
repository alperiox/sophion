import json

from sophion.gaps import Gap, GapTracker, StudySession


def test_gap_creation():
    gap = Gap(topic="diffusion", question="Why does the forward process converge to N(0,I)?")
    assert gap.topic == "diffusion"
    assert gap.question == "Why does the forward process converge to N(0,I)?"
    assert gap.status == "open"
    assert gap.id is not None


def test_gap_roundtrip():
    gap = Gap(topic="attention", question="How does multi-head attention work?")
    data = gap.to_dict()
    loaded = Gap.from_dict(data)
    assert loaded.id == gap.id
    assert loaded.topic == gap.topic
    assert loaded.question == gap.question
    assert loaded.status == gap.status


def test_gap_tracker_add(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")
    gap = tracker.add("diffusion", "What is the ELBO?")
    assert gap.status == "open"
    assert len(tracker.list_open()) == 1


def test_gap_tracker_resolve(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")
    gap = tracker.add("diffusion", "What is the ELBO?")
    tracker.resolve(gap.id, resolution="ELBO decomposes the log-likelihood into reconstruction + KL terms")

    resolved = tracker.get(gap.id)
    assert resolved.status == "resolved"
    assert resolved.resolution == "ELBO decomposes the log-likelihood into reconstruction + KL terms"


def test_gap_tracker_list_open(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")
    tracker.add("diffusion", "Q1")
    gap2 = tracker.add("attention", "Q2")
    tracker.resolve(gap2.id, resolution="Answered")

    open_gaps = tracker.list_open()
    assert len(open_gaps) == 1
    assert open_gaps[0].topic == "diffusion"


def test_gap_tracker_list_all(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")
    tracker.add("diffusion", "Q1")
    tracker.add("attention", "Q2")

    assert len(tracker.list_all()) == 2


def test_gap_tracker_persistence(tmp_path):
    path = tmp_path / "gaps.json"
    tracker1 = GapTracker(path)
    tracker1.add("diffusion", "Q1")
    tracker1.add("attention", "Q2")

    tracker2 = GapTracker(path)
    assert len(tracker2.list_all()) == 2


def test_gap_tracker_empty(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")
    assert tracker.list_open() == []
    assert tracker.list_all() == []


# --- StudySession tests ---


def test_study_session_starts_inactive(tmp_path):
    session = StudySession(tmp_path / "session.json")
    assert session.is_active() is False


def test_study_session_start(tmp_path):
    session = StudySession(tmp_path / "session.json")
    started = session.start()
    assert session.is_active() is True
    assert started != ""


def test_study_session_stop(tmp_path):
    session = StudySession(tmp_path / "session.json")
    session.start()
    started = session.stop()
    assert session.is_active() is False
    assert started != ""


def test_study_session_persistence(tmp_path):
    path = tmp_path / "session.json"
    s1 = StudySession(path)
    s1.start()

    s2 = StudySession(path)
    assert s2.is_active() is True

    s2.stop()

    s3 = StudySession(path)
    assert s3.is_active() is False


def test_gaps_since(tmp_path):
    tracker = GapTracker(tmp_path / "gaps.json")

    # Add a gap, record the time, add another
    gap1 = tracker.add("old", "Old question")

    from datetime import datetime
    midpoint = datetime.now().isoformat()

    gap2 = tracker.add("new", "New question")
    tracker.resolve(gap1.id, "Resolved now")

    added, resolved = tracker.gaps_since(midpoint)
    assert len(added) == 1
    assert added[0].topic == "new"
    assert len(resolved) == 1
    assert resolved[0].topic == "old"
