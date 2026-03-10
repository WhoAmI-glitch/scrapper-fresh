---
name: prompt-engineering
description: Design and optimize prompts for LLM applications using structured outputs, chain-of-thought, few-shot learning, and template systems. Use when optimizing prompts, improving LLM output quality, designing production prompt templates, or implementing structured reasoning patterns.
---

# Prompt Engineering Patterns

Maximize LLM performance, reliability, and controllability through proven prompting techniques.

## Core Techniques

### 1. Structured Outputs with Pydantic

Enforce reliable, parseable responses with schema enforcement:

```python
from pydantic import BaseModel, Field
from typing import Literal

class SentimentAnalysis(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0, le=1)
    key_phrases: list[str]
    reasoning: str
```

Use `llm.with_structured_output(Schema)` or instruct the model to respond in JSON matching your schema.

### 2. Chain-of-Thought with Self-Verification

Elicit step-by-step reasoning and self-checking:

```
Solve this problem step by step.

Problem: {problem}

Instructions:
1. Break down the problem into clear steps
2. Work through each step showing your reasoning
3. State your final answer
4. Verify your answer by checking it against the original problem
```

Zero-shot CoT: append "Let's think step by step" to any prompt.

### 3. Few-Shot with Dynamic Example Selection

Select examples by semantic similarity to the input:

```python
example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples=[
        {"input": "How do I reset my password?", "output": "Go to Settings > Security > Reset Password"},
        {"input": "Where can I see my order history?", "output": "Navigate to Account > Orders"},
    ],
    embeddings=embeddings,
    vectorstore_cls=Chroma,
    k=2
)
```

### 4. Progressive Disclosure

Start simple, add complexity only when needed:

- **Level 1**: Direct instruction -- "Summarize this article: {text}"
- **Level 2**: Add constraints -- bullet points, focus areas
- **Level 3**: Add reasoning steps -- identify thesis, extract points, then summarize
- **Level 4**: Add examples -- show input/output pairs before the task

### 5. Error Recovery and Fallback

Handle malformed outputs gracefully:

```python
try:
    response = await llm.ainvoke(structured_prompt)
    return Schema(**json.loads(response.content))
except (json.JSONDecodeError, ValidationError):
    simple_response = await llm.ainvoke(fallback_prompt)
    return Schema(answer=simple_response.content, confidence=0.5, sources=["fallback"])
```

### 6. Role-Based System Prompts

Define expertise, responsibilities, communication style, and constraints:

```python
SYSTEM_PROMPTS = {
    "analyst": """You are a senior data analyst. Write efficient queries.
    Explain methodology. Highlight insights. Flag data quality concerns.""",

    "code_reviewer": """You are a senior engineer conducting code reviews.
    Assess: correctness, security, performance, maintainability.
    Output: summary, critical issues, suggestions, positive feedback.""",
}
```

## Integration with RAG

```
Answer based on the provided context. If you cannot answer, say so.
Cite specific passages using [1], [2] notation.
If the question is ambiguous, ask for clarification.

Context:
{context}

Question: {question}
```

## Token Efficiency

```python
# Verbose (150+ tokens)
"I would like you to please take the following text and provide me with
a comprehensive summary of the main points..."

# Concise (30 tokens)
"Summarize the key points concisely:\n\n{text}\n\nSummary:"
```

Use prompt caching for repeated system prompts:

```python
system=[{
    "type": "text",
    "text": LONG_SYSTEM_PROMPT,
    "cache_control": {"type": "ephemeral"}
}]
```

## Best Practices

1. **Be specific** -- vague prompts produce inconsistent results
2. **Show, don't tell** -- examples outperform descriptions
3. **Use structured outputs** -- enforce schemas for reliability
4. **Test extensively** -- evaluate on diverse, representative inputs
5. **Iterate rapidly** -- small changes can have large impacts
6. **Version control prompts** -- treat them as code
7. **Document intent** -- explain why prompts are structured as they are

## Common Pitfalls

- Over-engineering prompts before trying simple ones
- Using examples that don't match the target task
- Exceeding token limits with excessive context
- Leaving room for multiple interpretations
- Assuming outputs will always be well-formed
- Not parameterizing prompts for reuse

## Success Metrics

Track these KPIs: accuracy, consistency across inputs, latency (P50/P95/P99), token usage per request, success rate of parseable outputs, user satisfaction.
