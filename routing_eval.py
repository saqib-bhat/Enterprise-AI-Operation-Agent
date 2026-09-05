from app.rag.retrieval import retrieve


tests = [
    ("What is the inventory reorder policy?", "inventory_policy.pdf"),
    ("What are the rules for low stock inventory?", "inventory_policy.pdf"),
    ("When should inventory be reordered?", "inventory_policy.pdf"),
    ("What is the minimum stock requirement?", "inventory_policy.pdf"),
    ("What approval is required for large inventory orders?", "inventory_policy.pdf"),

    ("What is the vendor evaluation process?", "vendor_policy.pdf"),
    ("How are vendors evaluated?", "vendor_policy.pdf"),
    ("How often are vendors reviewed?", "vendor_policy.pdf"),
    ("What are the vendor contract requirements?", "vendor_policy.pdf"),
    ("What is the procurement approval process?", "vendor_policy.pdf"),

    ("What is the operations SOP?", "operations_sop.pdf"),
    ("What is the operations procedure?", "operations_sop.pdf"),
    ("What is the escalation procedure?", "operations_sop.pdf"),
    ("How are emergency restocks handled?", "operations_sop.pdf"),
    ("What are the purchasing procedures?", "operations_sop.pdf"),

    ("Explain the inventory procedures.", "operations_sop.pdf"),
    ("What are the receiving and inspection steps?", "operations_sop.pdf"),
    ("What are the reconciliation procedures?", "operations_sop.pdf"),
    ("What are the rules for vendor procurement?", "vendor_policy.pdf"),
    ("Explain the vendor management process.", "vendor_policy.pdf"),
]


def main() -> None:
    hit_at_1 = 0
    hit_at_3 = 0

    print("=" * 100)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 100)

    for query, expected_source in tests:

        result = retrieve(query, top_k=3)

        results = result.get("results", [])

        sources = [
            item.get("source")
            for item in results
            if isinstance(item, dict) and item.get("source")
        ]

        top1_hit = bool(sources) and sources[0] == expected_source
        top3_hit = expected_source in sources

        if top1_hit:
            hit_at_1 += 1

        if top3_hit:
            hit_at_3 += 1

        print(f"\nQuery: {query}")
        print(f"Expected: {expected_source}")
        print(f"Retrieved: {sources}")
        print(f"Hit@1: {'PASS' if top1_hit else 'FAIL'}")
        print(f"Hit@3: {'PASS' if top3_hit else 'FAIL'}")


    total = len(tests)

    print("\n" + "=" * 100)
    print(f"Hit@1: {hit_at_1}/{total} = {(hit_at_1 / total) * 100:.1f}%")
    print(f"Hit@3: {hit_at_3}/{total} = {(hit_at_3 / total) * 100:.1f}%")
    print("=" * 100)


if __name__ == "__main__":
    main()