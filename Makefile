.PHONY: chat check parse index generate-eval evaluate evaluate-retrieval

chat:
	./scripts/uv run --locked warhammer-rag chat
check:
	./scripts/check.sh
parse:
	./scripts/uv run --locked warhammer-rag parse
index:
	./scripts/uv run --locked warhammer-rag index
generate-eval:
	./scripts/uv run --locked warhammer-rag generate-eval --output evaluation/reports/text-draft.json
evaluate:
	./scripts/uv run --locked warhammer-rag evaluate-answers
evaluate-retrieval:
	./scripts/uv run --locked warhammer-rag evaluate-retrieval
