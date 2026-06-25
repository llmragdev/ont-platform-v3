import pytest

from app.api.extn import customer_questions
from app.api.extn.customer_questions import CustomerQuestionEventRequest, _handle_question_event
from app.api.extn.customer_replies import DraftReplyResponse, PostViaMcpResponse, _customer_safe_reply
from app.models.tenant_context import TenantContext


@pytest.fixture()
def tenant_ctx():
    return TenantContext(
        user_id="tester",
        company_id="default",
        project_id="proj-default",
        role="Admin",
        permissions={},
    )


@pytest.mark.asyncio
async def test_customer_question_event_is_idempotent_by_event_id(tmp_path, monkeypatch, tenant_ctx):
    monkeypatch.chdir(tmp_path)

    async def fake_post(request, ctx):
        return PostViaMcpResponse(
            request_id=request.request_id,
            status="dry_run",
            result={"external_thread_id": request.question_id, "message": request.reply_message},
            error=None,
            audit_id="audit-1",
            duration_ms=1,
            status_code=200,
        )

    def fake_draft(request, ctx, query_svc):
        return DraftReplyResponse(
            request_id=request.request_id,
            reply_id="reply-1",
            question_id=request.question_id,
            reply_message="draft",
            confidence=0.7,
            created_at="2026-06-13T00:00:00Z",
        )

    monkeypatch.setattr(customer_questions, "_post_to_customer_mcp", fake_post)
    monkeypatch.setattr(customer_questions, "_generate_draft", fake_draft)

    event = CustomerQuestionEventRequest(
        event_id="evt-001",
        question_id="q-001",
        title="title",
        content="content",
    )

    first = await _handle_question_event(event, tenant_ctx, query_svc=None)
    second = await _handle_question_event(event, tenant_ctx, query_svc=None)

    assert first.status == "accepted"
    assert first.duplicate is False
    assert second.status == "skipped"
    assert second.duplicate is True
    assert second.reason == "event_already_seen"


@pytest.mark.asyncio
async def test_customer_question_event_skips_processed_question(tmp_path, monkeypatch, tenant_ctx):
    monkeypatch.chdir(tmp_path)

    async def fake_post(request, ctx):
        return PostViaMcpResponse(
            request_id=request.request_id,
            status="success",
            result={"external_comment_id": "comment-1", "external_thread_id": request.question_id},
            error=None,
            audit_id="audit-1",
            duration_ms=1,
            status_code=200,
        )

    def fake_draft(request, ctx, query_svc):
        return DraftReplyResponse(
            request_id=request.request_id,
            reply_id="reply-1",
            question_id=request.question_id,
            reply_message="draft",
            confidence=0.7,
            created_at="2026-06-13T00:00:00Z",
        )

    monkeypatch.setattr(customer_questions, "_post_to_customer_mcp", fake_post)
    monkeypatch.setattr(customer_questions, "_generate_draft", fake_draft)

    first = await _handle_question_event(
        CustomerQuestionEventRequest(event_id="evt-001", question_id="q-001", content="content", mode="post"),
        tenant_ctx,
        query_svc=None,
    )
    second = await _handle_question_event(
        CustomerQuestionEventRequest(event_id="evt-002", question_id="q-001", content="content", mode="post"),
        tenant_ctx,
        query_svc=None,
    )

    assert first.status == "accepted"
    assert second.status == "skipped"
    assert second.duplicate is False
    assert second.reason == "question_already_processed"


def test_customer_safe_reply_replaces_internal_ontology_fallback():
    reply = _customer_safe_reply(
        "Found 3 ontology item(s). Citations: ontology:order-example:order-1001.",
        "비밀번호 초기화 요청\n\n관리자 계정 비밀번호를 분실했습니다.",
    )

    assert "Found 3 ontology" not in reply
    assert "Citations:" not in reply
    assert "비밀번호" in reply
    assert "본인 확인" in reply
