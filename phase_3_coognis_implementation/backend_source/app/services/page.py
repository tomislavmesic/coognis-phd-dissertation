import re

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import settings
from app.schemas.page import PageRespondRequest, PageRespondResponse, PageUlmSource
from app.services.local_llm import LocalLlmClient, get_llm_client_from_db


class PlaceholderPageRenderer:
    """Deterministic first-slice PAGE renderer until a real LLM client is wired."""

    STYLE_LEADS = {
        "strategic-structured": "The clearest path is this.",
        "practical-stepwise": "",
        "warm-exploratory": "A helpful way to approach this is:",
        "empathetic-insightful": "Here is a careful way to approach this.",
        "supportive-reassuring": "A grounded way to move forward is this.",
        "direct-decisive": "The most direct answer is this.",
        "balanced-clear": "",
    }

    def generate(
        self,
        prompt: str,
        style_label: str,
        intent_label: str,
        payload: PageRespondRequest,
        sections: list[str],
        format_rule: dict[str, object] | None = None,
    ) -> str:
        del prompt

        lead = self.STYLE_LEADS.get(style_label, self.STYLE_LEADS["balanced-clear"])
        paragraphs: list[str] = [lead] if lead else []
        support_sentences: list[str] = []

        if "answer" in sections:
            paragraphs.append(self._compose_answer(payload, intent_label))

        if "collaboration_note" in sections:
            support_sentences.append(self._compose_collaboration_note(payload))

        if "next_steps" in sections:
            paragraphs.append(self._compose_next_steps(payload, intent_label))

        if "expert_note" in sections and payload.expert_suggestion is not None:
            support_sentences.append(self._compose_expert_note(payload))

        if "grounding_note" in sections and payload.ulm_used and payload.ulm_grounding is not None:
            support_sentences.append(self._compose_grounding_note(payload))

        if "clarifying_note" in sections:
            support_sentences.append(self._compose_clarifying_note(payload))

        if "source_note" in sections:
            support_sentences.append(self._compose_source_note(payload))

        if support_sentences:
            paragraphs.append(" ".join(sentence for sentence in support_sentences if sentence))

        content = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
        content = self._apply_format_rule(content, payload=payload, format_rule=format_rule)
        return self._apply_intent_presentation(content, payload=payload, intent_label=intent_label, format_rule=format_rule)

    def _compose_answer(self, payload: PageRespondRequest, intent_label: str) -> str:
        knowledge_summary = self._summarize_knowledge(payload.uex_knowledge)
        intent_tail = {
            "troubleshooting": "Start with the most likely cause and the quickest useful check.",
            "planning": "Keep the plan short and workable.",
            "decision": "Focus on the main tradeoff before choosing.",
            "clarification": "Keep the explanation careful where context is still thin.",
        }.get(intent_label, "")
        if payload.conversation_mode == "expert":
            return (
                f"{knowledge_summary} {intent_tail} Keep it aligned with the ongoing expert exchange."
            )

        if payload.ulm_used and payload.ulm_grounding is not None:
            return f"{knowledge_summary} {intent_tail} Use grounded external context where it makes the answer clearer."

        return f"{knowledge_summary} {intent_tail}".strip()

    def _compose_collaboration_note(self, payload: PageRespondRequest) -> str:
        if payload.conversation_mode != "expert":
            return ""

        return (
            "Keep the reply easy for the expert and user to continue from in the same thread, "
            "without resetting the conversation or restating unnecessary background."
        )

    def _compose_next_steps(self, payload: PageRespondRequest, intent_label: str) -> str:
        query_summary = self._truncate(payload.query.strip(), 120)
        if intent_label == "troubleshooting":
            return (
                f"Check the most likely cause behind '{query_summary}', confirm the exact symptom, "
                "and try the smallest concrete fix before escalating."
            )
        if intent_label == "planning":
            return (
                f"Turn '{query_summary}' into a short sequence of actions, complete the first low-risk step, "
                "and then confirm the next step."
            )
        if intent_label == "decision":
            return (
                f"List the most important options behind '{query_summary}', compare the main tradeoff for each one, "
                "and then choose the option with the clearest practical fit."
            )
        if payload.conversation_mode == "expert":
            return (
                f"Confirm the exact details behind '{query_summary}', answer the most important unresolved point first, "
                "and keep the next reply tightly focused."
            )

        if payload.expert_suggestion is not None:
            return (
                f"Confirm the exact details behind '{query_summary}', act on the most relevant guidance above, "
                "and use expert follow-up if the issue still needs case-specific judgement."
            )

        return (
            f"Confirm the exact details behind '{query_summary}', act on the most relevant guidance above, "
            "and continue the conversation with any missing facts if the issue remains unclear."
        )

    def _compose_expert_note(self, payload: PageRespondRequest) -> str:
        expert = payload.expert_suggestion
        if expert is None:
            return ""

        domain_note = ""
        if expert.domain_codes:
            domain_note = f" Relevant domains: {', '.join(expert.domain_codes)}."

        reason_note = ""
        if expert.reason:
            reason_note = f" {self._truncate(expert.reason, 140)}"

        if expert.is_contactable:
            return f"{expert.name} is a suitable follow-up if you need deeper help.{domain_note}{reason_note}"

        return (
            f"{expert.name} looks relevant, but is currently available as a knowledge match only "
            f"until a {settings.app_public_name} expert account is provisioned.{domain_note}{reason_note}"
        )

    def _compose_clarifying_note(self, payload: PageRespondRequest) -> str:
        return (
            "The current response has limited supporting context, so the next turn should focus on the "
            "specific facts, constraints, or examples needed to narrow the answer."
        )

    def _compose_grounding_note(self, payload: PageRespondRequest) -> str:
        grounding = payload.ulm_grounding
        if grounding is None:
            return ""

        source_citations = self._build_source_citations(grounding.sources)
        source_note = ""
        if source_citations:
            source_note = f" External support came from {', '.join(source_citations[:2])}."

        return (
            f"{self._truncate(grounding.summary, 220)} "
            f"This was based on {grounding.chunk_count} retrieved chunk(s) from {grounding.source_count} source(s)."
            f"{source_note}"
        ).strip()

    def _compose_source_note(self, payload: PageRespondRequest) -> str:
        grounding = payload.ulm_grounding
        if grounding is None or not grounding.sources:
            return ""

        source_citations = self._build_source_citations(grounding.sources)
        if not source_citations:
            return ""

        return f"External sources used include {', '.join(source_citations[:3])}."

    @staticmethod
    def _canonicalize_source_title(title: str | None) -> str:
        normalized = (title or "").strip()
        if not normalized:
            return ""
        return re.sub(r"\s*\(Chunk\s+\d+/\d+\)\s*$", "", normalized, flags=re.IGNORECASE).strip()

    def _build_source_citations(self, sources: list[PageUlmSource]) -> list[str]:
        citations: list[str] = []
        seen: set[tuple[str, str]] = set()
        for source in sources:
            title = self._canonicalize_source_title(source.title)
            url = (source.url or "").strip()
            if not title and not url:
                continue
            key = (title.lower(), url.lower())
            if key in seen:
                continue
            seen.add(key)
            if title and url:
                citations.append(f"{title} ({url})")
            elif title:
                citations.append(title)
            else:
                citations.append(url)
        return citations

    def _summarize_knowledge(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
        cleaned = [sentence.strip() for sentence in sentences if sentence.strip()]
        if not cleaned:
            return "No strong UEX knowledge context was available, so the response should stay cautious and focused on clarifying the issue."

        return " ".join(cleaned[:2])

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        value = (value or "").strip()
        if len(value) <= max_length:
            return value
        return f"{value[: max_length - 1].rstrip()}…"

    def _apply_format_rule(
        self,
        content: str,
        *,
        payload: PageRespondRequest,
        format_rule: dict[str, object] | None,
    ) -> str:
        if not format_rule:
            return content

        structure = format_rule.get("structure")
        if structure == "ordered_steps":
            return self._format_ordered_steps(content, payload=payload, labels=str(format_rule.get("labels") or "Step {n}:"))
        if structure == "quick_actions":
            return self._format_quick_actions(content)
        if structure == "conceptual_analysis":
            return self._format_conceptual_analysis(content)
        if structure == "guided_explanation":
            return self._format_guided_explanation(content)
        return content

    def _apply_intent_presentation(
        self,
        content: str,
        *,
        payload: PageRespondRequest,
        intent_label: str,
        format_rule: dict[str, object] | None,
    ) -> str:
        if format_rule:
            return content

        normalized = content.strip()
        if not normalized:
            return normalized

        if intent_label == "troubleshooting":
            return self._format_quick_actions(normalized)
        if intent_label == "planning":
            return self._format_ordered_steps(normalized, payload=payload, labels="Step {n}:")
        if intent_label == "decision":
            return self._format_decision_layout(normalized)
        return normalized

    def _format_ordered_steps(self, content: str, *, payload: PageRespondRequest, labels: str) -> str:
        normalized = content.strip()
        if not normalized:
            return normalized

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]
        if len(sentences) < 2:
            return normalized

        intro = self._build_steps_intro(payload.query)
        steps = []
        note_sentences = []
        for index, sentence in enumerate(sentences, start=1):
            lowered = sentence.lower()
            if lowered.startswith(("if ", "note:", "however", "alternatively")):
                note_sentences.append(sentence)
                continue
            steps.append(f"{labels.format(n=len(steps) + 1)} {sentence.rstrip()}")

        if not steps:
            return normalized

        blocks = [intro, *steps]
        if note_sentences:
            blocks.append(" ".join(note_sentences))
        return "\n".join(block for block in blocks if block)

    @staticmethod
    def _build_steps_intro(query: str) -> str:
        cleaned_query = (query or "").strip().rstrip("?.!")
        if not cleaned_query:
            return "Follow these steps:"
        lowered = cleaned_query[:1].lower() + cleaned_query[1:]
        return f"To {lowered}, you need to:"

    @staticmethod
    def _format_quick_actions(content: str) -> str:
        normalized = content.strip()
        if not normalized:
            return normalized
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]
        if len(sentences) < 2:
            return normalized
        return "\n".join(f"- {sentence.rstrip()}" for sentence in sentences)

    @staticmethod
    def _format_decision_layout(content: str) -> str:
        normalized = content.strip()
        if not normalized:
            return normalized
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]
        if len(sentences) < 2:
            return normalized
        lead = sentences[0]
        remainder = "\n".join(f"- {sentence.rstrip()}" for sentence in sentences[1:])
        return f"{lead}\n{remainder}".strip()

    @staticmethod
    def _format_conceptual_analysis(content: str) -> str:
        normalized = content.strip()
        if not normalized:
            return normalized

        sentences = PlaceholderPageRenderer._extract_user_facing_sentences(normalized)
        if len(sentences) < 2:
            return normalized

        core = sentences[0]
        reasoning: list[str] = []
        options: list[str] = []
        for sentence in sentences[1:]:
            lowered = sentence.lower()
            if any(token in lowered for token in {"option", "choose", "alternative", "tradeoff", "compare", "if "}):
                options.append(sentence)
            else:
                reasoning.append(sentence)

        blocks = [core]
        if reasoning:
            blocks.append("Reasoning:\n" + "\n".join(f"- {sentence.rstrip()}" for sentence in reasoning))
        if options and PlaceholderPageRenderer._has_meaningful_alternatives(options):
            blocks.append("Options to consider:\n" + "\n".join(f"- {sentence.rstrip()}" for sentence in options))
        return "\n\n".join(block for block in blocks if block)

    @staticmethod
    def _format_guided_explanation(content: str) -> str:
        normalized = content.strip()
        if not normalized:
            return normalized

        sentences = PlaceholderPageRenderer._extract_user_facing_sentences(normalized)
        if len(sentences) < 2:
            return normalized

        intro = PlaceholderPageRenderer._ensure_supportive_intro(sentences[0])
        guidance = sentences[1:]
        if not guidance:
            return intro

        next_step = PlaceholderPageRenderer._build_nfj_next_step(guidance[0])
        remainder = guidance[1:]
        closing = PlaceholderPageRenderer._build_nfj_closing(remainder)

        blocks = [intro, next_step]
        if closing:
            blocks.append(closing)
        return "\n\n".join(block for block in blocks if block)

    @staticmethod
    def _extract_user_facing_sentences(content: str) -> list[str]:
        raw_sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", content)
            if sentence.strip()
        ]
        cleaned: list[str] = []
        seen_normalized: set[str] = set()
        for sentence in raw_sentences:
            candidate = sentence.strip().lstrip("- ").strip()
            if not candidate:
                continue
            if PlaceholderPageRenderer._looks_like_internal_instruction(candidate):
                continue
            normalized = re.sub(r"\s+", " ", candidate.lower()).rstrip(".!?")
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)
            cleaned.append(candidate)
        return cleaned

    @staticmethod
    def _looks_like_internal_instruction(sentence: str) -> bool:
        lowered = sentence.lower().strip()
        prefixes = (
            "assume the user",
            "use the system",
            "use the tone and style requested",
            "use the structure and formatting requested",
            "use the requested sections",
            "use the required style",
            "when the answer is supported by external context",
            "if the system does not have enough context",
            "if neither uex nor ulm provides relevant support",
            "when ulm grounding is present",
            "include a clear next step",
            "if the system has enough context",
            "if the system has no relevant knowledge",
            "keep the response",
            "follow the",
            "do not use",
            "do not claim",
            "mention expert escalation",
            "write one natural user-facing answer",
            "adapt the response",
            "detected intent",
            "preferred style",
            "formatting rule",
            "required sections",
            "output format",
            "rules",
            "user query",
            "uex knowledge",
            "expert info",
            "ulm grounding summary",
            "conversation mode",
        )
        return lowered.startswith(prefixes)

    @staticmethod
    def _has_meaningful_alternatives(options: list[str]) -> bool:
        if len(options) > 1:
            return True
        if not options:
            return False
        lowered = options[0].lower()
        return any(token in lowered for token in {"alternative", "tradeoff", "compare", "choose", "option", "or "})

    @staticmethod
    def _ensure_supportive_intro(sentence: str) -> str:
        cleaned = sentence.strip()
        if not cleaned:
            return cleaned

        lowered = cleaned.lower()
        if lowered.startswith(("a good way to approach this", "a helpful way to approach this", "a calm way to approach this")):
            return cleaned
        if lowered.startswith(("you can", "start by", "first,")):
            return f"A calm way to approach this is to {cleaned[:1].lower() + cleaned[1:]}"
        return cleaned

    @staticmethod
    def _build_nfj_next_step(sentence: str) -> str:
        cleaned = sentence.strip().rstrip()
        if not cleaned:
            return ""

        lowered = cleaned.lower()
        if lowered.startswith("a good next step is to"):
            return cleaned
        if lowered.startswith(("you can ", "start by ", "first, ")):
            return f"A good next step is to {cleaned[:1].lower() + cleaned[1:]}"
        return f"A good next step is to {cleaned.rstrip('.')}."

    @staticmethod
    def _build_nfj_closing(sentences: list[str]) -> str:
        if not sentences:
            return ""

        trimmed = [sentence.strip() for sentence in sentences if sentence.strip()]
        if not trimmed:
            return ""

        combined = " ".join(trimmed[:2])
        lowered = combined.lower()
        if any(token in lowered for token in {"if ", "when ", "once ", "after "}):
            return combined
        return f"This should give you a clear way forward. {combined}".strip()


class PageService:
    """Prompt-building and first-slice response generation for PAGE."""

    MBTI_STYLE_MAP = {
        "INTJ": "strategic-structured",
        "ENTJ": "direct-decisive",
        "ISTJ": "practical-stepwise",
        "ESTJ": "practical-stepwise",
        "ENFP": "warm-exploratory",
        "INFJ": "empathetic-insightful",
        "INFP": "supportive-reassuring",
        "ENFJ": "empathetic-insightful",
    }

    MBTI_FORMAT_RULES = {
        "STJ": {
            "structure": "ordered_steps",
            "labels": "Step {n}:",
            "intro": "optional",
            "note": True,
            "tone": "formal_practical",
        },
        "NTP": {
            "structure": "conceptual_analysis",
            "options": True,
            "reasoning": True,
            "tone": "analytical",
        },
        "NFJ": {
            "structure": "guided_explanation",
            "supportive_language": True,
            "tone": "empathetic_formal",
        },
        "SFP": {
            "structure": "quick_actions",
            "bullet_list": True,
            "tone": "practical_friendly",
        },
    }

    def build_prompt(self, payload: PageRespondRequest) -> tuple[str, str, str, list[str], dict[str, object] | None]:
        mbti = payload.user_profile.mbti.upper() if payload.user_profile.mbti else "DEFAULT"
        style_label = self.MBTI_STYLE_MAP.get(mbti, "balanced-clear")
        format_rule = self._resolve_format_rule(mbti)
        intent_label = self._infer_intent(payload.query)
        sections = self._resolve_sections(payload, intent_label=intent_label)
        expert_instruction = "No expert suggestion available."
        if payload.expert_suggestion is not None:
            expert_instruction = (
                f"Suggested expert: {payload.expert_suggestion.name}. "
                f"Contactable: {'yes' if payload.expert_suggestion.is_contactable else 'no'}. "
                f"Domains: {', '.join(payload.expert_suggestion.domain_codes) or 'none'}."
            )

        ulm_context = "No ULM summary used."
        if payload.ulm_grounding is not None:
            source_titles = [source.title for source in payload.ulm_grounding.sources if source.title]
            ulm_context = (
                f"Summary: {payload.ulm_grounding.summary}\n"
                f"Source count: {payload.ulm_grounding.source_count}\n"
                f"Chunk count: {payload.ulm_grounding.chunk_count}\n"
                f"Source titles: {', '.join(source_titles[:3]) or 'none'}"
            )

        prompt = (
            f"You are PAGE, the final response composition layer for {settings.app_public_name}.\n"
            f"Adapt the response for MBTI profile: {mbti}.\n"
            f"Preferred style: {style_label}.\n"
            f"Formatting rule: {self._describe_format_rule(format_rule)}.\n"
            f"Detected intent: {intent_label}.\n"
            f"Conversation mode: {payload.conversation_mode}.\n"
            f"Required sections: {', '.join(sections)}.\n\n"
            f"User query:\n{payload.query}\n\n"
            f"UEX knowledge:\n{payload.uex_knowledge}\n\n"
            f"Expert info:\n{expert_instruction}\n\n"
            f"ULM grounding summary:\n{ulm_context}\n\n"
            "Rules:\n"
            "- Start with a direct answer.\n"
            "- Keep the answer concise, clear, and user-facing.\n"
            "- Add practical next steps when useful.\n"
            "- If neither UEX nor ULM provides relevant support, say clearly that the system does not have enough relevant context instead of improvising domain-specific guidance.\n"
            "- Use the detected intent to shape the answer: troubleshooting should be diagnostic, planning should be sequential, decision support should state the tradeoff clearly.\n"
            "- Mention expert escalation only if an expert suggestion exists.\n"
            "- Do not claim grounded evidence that is not present.\n"
            "- When ULM grounding is present, reflect that the answer is supported by external retrieved context and keep ULM support distinct from UEX expert knowledge.\n"
            "- If the expert is not contactable, say so briefly without suggesting immediate handoff.\n"
            "- Follow the MBTI formatting rule strictly when it is provided.\n"
            "- For STJ profiles, prefer ordered Step n formatting with a practical concluding note when relevant.\n"
            "- For NTP profiles, state the core point first, then make the reasoning explicit, and compare options or tradeoffs when useful.\n"
            "- For NFJ profiles, use guided explanation with supportive but formal language and end with one clear next step.\n"
            "- For SFP profiles, prefer quick action bullets and short practical language.\n"
            "- Do not use markdown headings unless they make the answer materially clearer.\n"
            "- If source titles are available, you may mention them briefly in the source note.\n\n"
            "Output format:\n"
            "- Write one natural user-facing answer, not a labeled report.\n"
            "- Use the requested sections internally, but merge them into smooth prose.\n"
            "- Do not emit headings such as 'Final response', 'Answer', 'Next steps', 'Expert note', 'Grounding note', 'Source note', or 'Note'.\n"
            "- Do not sign the response with names like 'ULM' or 'PAGE'.\n"
            "- Keep paragraphs short and natural; avoid meta commentary.\n"
        )
        return prompt, style_label, intent_label, sections, format_rule

    def respond(
        self,
        payload: PageRespondRequest,
        llm_client: LocalLlmClient,
    ) -> PageRespondResponse:
        prompt, style_label, intent_label, sections, format_rule = self.build_prompt(payload)
        fallback_content = PlaceholderPageRenderer().generate(
            prompt,
            style_label,
            intent_label,
            payload,
            sections,
            format_rule,
        )
        if self._should_force_no_context_response(payload):
            content = self._build_no_context_response(payload, fallback_content)
        elif getattr(llm_client, "backend_name", "") == "mock":
            content = fallback_content
        else:
            try:
                raw_content = llm_client.generate(prompt, style_label)
            except TypeError:
                raw_content = llm_client.generate(prompt)
            content = self._post_shape_llm_output(
                raw_content,
                prompt=prompt,
                payload=payload,
                style_label=style_label,
                intent_label=intent_label,
                sections=sections,
                format_rule=format_rule,
                fallback_content=fallback_content,
            )
        return PageRespondResponse(
            response=content,
            style_label=style_label,
            intent_label=intent_label,
            sections=sections,
        )

    def _resolve_sections(self, payload: PageRespondRequest, *, intent_label: str) -> list[str]:
        sections = ["answer", "next_steps"]
        if payload.conversation_mode == "expert":
            sections.insert(1, "collaboration_note")
        if payload.expert_suggestion is not None:
            sections.append("expert_note")
        if payload.ulm_used and payload.ulm_grounding is not None:
            sections.append("grounding_note")
            if payload.ulm_grounding.sources:
                sections.append("source_note")
        if not payload.ulm_used and "No UEX knowledge available." in payload.uex_knowledge:
            sections.append("clarifying_note")
        if intent_label == "clarification" and "clarifying_note" not in sections:
            sections.append("clarifying_note")
        return sections

    @staticmethod
    def _infer_intent(query: str) -> str:
        normalized = (query or "").lower()
        if any(token in normalized for token in {"error", "issue", "problem", "not working", "fail", "disconnect", "broken"}):
            return "troubleshooting"
        if any(token in normalized for token in {"plan", "schedule", "organize", "prepare", "roadmap", "steps"}):
            return "planning"
        if any(token in normalized for token in {"should i", "which", "choose", "better", "decide", "option"}):
            return "decision"
        if any(token in normalized for token in {"what does", "explain", "clarify", "mean", "how does"}):
            return "clarification"
        return "general_guidance"

    def _post_shape_llm_output(
        self,
        raw_content: str,
        *,
        prompt: str,
        payload: PageRespondRequest,
        style_label: str,
        intent_label: str,
        sections: list[str],
        format_rule: dict[str, object] | None,
        fallback_content: str,
    ) -> str:
        del style_label

        content = (raw_content or "").strip()
        if not content:
            return fallback_content

        content = self._strip_prompt_echo(content, prompt)
        content = self._strip_common_artifacts(content)
        content = self._collapse_visible_section_labels(content)
        content = self._normalize_spacing(content)
        content = self._trim_generic_intro_phrases(content)
        content = self._trim_low_signal_tail(content)
        content = self._repair_incomplete_ending(content)
        content = self._reinforce_query_signal(content, payload=payload, intent_label=intent_label)
        content = self._standardize_no_context_response(content, payload=payload)
        content = self._apply_format_rule_post_shape(content, payload=payload, format_rule=format_rule)
        content = self._apply_intent_presentation_post_shape(content, intent_label=intent_label, format_rule=format_rule)

        if self._looks_invalid(content, prompt=prompt, payload=payload):
            return fallback_content

        if len(content) < 60 and len(fallback_content) > len(content):
            return fallback_content

        if "source_note" in sections and payload.ulm_grounding is not None and payload.ulm_grounding.sources:
            source_citations = self._build_source_citations(payload.ulm_grounding.sources)
            if source_citations and not any(citation in content for citation in source_citations[:2]):
                content = f"{content}\n\nExternal sources used: {', '.join(source_citations[:2])}."

        if "expert_note" in sections and payload.expert_suggestion is not None:
            expert_name = payload.expert_suggestion.name
            if expert_name and expert_name not in content and "expert" not in content.lower():
                content = f"{content}\n\nExpert option: {expert_name} may be useful if deeper follow-up is needed."

        return content.strip() or fallback_content

    def _resolve_format_rule(self, mbti: str) -> dict[str, object] | None:
        if len(mbti) != 4:
            return None
        family = f"{mbti[1:]}"
        return self.MBTI_FORMAT_RULES.get(family)

    @staticmethod
    def _describe_format_rule(format_rule: dict[str, object] | None) -> str:
        if not format_rule:
            return "No special formatting rule."
        parts = [
            f"structure={format_rule.get('structure')}",
            f"tone={format_rule.get('tone')}",
        ]
        if format_rule.get("labels"):
            parts.append(f"labels={format_rule.get('labels')}")
        if format_rule.get("options"):
            parts.append("include options")
        if format_rule.get("reasoning"):
            parts.append("show reasoning")
        if format_rule.get("supportive_language"):
            parts.append("use supportive language")
        if format_rule.get("bullet_list"):
            parts.append("use bullet list")
        return ", ".join(parts)

    def _apply_format_rule_post_shape(
        self,
        content: str,
        *,
        payload: PageRespondRequest,
        format_rule: dict[str, object] | None,
    ) -> str:
        if not format_rule:
            return content

        structure = format_rule.get("structure")
        normalized = (content or "").strip()
        if not normalized:
            return normalized

        if structure == "ordered_steps" and "Step 1:" not in normalized:
            return PlaceholderPageRenderer()._format_ordered_steps(
                normalized,
                payload=payload,
                labels=str(format_rule.get("labels") or "Step {n}:"),
            )

        if structure == "quick_actions" and "- " not in normalized:
            return PlaceholderPageRenderer()._format_quick_actions(normalized)

        if structure == "conceptual_analysis" and "Reasoning:" not in normalized:
            return PlaceholderPageRenderer()._format_conceptual_analysis(normalized)

        if structure == "guided_explanation":
            renderer = PlaceholderPageRenderer()
            if "\n\n" not in normalized or "A good next step is to " not in normalized:
                return renderer._format_guided_explanation(normalized)

        return normalized

    def _apply_intent_presentation_post_shape(
        self,
        content: str,
        *,
        intent_label: str,
        format_rule: dict[str, object] | None,
    ) -> str:
        if format_rule:
            return content

        normalized = (content or "").strip()
        if not normalized:
            return normalized

        if intent_label == "troubleshooting" and "- " not in normalized and "Step 1:" not in normalized:
            return PlaceholderPageRenderer()._format_quick_actions(normalized)
        if intent_label == "planning" and "Step 1:" not in normalized:
            return self._format_ordered_steps_generic(normalized, labels="Step {n}:")
        if intent_label == "decision" and "- " not in normalized:
            return PlaceholderPageRenderer()._format_decision_layout(normalized)
        return normalized

    @staticmethod
    def _format_ordered_steps_generic(content: str, *, labels: str) -> str:
        normalized = (content or "").strip()
        if not normalized:
            return normalized

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if sentence.strip()
        ]
        if len(sentences) < 2:
            return normalized

        lines = ["Follow these steps:"]
        note_sentences: list[str] = []
        for sentence in sentences:
            lowered = sentence.lower()
            if lowered.startswith(("if ", "note:", "however", "alternatively")):
                note_sentences.append(sentence)
                continue
            lines.append(f"{labels.format(n=len(lines))} {sentence.rstrip()}")

        if note_sentences:
            lines.append(" ".join(note_sentences))
        return "\n".join(lines)

    @staticmethod
    def _trim_generic_intro_phrases(content: str) -> str:
        cleaned = (content or "").strip()
        patterns = [
            r"^\s*here is a clear response\.\s*",
            r"^\s*the clearest path is this\.\s*",
            r"^\s*the most direct answer is this\.\s*",
            r"^\s*a grounded way to move forward is this\.\s*",
            r"^\s*here is a careful way to approach this\.\s*",
            r"^\s*a helpful way to approach this is:\s*",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _strip_prompt_echo(content: str, prompt: str) -> str:
        cleaned = content.strip()
        prompt_lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        for line in prompt_lines[:12]:
            if cleaned.startswith(line):
                cleaned = cleaned[len(line):].lstrip(" \n:-")
        marker_phrases = [
            f"You are PAGE, the final response composition layer for {settings.app_public_name}.",
            "Rules:",
            "Output format:",
            "User query:",
            "UEX knowledge:",
            "Expert info:",
            "ULM grounding summary:",
            "Required sections:",
            "Preferred style:",
            "Detected intent:",
            "Conversation mode:",
        ]
        lowered = cleaned.lower()
        for marker in marker_phrases:
            idx = lowered.find(marker.lower())
            if idx != -1 and idx < 120:
                cleaned = cleaned[idx + len(marker):].lstrip(" \n:-")
                lowered = cleaned.lower()
        return cleaned.strip()

    @staticmethod
    def _strip_common_artifacts(content: str) -> str:
        cleaned = content
        patterns = [
            r"^\s*(assistant|page|response)\s*:\s*",
            r"^\s*here(?:'s| is) (?:the )?(?:final )?response\s*:\s*",
            r"^\s*here is the response\s*:\s*",
            r"^\s*answer\s*:\s*",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bresponse\s*:\s*", "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(
            r"^(?:\s*-\s*Use .*?\n)+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^(?:\s*-\s*Keep the response .*?\n)+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^(?:\s*-\s*Do not .*?\n)+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^(?:\s*-\s*If .*?\n)+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^\s*-\s*Use the detected intent to guide the structure of the answer\.\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^\s*-\s*If the user query is too vague or lacks context, say so and ask for clarification\.\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^\s*here is the\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"```(?:text)?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^\s*[-*]{3,}\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"(?:\n\s*Best,\s*ULM\.\s*)+$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(?:\n\s*Best,\s*)+$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _collapse_visible_section_labels(content: str) -> str:
        cleaned = content.strip()
        label_patterns = [
            r"^\s*final response\s*:\s*",
            r"^\s*answer\s*:\s*",
            r"^\s*next steps\s*:\s*",
            r"^\s*expert note\s*:\s*",
            r"^\s*grounding note\s*:\s*",
            r"^\s*source note\s*:\s*",
            r"^\s*note\s*:\s*",
        ]
        for pattern in label_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

        blocks = [block.strip() for block in re.split(r"\n\s*\n", cleaned) if block.strip()]
        normalized_blocks: list[str] = []
        for block in blocks:
            block = re.sub(r"^(answer|next steps|expert note|grounding note|source note|note)\s*:\s*", "", block, flags=re.IGNORECASE)
            normalized_blocks.append(block.strip())
        return "\n\n".join(block for block in normalized_blocks if block)

    @staticmethod
    def _normalize_spacing(content: str) -> str:
        cleaned = content.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _trim_low_signal_tail(content: str) -> str:
        tail_markers = [
            "let me know if you want",
            "if you need anything else",
            "i hope this helps",
            "feel free to ask",
        ]
        lowered = content.lower()
        for marker in tail_markers:
            idx = lowered.find(marker)
            if idx != -1 and idx > 120:
                return content[:idx].rstrip()
        return content

    @staticmethod
    def _repair_incomplete_ending(content: str) -> str:
        cleaned = content.strip()
        if not cleaned:
            return cleaned

        dangling_words = {"and", "or", "but", "if", "however", "because", "while", "although"}
        if cleaned[-1] in {",", ";", ":"} or cleaned.split()[-1].lower().rstrip(",;:") in dangling_words:
            sentence_endings = [cleaned.rfind("."), cleaned.rfind("!"), cleaned.rfind("?")]
            last_sentence_end = max(sentence_endings)
            if last_sentence_end > 40:
                return cleaned[: last_sentence_end + 1].rstrip()
            return ""

        if cleaned[-1] not in {".", "!", "?"}:
            return f"{cleaned}."

        return cleaned

    @staticmethod
    def _reinforce_query_signal(content: str, *, payload: PageRespondRequest, intent_label: str) -> str:
        cleaned = (content or "").strip()
        if not cleaned:
            return cleaned

        cleaned = re.sub(
            r"\bdon't have enough relevant context\b",
            "do not have enough relevant context",
            cleaned,
            flags=re.IGNORECASE,
        )

        normalized_query = (payload.query or "").lower()
        normalized_content = cleaned.lower()
        if (
            intent_label == "troubleshooting"
            and "disconnect" in normalized_query
            and "disconnect" not in normalized_content
        ):
            cleaned = f"{cleaned} This is especially relevant if the connection keeps disconnecting."

        return cleaned

    @staticmethod
    def _standardize_no_context_response(content: str, *, payload: PageRespondRequest) -> str:
        cleaned = (content or "").strip()
        if not PageService._should_force_no_context_response(payload):
            return cleaned

        normalized = cleaned.lower()
        if "do not have enough relevant context" in normalized:
            return cleaned

        return PageService._build_no_context_response(payload, cleaned)

    @staticmethod
    def _should_force_no_context_response(payload: PageRespondRequest) -> bool:
        has_uex = bool((payload.uex_knowledge or "").strip()) and payload.uex_knowledge != "No UEX knowledge available."
        has_ulm = payload.ulm_grounding is not None and bool((payload.ulm_grounding.summary or "").strip())
        return not has_uex and not has_ulm

    @staticmethod
    def _build_no_context_response(payload: PageRespondRequest, fallback_content: str | None = None) -> str:
        del payload, fallback_content
        return "I do not have enough relevant context to answer that."

    @staticmethod
    def _looks_invalid(content: str, *, prompt: str, payload: PageRespondRequest) -> bool:
        normalized = content.strip().lower()
        if not normalized:
            return True
        if normalized == prompt.strip().lower():
            return True
        invalid_markers = [
            "you are page",
            "required sections:",
            "output format:",
            "rules:",
            "uex knowledge:",
            "ulm grounding summary:",
        ]
        if sum(marker in normalized for marker in invalid_markers) >= 2:
            return True
        query_fragment = payload.query.strip().lower()
        if query_fragment and len(normalized) <= len(query_fragment) + 10 and query_fragment in normalized:
            return True
        return False

    @staticmethod
    def _canonicalize_source_title(title: str | None) -> str:
        normalized = (title or "").strip()
        if not normalized:
            return ""
        return re.sub(r"\s*\(Chunk\s+\d+/\d+\)\s*$", "", normalized, flags=re.IGNORECASE).strip()

    def _build_source_citations(self, sources: list[PageUlmSource]) -> list[str]:
        citations: list[str] = []
        seen: set[tuple[str, str]] = set()
        for source in sources:
            title = self._canonicalize_source_title(source.title)
            url = (source.url or "").strip()
            if not title and not url:
                continue
            key = (title.lower(), url.lower())
            if key in seen:
                continue
            seen.add(key)
            if title and url:
                citations.append(f"{title} ({url})")
            elif title:
                citations.append(title)
            else:
                citations.append(url)
        return citations


def get_page_service() -> PageService:
    return PageService()


def get_page_llm_client(
    db: Session = Depends(get_db_session),
) -> LocalLlmClient:
    return get_llm_client_from_db(db)
