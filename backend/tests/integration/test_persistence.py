import json
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from career_assistant.database import (
    ensure_local_database,
    migrate_database,
    migration_config,
)
from career_assistant.db_cli import main
from career_assistant.models import (
    BackgroundFact,
    Clarification,
    DocumentDeletion,
    JobDefinition,
    Owner,
    Preference,
    Source,
)
from career_assistant.persistence import (
    DefinitionData,
    DefinitionRepository,
    PreferenceData,
    SourceData,
    ensure_owner,
)
from career_assistant.storage import LocalDocumentStore, cleanup_documents


def draft(**overrides):
    values = dict(
        description="Staff architecture with remote work and continuous learning.",
        preferences=[
            PreferenceData(key="scope", category="seniority", value="Staff"),
            PreferenceData(key="remote", category="work_arrangement", value=True),
            PreferenceData(
                key="onsite_limit",
                category="work_arrangement",
                priority="mandatory",
                value={"days": 2, "period": None},
            ),
            PreferenceData(key="salary", category="compensation", value=None),
            PreferenceData(
                key="frontend_only",
                category="responsibilities",
                priority="excluded",
                value=True,
            ),
        ],
    )
    values.update(overrides)
    return DefinitionData(**values)


def file_source():
    return SourceData(
        kind="file",
        display_name="synthetic.md",
        media_type="text/markdown",
        size_bytes=100,
        object_key=uuid4(),
    )


def test_save_reload_refine_preserves_id_constraints_and_unknowns(sessions):
    with sessions.begin() as session:
        definition = DefinitionRepository(session).save(draft())
        identity, created_at = definition.id, definition.created_at
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        loaded = repo.current()
        assert loaded.id == identity
        assert loaded.created_at.tzinfo is not None
        preferences = {item.key: item for item in session.scalars(select(Preference))}
        assert preferences["salary"].value is None
        assert preferences["onsite_limit"].value == {"days": 2, "period": None}
        assert preferences["frontend_only"].priority == "excluded"
        assert session.scalar(
            text("SELECT value IS NULL FROM preferences WHERE key = 'salary'")
        )
        previous_remote_id = preferences["remote"].id
        revised = draft(
            description="Arquitectura Staff; híbrido cerca de Madrid.",
            state="ready",
            preferences=[
                PreferenceData(key="remote", category="work_arrangement", value=False),
                PreferenceData(
                    key="hybrid_location",
                    category="location",
                    priority="mandatory",
                    value="Madrid",
                ),
            ],
        )
        repo.save(revised)
    with sessions() as session:
        definition = DefinitionRepository(session).current()
        assert definition.id == identity
        assert definition.created_at == created_at
        assert definition.state == "ready"
        assert "Madrid" in definition.description
        assert definition.updated_at >= definition.created_at
        preferences = {item.key: item for item in session.scalars(select(Preference))}
        assert set(preferences) == {"remote", "hybrid_location"}
        assert preferences["remote"].id == previous_remote_id
        assert preferences["remote"].value is False


def test_failed_transaction_preserves_previous_definition_and_preferences(sessions):
    with sessions.begin() as session:
        DefinitionRepository(session).save(draft())
    with pytest.raises(RuntimeError, match="simulated failure"):
        with sessions.begin() as session:
            DefinitionRepository(session).save(
                draft(description="Uncommitted", preferences=[])
            )
            raise RuntimeError("simulated failure")
    with sessions() as session:
        assert (
            DefinitionRepository(session).current().description == draft().description
        )
        assert session.scalar(select(func.count()).select_from(Preference)) == 5


def test_reviewed_context_is_separate_and_corrections_invalidate_derivatives(sessions):
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        repo.save(draft())
        source = repo.add_source(
            SourceData(kind="text", display_name="Synthetic profile")
        )
        source_id = source.id
        with pytest.raises(ValueError, match="Extract"):
            repo.review_source(source_id, ["Staff engineer"])
        repo.record_extraction(
            source_id, text="Synthetic historical frontend experience"
        )
        assert repo.reviewed_background() == []
        repo.review_source(source_id, [" Previously worked on frontend systems "])
        assert [fact.content for fact in repo.reviewed_background()] == [
            "Previously worked on frontend systems"
        ]
        assert session.scalar(select(func.count()).select_from(Preference)) == 5
        repo.add_clarifications(["What salary range would you prefer?"])
        repo.review_source(source_id, ["Corrected background fact"])
        assert session.scalar(select(func.count()).select_from(Clarification)) == 0
        repo.record_extraction(source_id, text=None, failed=True)
        assert source.reviewed_at is None
        assert repo.reviewed_background() == []
        assert session.scalar(select(func.count()).select_from(BackgroundFact)) == 0


def test_clarification_answers_persist_explicit_unknown_and_skip(sessions):
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        repo.save(draft())
        questions = repo.add_clarifications(
            ["Salary?", "Office-day period?", "Location?"]
        )
        ids = [item.id for item in questions]
        repo.answer_clarification(ids[0], "unknown")
        repo.answer_clarification(ids[1], "skipped")
        repo.answer_clarification(ids[2], "answered", " Madrid ")
        with pytest.raises(ValueError):
            repo.answer_clarification(ids[0], "answered")
        with pytest.raises(ValueError):
            repo.answer_clarification(ids[0], "skipped", "unaccepted text")
        with pytest.raises(ValueError):
            repo.add_clarifications(["A", "B", "C", "D"])
        with pytest.raises(ValueError):
            repo.add_clarifications([" "])
    with sessions() as session:
        questions = [session.get(Clarification, identity) for identity in ids]
        assert [(item.answer_state, item.answer) for item in questions] == [
            ("unknown", None),
            ("skipped", None),
            ("answered", "Madrid"),
        ]
        assert len({item.round_id for item in questions}) == 1
        assert session.scalar(select(func.count()).select_from(Preference)) == 5


def test_file_limit_slot_reuse_and_source_deletion_preserve_preferences(sessions):
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        repo.save(draft())
        originals = [repo.add_source(file_source()) for _ in range(5)]
        assert {item.file_slot for item in originals} == {1, 2, 3, 4, 5}
        with pytest.raises(ValueError, match="five"):
            repo.add_source(file_source())
        repo.record_extraction(originals[0].id, text="Synthetic background")
        repo.review_source(originals[0].id, ["Synthetic skill"])
        repo.add_clarifications(["Clarify compensation"])
        deleted_id, deleted_key = originals[0].id, originals[0].object_key
        repo.delete_source(deleted_id)
        replacement = repo.add_source(file_source())
        assert replacement.file_slot == 1
    with sessions() as session:
        assert session.get(Source, deleted_id) is None
        assert session.get(DocumentDeletion, deleted_key) is not None
        assert session.scalar(select(func.count()).select_from(BackgroundFact)) == 0
        assert session.scalar(select(func.count()).select_from(Clarification)) == 0
        assert session.scalar(select(func.count()).select_from(Preference)) == 5


def test_complete_deletion_and_retryable_original_cleanup(sessions, tmp_path):
    store = LocalDocumentStore(tmp_path / "originals")
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        definition_id = repo.save(draft()).id
        source = repo.add_source(file_source())
        key = source.object_key
        store.put(key, b"synthetic original")
        repo.record_extraction(source.id, text="Synthetic profile")
        repo.review_source(source.id, ["Synthetic fact"])
        repo.add_clarifications(["What would you change?"])
        repo.delete_definition()
    with sessions() as session:
        assert session.get(JobDefinition, definition_id) is None
        assert session.get(Owner, 1) is not None
        for model in (Source, BackgroundFact, Preference, Clarification):
            assert session.scalar(select(func.count()).select_from(model)) == 0

    class UnavailableStorage:
        def delete(self, key):
            raise OSError("synthetic storage outage")

    with pytest.raises(OSError):
        cleanup_documents(sessions, UnavailableStorage())
    with sessions() as session:
        assert session.get(DocumentDeletion, key) is not None
    assert store.get(key) == b"synthetic original"
    assert cleanup_documents(sessions, store) == 1
    assert cleanup_documents(sessions, store) == 0
    with pytest.raises(FileNotFoundError):
        store.get(key)


def test_rolled_back_deletion_never_queues_or_removes_an_original(sessions):
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        repo.save(draft())
        source_id = repo.add_source(file_source()).id
    with pytest.raises(RuntimeError):
        with sessions.begin() as session:
            DefinitionRepository(session).delete_source(source_id)
            raise RuntimeError("simulated rollback")
    with sessions() as session:
        assert session.get(Source, source_id) is not None
        assert session.scalar(select(func.count()).select_from(DocumentDeletion)) == 0


def test_cleanup_command_uses_the_configured_private_store(
    database, sessions, tmp_path, monkeypatch, capsys
):
    directory = tmp_path / "originals"
    store = LocalDocumentStore(directory)
    key = uuid4()
    store.put(key, b"synthetic original awaiting deletion")
    with sessions.begin() as session:
        session.add(DocumentDeletion(object_key=key))
    monkeypatch.setenv(
        "DATABASE_URL", database.url.render_as_string(hide_password=False)
    )
    monkeypatch.setenv("CAREER_DOCUMENT_BACKEND", "local")
    monkeypatch.setenv("CAREER_DOCUMENT_DIRECTORY", str(directory))
    main(["cleanup"])
    assert "Removed 1" in capsys.readouterr().out
    assert not list(directory.iterdir())
    with sessions() as session:
        assert session.get(DocumentDeletion, key) is None


def test_context_operations_require_the_current_definition_and_valid_ids(sessions):
    with sessions.begin() as session:
        repo = DefinitionRepository(session)
        assert repo.current() is None
        with pytest.raises(LookupError, match="Save a definition"):
            repo.add_source(file_source())
        repo.save(draft())
        with pytest.raises(LookupError, match="Source not found"):
            repo.delete_source(uuid4())
        with pytest.raises(LookupError, match="Clarification not found"):
            repo.answer_clarification(uuid4(), "unknown")
        source = repo.add_source(
            SourceData(
                kind="url",
                display_name="Public synthetic profile",
                url="https://example.invalid/profile",
            )
        )
        repo.record_extraction(source.id, text="Synthetic profile")
        with pytest.raises(ValueError, match="not be blank"):
            repo.review_source(source.id, [" "])
    with sessions.begin() as session:
        session.delete(session.get(Owner, 1))
    with sessions.begin() as session:
        with pytest.raises(LookupError, match="Initialize"):
            DefinitionRepository(session).save(draft())


@pytest.mark.parametrize(
    "invalid",
    [
        "second_owner",
        "second_definition",
        "blank_description",
        "invalid_priority",
        "duplicate_criterion",
        "oversize_file",
        "invalid_slot",
        "invalid_source_url",
        "answer_without_text",
        "fourth_question",
        "foreign_source",
    ],
)
def test_database_constraints_survive_bypassing_repository(sessions, invalid):
    with sessions.begin() as session:
        identity = DefinitionRepository(session).save(draft()).id
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            if invalid == "second_owner":
                record = Owner(id=2, username="unconfigured")
            elif invalid == "second_definition":
                record = JobDefinition(
                    owner_id=1, description="Duplicate current definition"
                )
            elif invalid == "blank_description":
                session.get(JobDefinition, identity).description = " "
                record = None
            elif invalid in {"invalid_priority", "duplicate_criterion"}:
                record = Preference(
                    definition_id=identity,
                    key="scope" if invalid == "duplicate_criterion" else "bad",
                    category="role",
                    priority="invented"
                    if invalid == "invalid_priority"
                    else "preferred",
                )
            elif invalid in {"oversize_file", "invalid_slot"}:
                record = Source(
                    definition_id=identity,
                    kind="file",
                    display_name="synthetic.md",
                    file_slot=6 if invalid == "invalid_slot" else 1,
                    object_key=uuid4(),
                    size_bytes=10485761 if invalid == "oversize_file" else 10,
                    media_type="text/markdown",
                )
            elif invalid == "invalid_source_url":
                record = Source(
                    definition_id=identity,
                    kind="url",
                    display_name="No internal fetch",
                    url="file:///tmp/test",
                )
            elif invalid in {"answer_without_text", "fourth_question"}:
                record = Clarification(
                    definition_id=identity,
                    round_id=uuid4(),
                    question="Synthetic question?",
                    position=4 if invalid == "fourth_question" else 1,
                    answer_state="answered"
                    if invalid == "answer_without_text"
                    else "unanswered",
                )
            else:
                record = BackgroundFact(source_id=uuid4(), content="Orphan fact")
            if record is not None:
                session.add(record)
    with sessions() as session:
        assert (
            DefinitionRepository(session).current().description == draft().description
        )
        assert session.scalar(select(func.count()).select_from(Owner)) == 1
        assert session.scalar(select(func.count()).select_from(Preference)) == 5


def test_migration_upgrade_and_repeated_initialization_preserve_data(
    database, sessions, monkeypatch, capsys
):
    with database.begin() as connection:
        config = migration_config()
        config.attributes["connection"] = connection
        command.downgrade(config, "0001")
    # Seed the old schema without querying it with the current ORM model.
    identity = uuid4()
    with database.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO job_definitions (id, owner_id, description) "
                "VALUES (:id, 1, :description)"
            ),
            {"id": identity, "description": draft().description},
        )
        for item in draft().preferences:
            connection.execute(
                text(
                    "INSERT INTO preferences (id, definition_id, key, category, "
                    "priority, value, note) VALUES (:id, :definition_id, :key, "
                    ":category, :priority, CAST(:value AS jsonb), :note)"
                ),
                {
                    "id": uuid4(),
                    "definition_id": identity,
                    **item.model_dump(),
                    "value": json.dumps(item.value) if item.value is not None else None,
                },
            )
        connection.execute(
            text(
                "UPDATE owners SET username = 'configured-owner', "
                "password_hash = 'synthetic-hash-not-a-real-credential' WHERE id = 1"
            )
        )
    migrate_database(database.url)
    assert ensure_local_database(database.url) is False
    monkeypatch.setenv(
        "DATABASE_URL", database.url.render_as_string(hide_password=False)
    )
    monkeypatch.setenv(
        "DATABASE_DIRECT_URL", database.url.render_as_string(hide_password=False)
    )
    main(["init"])
    main(["init"])
    main(["migrate"])
    assert "configured owner preserved" in capsys.readouterr().out
    with sessions.begin() as session:
        ensure_owner(session)
        assert DefinitionRepository(session).current().id == identity
        assert session.get(Owner, 1).username == "configured-owner"
        assert (
            session.get(Owner, 1).password_hash
            == "synthetic-hash-not-a-real-credential"
        )
        assert session.scalar(select(func.count()).select_from(Preference)) == 5
    with database.begin() as connection:
        config = migration_config()
        config.attributes["connection"] = connection
        command.check(config)
