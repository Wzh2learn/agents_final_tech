"""Deterministic M1 extraction baseline for local demonstrations."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


RunMode = Literal["local-rule-baseline"]
ReviewDecision = Literal["approved", "needs_review"]


SAMPLE_DOCUMENT = """文件名称：金融业务规则样例-开户与支付审核

规则一：企业客户开户资料核验
适用场景：企业客户首次开户、变更经办人或补充受益所有人信息。
触发条件：当客户类型为企业且开户申请进入初审环节时，系统必须核验营业执照、法定代表人证件、授权书和受益所有人声明。
执行动作：如果任一关键材料缺失或证件有效期小于30天，则将申请标记为need_human_review并推送人工复核；材料完整时允许进入风险评级。
配置参数：证件有效期阈值=30天；关键材料缺失容忍数=0。
注意事项：来源页码和段落编号必须进入M2知识库，便于客服问答时追溯证据。

规则二：重复发票与异常报销拦截
适用场景：费用报销、供应商付款和月度财务审计。
触发条件：当发票号码、销方税号和金额同时命中历史记录，或同一供应商在7天内提交三张以上同金额发票时，触发重复或异常候选。
执行动作：系统应暂停自动付款，生成异常事件，并要求业务负责人补充合同、验收单或付款说明。
配置参数：时间窗口=7天；同金额阈值=3张；相似金额容差=1%。
注意事项：金额字段必须保留原始文本和标准化数值两个版本。

规则三：大额对公转账审批
适用场景：对公转账、批量付款和资金划拨。
触发条件：单笔金额大于等于500000元，或收款方风险等级为高，或付款账户当日累计转出超过2000000元。
执行动作：系统需要追加二级审批，并在审批意见中展示命中的金额、账户、收款方和风险等级证据。
配置参数：单笔阈值=500000元；日累计阈值=2000000元；高风险收款方=必须人工审批。
注意事项：若缺少收款方风险等级，则不得自动通过，应标记为need_human_review。
"""


class SourceEvidence(BaseModel):
    """Evidence location for a parsed rule."""

    page_no: int = Field(default=1, ge=1)
    paragraph_no: int = Field(ge=1)
    quote: str = Field(min_length=6, max_length=500)


class ExtractedRule(BaseModel):
    """Structured M1 rule that can enter review or M2 ingestion."""

    rule_id: str = Field(pattern=r"^M1-[0-9A-F]{8}$")
    rule_name: str = Field(min_length=2, max_length=80)
    scenario: str = Field(min_length=2, max_length=300)
    trigger_condition: str = Field(min_length=8, max_length=600)
    action: str = Field(min_length=8, max_length=600)
    parameters: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    source: SourceEvidence
    confidence: float = Field(ge=0, le=1)
    need_human_review: bool


class PipelineStage(BaseModel):
    """Visible progress state for the M1 demo page."""

    key: str
    label: str
    status: Literal["passed", "warning", "failed"]
    duration_ms: int
    detail: str


class ValidationSummary(BaseModel):
    """Schema validation results shown in the UI."""

    passed: int
    failed: int
    warnings: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


class M2Payload(BaseModel):
    """Compact handoff object for the M2 knowledge-building step."""

    document_id: str
    chunks: list[dict[str, Any]]
    records: list[dict[str, Any]]


class M1ExtractionRequest(BaseModel):
    """Request body for local M1 extraction."""

    document_name: str = Field(default="local-demo-document", max_length=120)
    text: str = Field(min_length=20, max_length=20000)
    mode: RunMode = "local-rule-baseline"


class M1ExtractionResponse(BaseModel):
    """Full M1 demo response."""

    status: Literal["success", "needs_review"]
    run_mode: RunMode
    document_id: str
    document_name: str
    disclaimer: str
    stages: list[PipelineStage]
    metrics: dict[str, Any]
    rules: list[ExtractedRule]
    validation: ValidationSummary
    m2_payload: M2Payload


class M1ReviewRequest(BaseModel):
    """Human review update for a single extracted rule."""

    rule: ExtractedRule
    decision: ReviewDecision
    reviewer_note: str = Field(default="", max_length=500)


class M1ReviewResponse(BaseModel):
    """Review result without persistence."""

    status: Literal["success"]
    persisted: bool = False
    rule: ExtractedRule
    review: dict[str, Any]


class M1Service:
    """Local deterministic M1 baseline used before GB10 OCR/VLM validation."""

    def sample_document(self) -> dict[str, str]:
        """Return the built-in demo document."""
        return {
            "document_name": "financial_rules_m1_demo.txt",
            "text": SAMPLE_DOCUMENT,
        }

    def extract(self, request: M1ExtractionRequest) -> M1ExtractionResponse:
        """Extract structured rules from pasted text or a text file."""
        started = time.perf_counter()
        paragraphs = self._paragraphs(request.text)
        document_id = self._document_id(request.document_name, request.text)

        stages = [
            self._stage("document_loaded", "文档载入", "passed", started, f"{len(request.text)} chars"),
            self._stage("text_parsed", "段落切分", "passed", started, f"{len(paragraphs)} paragraphs"),
        ]

        raw_rules = self._candidate_blocks(paragraphs)
        parsed_rules: list[ExtractedRule] = []
        validation_errors: list[dict[str, Any]] = []

        for index, block in enumerate(raw_rules, start=1):
            candidate = self._parse_block(document_id, index, block)
            try:
                parsed_rules.append(ExtractedRule.model_validate(candidate))
            except ValidationError as exc:
                validation_errors.append({"candidate": candidate.get("rule_name", f"rule-{index}"), "errors": exc.errors()})

        review_count = sum(1 for rule in parsed_rules if rule.need_human_review)
        schema_status = "warning" if validation_errors or review_count else "passed"
        stages.extend(
            [
                self._stage("rules_extracted", "规则抽取", "passed", started, f"{len(parsed_rules)} rules"),
                self._stage("schema_validated", "Pydantic校验", schema_status, started, f"{len(validation_errors)} errors"),
                self._stage("m2_payload_ready", "M2载荷生成", "passed", started, f"{len(parsed_rules)} records"),
            ]
        )

        m2_payload = self._build_m2_payload(document_id, parsed_rules)
        metrics = self._metrics(request.text, paragraphs, parsed_rules, validation_errors)
        return M1ExtractionResponse(
            status="needs_review" if review_count or validation_errors else "success",
            run_mode=request.mode,
            document_id=document_id,
            document_name=request.document_name,
            disclaimer="本地展示使用确定性规则基线；OCR、版面解析、VLM和开源模型效果需要在GB10逐项验证。",
            stages=stages,
            metrics=metrics,
            rules=parsed_rules,
            validation=ValidationSummary(
                passed=len(parsed_rules),
                failed=len(validation_errors),
                warnings=review_count,
                errors=validation_errors,
            ),
            m2_payload=m2_payload,
        )

    def review(self, request: M1ReviewRequest) -> M1ReviewResponse:
        """Apply a non-persistent human review decision."""
        rule = request.rule.model_copy(update={"need_human_review": request.decision == "needs_review"})
        return M1ReviewResponse(
            status="success",
            persisted=False,
            rule=rule,
            review={
                "decision": request.decision,
                "reviewer_note": request.reviewer_note,
                "message": "演示模式仅返回更新后的规则，正式流程需保存到人工复核表。",
            },
        )

    def _paragraphs(self, text: str) -> list[dict[str, Any]]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]
        if len(parts) <= 1:
            parts = [part.strip() for part in re.split(r"\n+", normalized) if part.strip()]
        return [{"paragraph_no": idx, "text": part} for idx, part in enumerate(parts, start=1)]

    def _candidate_blocks(self, paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        title_pattern = re.compile(r"^(规则[一二三四五六七八九十\d]+[:：]|Rule\s*\d+[:：]?)", re.IGNORECASE)

        for paragraph in paragraphs:
            text = paragraph["text"]
            if title_pattern.search(text):
                if current:
                    blocks.append(current)
                current = {"paragraph_no": paragraph["paragraph_no"], "text": text}
            elif current:
                current["text"] += "\n" + text
            # Paragraphs before the first rule heading are document preamble; skip them.


        if current:
            blocks.append(current)
        return blocks or [{"paragraph_no": 1, "text": ""}]

    def _parse_block(self, document_id: str, index: int, block: dict[str, Any]) -> dict[str, Any]:
        text = block["text"].strip()
        labels = {
            "scenario": self._field(text, "适用场景"),
            "trigger_condition": self._field(text, "触发条件"),
            "action": self._field(text, "执行动作"),
            "parameters": self._field(text, "配置参数"),
            "cautions": self._field(text, "注意事项"),
        }
        name_match = re.search(r"^(规则[一二三四五六七八九十\d]+[:：]\s*)?(?P<name>[^\n：:]{2,80})", text)
        rule_name = name_match.group("name").strip() if name_match else f"候选规则{index}"

        fallback = re.sub(r"\s+", " ", text)[:260]
        missing = [key for key in ("trigger_condition", "action") if not labels[key]]
        confidence = 0.92 - (0.16 * len(missing))
        if not labels["scenario"]:
            confidence -= 0.06

        digest = hashlib.sha1(f"{document_id}:{index}:{rule_name}".encode("utf-8")).hexdigest()[:8].upper()
        return {
            "rule_id": f"M1-{digest}",
            "rule_name": rule_name,
            "scenario": labels["scenario"] or "需人工确认适用场景",
            "trigger_condition": labels["trigger_condition"] or fallback,
            "action": labels["action"] or "需人工补充执行动作",
            "parameters": self._split_items(labels["parameters"]),
            "cautions": self._split_items(labels["cautions"]),
            "source": {
                "page_no": 1,
                "paragraph_no": block["paragraph_no"],
                "quote": fallback,
            },
            "confidence": max(0.4, min(0.98, round(confidence, 2))),
            "need_human_review": bool(missing) or confidence < 0.82,
        }

    def _field(self, text: str, label: str) -> str:
        pattern = re.compile(rf"{label}[:：]\s*(?P<value>.*?)(?=\n\S+[:：]|\Z)", re.S)
        match = pattern.search(text)
        return re.sub(r"\s+", " ", match.group("value")).strip() if match else ""

    def _split_items(self, value: str) -> list[str]:
        if not value:
            return []
        return [item.strip(" ；;，,") for item in re.split(r"[；;]\s*", value) if item.strip(" ；;，,")]

    def _build_m2_payload(self, document_id: str, rules: list[ExtractedRule]) -> M2Payload:
        chunks = []
        records = []
        for rule in rules:
            evidence = rule.source.model_dump()
            chunks.append(
                {
                    "chunk_id": f"{document_id}:{rule.rule_id}",
                    "text": f"{rule.rule_name}\n触发条件：{rule.trigger_condition}\n执行动作：{rule.action}",
                    "metadata": {"document_id": document_id, "rule_id": rule.rule_id, "source": evidence},
                }
            )
            records.append(rule.model_dump())
        return M2Payload(document_id=document_id, chunks=chunks, records=records)

    def _metrics(
        self,
        text: str,
        paragraphs: list[dict[str, Any]],
        rules: list[ExtractedRule],
        validation_errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total_rules = len(rules) + len(validation_errors)
        reviewed = sum(1 for rule in rules if rule.need_human_review)
        with_source = sum(1 for rule in rules if rule.source.quote)
        return {
            "chars": len(text),
            "paragraphs": len(paragraphs),
            "rules": len(rules),
            "schema_pass_rate": round(len(rules) / total_rules, 3) if total_rules else 0,
            "source_coverage_rate": round(with_source / len(rules), 3) if rules else 0,
            "human_review_rate": round(reviewed / len(rules), 3) if rules else 0,
        }

    def _stage(self, key: str, label: str, status: Literal["passed", "warning", "failed"], started: float, detail: str) -> PipelineStage:
        return PipelineStage(
            key=key,
            label=label,
            status=status,
            duration_ms=max(1, int((time.perf_counter() - started) * 1000)),
            detail=detail,
        )

    def _document_id(self, document_name: str, text: str) -> str:
        digest = hashlib.sha1(f"{document_name}:{text}".encode("utf-8")).hexdigest()[:10]
        return f"doc_{digest}"


def get_m1_service() -> M1Service:
    """Create an M1 service instance."""
    return M1Service()
