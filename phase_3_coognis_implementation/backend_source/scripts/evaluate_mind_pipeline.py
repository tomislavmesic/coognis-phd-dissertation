import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.db.session import SessionLocal
from app.schemas.page import PageExpertSuggestion, PageRespondRequest, PageUlmGrounding, PageUlmSource, PageUserProfile
from app.schemas.uex import ExpertMatchRequest
from app.schemas.ulm import UlmGenerateRequest
from app.services.local_llm import MockLocalLlmClient, get_local_llm_client
from app.services.page import PageService
from app.services.synapse import get_synapse_service
from app.services.uex import UexService
from app.services.ulm import UlmService


@dataclass
class CaseResult:
    case_id: str
    query: str
    synapse_mbti: str | None
    inferred_domain_codes: list[str]
    uex_item_titles: list[str]
    ulm_chunk_titles: list[str]
    expert_name: str | None
    page_intent: str | None
    page_style: str | None
    response_text: str
    response_preview: str
    passed: bool
    failures: list[str]


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Benchmark file must contain a JSON array of cases.")
    return payload


def normalize_case(case: dict) -> dict:
    if not isinstance(case, dict):
        raise ValueError("Each case must be a JSON object.")
    if not isinstance(case.get("id"), str) or not case["id"].strip():
        raise ValueError("Each case must include a non-empty string 'id'.")
    if not isinstance(case.get("query"), str) or not case["query"].strip():
        raise ValueError(f"Case '{case.get('id')}' must include a non-empty 'query'.")

    return {
        "id": case["id"].strip(),
        "query": case["query"].strip(),
        "use_synapse": bool(case.get("use_synapse", True)),
        "use_uex": bool(case.get("use_uex", True)),
        "use_ulm": bool(case.get("use_ulm", True)),
        "expect": case.get("expect", {}) if isinstance(case.get("expect", {}), dict) else {},
    }


def evaluate_expectations(result: CaseResult, expect: dict) -> list[str]:
    failures: list[str] = []

    min_uex_items = expect.get("min_uex_items")
    if isinstance(min_uex_items, int) and len(result.uex_item_titles) < min_uex_items:
        failures.append(f"Expected at least {min_uex_items} UEX items, got {len(result.uex_item_titles)}.")

    max_uex_items = expect.get("max_uex_items")
    if isinstance(max_uex_items, int) and len(result.uex_item_titles) > max_uex_items:
        failures.append(f"Expected at most {max_uex_items} UEX items, got {len(result.uex_item_titles)}.")

    expected_domains = expect.get("expected_domain_codes", [])
    if isinstance(expected_domains, list) and expected_domains:
        missing_domains = [code for code in expected_domains if code not in result.inferred_domain_codes]
        if missing_domains:
            failures.append(f"Missing expected domain codes: {', '.join(missing_domains)}.")

    forbidden_uex_titles = expect.get("forbidden_uex_titles", [])
    if isinstance(forbidden_uex_titles, list):
        matched_titles = [
            title for title in result.uex_item_titles
            if any(fragment.lower() in title.lower() for fragment in forbidden_uex_titles)
        ]
        if matched_titles:
            failures.append(f"UEX returned forbidden titles: {', '.join(matched_titles)}.")

    max_ulm_chunks = expect.get("max_ulm_chunks")
    if isinstance(max_ulm_chunks, int) and len(result.ulm_chunk_titles) > max_ulm_chunks:
        failures.append(f"Expected at most {max_ulm_chunks} ULM chunks, got {len(result.ulm_chunk_titles)}.")

    expected_expert = expect.get("expert_suggestion")
    if isinstance(expected_expert, bool):
        has_expert = result.expert_name is not None
        if has_expert != expected_expert:
            failures.append(f"Expected expert_suggestion={expected_expert}, got {has_expert}.")

    must_contain = expect.get("response_should_contain", [])
    if isinstance(must_contain, list):
        for fragment in must_contain:
            if isinstance(fragment, str) and fragment.strip() and fragment.lower() not in result.response_text.lower():
                failures.append(f"Response is missing expected text fragment: '{fragment}'.")

    must_not_contain = expect.get("response_should_not_contain", [])
    if isinstance(must_not_contain, list):
        for fragment in must_not_contain:
            if isinstance(fragment, str) and fragment.strip() and fragment.lower() in result.response_text.lower():
                failures.append(f"Response includes forbidden text fragment: '{fragment}'.")

    return failures


def truncate(value: str, length: int = 260) -> str:
    normalized = " ".join((value or "").split())
    if len(normalized) <= length:
        return normalized
    return f"{normalized[: length - 1].rstrip()}…"


def build_run_payload(
    *,
    benchmark_path: Path,
    llm_backend: str,
    limit: int,
    results: list[CaseResult],
) -> dict:
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_path": str(benchmark_path),
        "llm_backend": llm_backend,
        "case_limit": limit,
        "total_cases": len(results),
        "passed_cases": passed_count,
        "failed_cases": failed_count,
        "results": [asdict(result) for result in results],
    }


def save_run_payload(*, payload: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"mind-eval-{timestamp}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a lightweight evaluation harness for SYNEXIS MIND/UEX/ULM/PAGE routing quality."
    )
    parser.add_argument(
        "--path",
        default="docs/evaluation-benchmark.json",
        help="Path to the benchmark JSON file. Default: docs/evaluation-benchmark.json",
    )
    parser.add_argument(
        "--llm-backend",
        choices=("configured", "mock"),
        default="mock",
        help="Use the configured local LLM backend or a fast mock PAGE/ULM backend. Default: mock",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of benchmark cases to run. Default: 0 (run all).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON results instead of the compact console summary.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the full benchmark run as a timestamped JSON artifact.",
    )
    parser.add_argument(
        "--output-dir",
        default="../docs/evaluation-results",
        help="Directory for saved benchmark run artifacts. Default: ../docs/evaluation-results",
    )
    args = parser.parse_args()

    benchmark_path = Path(args.path)
    cases = [normalize_case(case) for case in load_cases(benchmark_path)]
    if args.limit > 0:
        cases = cases[: args.limit]

    db = SessionLocal()
    try:
        synapse_service = get_synapse_service()
        uex_service = UexService(db)
        ulm_service = UlmService(db)
        page_service = PageService()
        llm_client = get_local_llm_client() if args.llm_backend == "configured" else MockLocalLlmClient()

        results: list[CaseResult] = []

        for case in cases:
            query = case["query"]
            expect = case["expect"]

            synapse_result = synapse_service.infer(query) if case["use_synapse"] else None
            target_mbti = synapse_result.mbti_type if synapse_result is not None else None

            inferred_domain_codes: list[str] = []
            uex_item_titles: list[str] = []
            uex_knowledge_content = "No UEX knowledge available."
            expert_name = None

            if case["use_uex"]:
                inferred_domain_codes = uex_service.suggest_domain_codes_for_text(query)
                uex_knowledge = uex_service.get_knowledge_context_for_query(
                    query=query,
                    domain_codes=inferred_domain_codes,
                    limit=3,
                )
                uex_knowledge_content = uex_knowledge.content or "No UEX knowledge available."
                uex_item_titles = [item.title for item in uex_knowledge.items]

                if uex_knowledge.items:
                    matches = uex_service.match_experts(
                        ExpertMatchRequest(
                            domain_codes=inferred_domain_codes,
                            target_mbti=target_mbti,
                            limit=1,
                        )
                    )
                    if matches.items:
                        expert_name = matches.items[0].name

            ulm_chunk_titles: list[str] = []
            ulm_grounding = None
            if case["use_ulm"]:
                retrieved = ulm_service.retrieve_context(query=query, limit=3)
                ulm_chunk_titles = [chunk.title or f"Chunk {index + 1}" for index, chunk in enumerate(retrieved.retrieved_chunks)]
                if retrieved.retrieved_chunks:
                    ulm_result = ulm_service.generate(
                        UlmGenerateRequest(query=query, retrieved_chunks=retrieved.retrieved_chunks),
                        llm_client,
                    )
                    ulm_grounding = PageUlmGrounding(
                        summary=ulm_result.explanation,
                        source_count=len({chunk.source_id for chunk in retrieved.retrieved_chunks if chunk.source_id}),
                        chunk_count=len(retrieved.retrieved_chunks),
                        sources=[
                            PageUlmSource(
                                title=chunk.title,
                                chunk_index=chunk.chunk_index,
                                source_type=chunk.source_type,
                            )
                            for chunk in retrieved.retrieved_chunks
                        ],
                    )

            page_payload = PageRespondRequest(
                user_profile=PageUserProfile(mbti=target_mbti),
                query=query,
                uex_knowledge=uex_knowledge_content,
                expert_suggestion=(
                    PageExpertSuggestion(
                        name=expert_name,
                        domain_codes=inferred_domain_codes,
                        is_contactable=bool(expert_name),
                        reason=None,
                    )
                    if expert_name
                    else None
                ),
                ulm_grounding=ulm_grounding,
                ulm_used=ulm_grounding is not None,
                conversation_mode="system",
            )
            page_result = page_service.respond(page_payload, llm_client)

            result = CaseResult(
                case_id=case["id"],
                query=query,
                synapse_mbti=target_mbti,
                inferred_domain_codes=inferred_domain_codes,
                uex_item_titles=uex_item_titles,
                ulm_chunk_titles=ulm_chunk_titles,
                expert_name=expert_name,
                page_intent=page_result.intent_label,
                page_style=page_result.style_label,
                response_text=page_result.response,
                response_preview=truncate(page_result.response, 320),
                passed=True,
                failures=[],
            )
            result.failures = evaluate_expectations(result, expect)
            result.passed = not result.failures
            results.append(result)

        run_payload = build_run_payload(
            benchmark_path=benchmark_path,
            llm_backend=args.llm_backend,
            limit=args.limit,
            results=results,
        )

        saved_output_path = None
        if args.save:
            saved_output_path = save_run_payload(
                payload=run_payload,
                output_dir=Path(args.output_dir),
            )

        if args.json:
            print(json.dumps(run_payload, ensure_ascii=False, indent=2))
            if saved_output_path is not None:
                print(f"\nSaved evaluation run: {saved_output_path}")
            return

        passed_count = sum(1 for result in results if result.passed)
        print(f"cases={len(results)} passed={passed_count} failed={len(results) - passed_count} llm_backend={args.llm_backend}")
        if saved_output_path is not None:
            print(f"saved: {saved_output_path}")
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(f"\n[{status}] {result.case_id}")
            print(f"query: {result.query}")
            print(f"synapse_mbti: {result.synapse_mbti or 'none'}")
            print(f"domains: {', '.join(result.inferred_domain_codes) or 'none'}")
            print(f"uex_items: {', '.join(result.uex_item_titles) or 'none'}")
            print(f"ulm_chunks: {', '.join(result.ulm_chunk_titles) or 'none'}")
            print(f"expert: {result.expert_name or 'none'}")
            print(f"page: intent={result.page_intent or 'n/a'} style={result.page_style or 'n/a'}")
            print(f"response: {result.response_preview}")
            if result.failures:
                for failure in result.failures:
                    print(f"  - {failure}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
