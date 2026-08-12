from app.agent.graph import build_graph, run_graph
from app.config import settings
from app.llm.factory import get_provider
import app.rag.retrieval as retrieval


def setup_mock_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    # reset factory cache
    import app.llm.factory as _f
    _f._provider_instance = None


def test_graph_construction():
    g = build_graph()
    assert g is not None
    # basic nodes exist
    for n in ["Planner", "Router", "ToolExecution", "EvidenceCollection", "Verifier", "ResponseGenerator"]:
        assert n in g.nodes


def test_sql_only_routing(monkeypatch):
    setup_mock_provider(monkeypatch)
    st = run_graph("What was July revenue?")
    assert "sql" in st["selected_tools"]
    assert st["sql_query"]
    assert st["sql_query"].lower().startswith("select")
    assert st["sql_results"]["success"] is True
    assert st["sql_results"]["row_count"] >= 1
    
def test_rag_only_routing(monkeypatch):
    setup_mock_provider(monkeypatch)

    # Prevent this unit test from loading SentenceTransformer/PyTorch.
    # The real RAG implementation remains unchanged.
    def fake_retrieve(query):
        return {
            "success": True,
            "results": [
                {
                    "text": (
                        "Inventory policy requires investigation "
                        "when inventory levels exceed reorder thresholds."
                    ),
                    "source": "inventory_policy.pdf",
                    "page": 3,
                    "chunk_id": "test-rag-chunk-1",
                }
            ],
        }

    import app.rag.retrieval as retrieval

    monkeypatch.setattr(
        retrieval,
        "retrieve",
        fake_retrieve,
    )

    st = run_graph("What is the inventory reorder policy?")

    assert "rag" in st["selected_tools"]
    assert st["retrieved_documents"]
    assert st["retrieved_documents"][0]["source"] == "inventory_policy.pdf"

def test_multi_tool_routing(monkeypatch):
    setup_mock_provider(monkeypatch)

    # Prevent the test from loading SentenceTransformer/PyTorch.
    # The real RAG implementation remains unchanged.
    def fake_retrieve(query):
        return {
            "success": True,
            "results": [
                {
                    "text": (
                        "Inventory policy requires investigation "
                        "when inventory cost increases significantly."
                    ),
                    "source": "inventory_policy.pdf",
                    "page": 3,
                    "chunk_id": "test-chunk-1",
                }
            ],
        }

    monkeypatch.setattr(
        retrieval,
        "retrieve",
        fake_retrieve,
    )

    st = run_graph(
        "Why did inventory cost increase in July "
        "and does this violate policy?"
    )

        # Planner/router should select multiple tools.
    assert "sql" in st["selected_tools"]
    assert "rag" in st["selected_tools"]

        # SQL should have actually executed.
    assert st["sql_results"]["success"] is True

        # RAG should have returned our mocked evidence.
    assert len(st["retrieved_documents"]) >= 1

        # Evidence should have been collected.
    assert isinstance(st.get("evidence", []), list)

def test_calculator_usage(monkeypatch):
    setup_mock_provider(monkeypatch)
    # inject calculation request into state via run_graph then manual exec
    st = run_graph("What percentage did revenue increase from June to July?")
    # calculator expected
    assert "calculator" in st.get("selected_tools", []) or "sql" in st.get("selected_tools", [])


def test_evidence_collection(monkeypatch):
    setup_mock_provider(monkeypatch)
    st = run_graph("What was July revenue?")
    assert isinstance(st.get("evidence", []), list)


def test_verification_and_response(monkeypatch):
    setup_mock_provider(monkeypatch)
    st = run_graph("What was July revenue?")
    vr = st.get("verification_result")
    assert isinstance(vr, dict)
    resp = st.get("final_response")
    assert resp is not None


def test_invalid_tool_selection(monkeypatch):
    setup_mock_provider(monkeypatch)
    # Monkeypatch planner to return an invalid tool
    import app.agent.planner as p

    orig = p.determine_plan

    def bad_plan(q):
        return ["sql", "evil_tool"]

    p.determine_plan = bad_plan
    try:
        st = run_graph("Some query")
        # router should raise and populate errors
        assert any("Invalid tool selection" in e for e in st.get("errors", []))
    finally:
        p.determine_plan = orig


def test_max_verification_attempts(monkeypatch):
    setup_mock_provider(monkeypatch)
    # Force verifier to exceed attempts
    import app.agent.verifier as v
    st = run_graph("What was July revenue?")
    st["verification_result"] = {"attempts": settings.max_verification_attempts}
    res = v.verify(st)
    assert res.get("ok") is False
