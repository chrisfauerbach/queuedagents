from dataclasses import dataclass, field


@dataclass
class CatalogVariant:
    tag: str
    parameter_size: str


@dataclass
class CatalogModel:
    name: str
    description: str
    category: str
    variants: list[CatalogVariant] = field(default_factory=list)


CATALOG: list[CatalogModel] = [
    # General Purpose
    CatalogModel(
        name="llama3.1",
        description="Meta's Llama 3.1 — strong general-purpose model with large context window",
        category="General Purpose",
        variants=[
            CatalogVariant("8b", "8B"),
            CatalogVariant("70b", "70B"),
            CatalogVariant("405b", "405B"),
        ],
    ),
    CatalogModel(
        name="llama3.2",
        description="Meta's Llama 3.2 — lightweight and efficient general-purpose model",
        category="General Purpose",
        variants=[
            CatalogVariant("1b", "1B"),
            CatalogVariant("3b", "3B"),
        ],
    ),
    CatalogModel(
        name="gemma3",
        description="Google's Gemma 3 — compact and capable open model",
        category="General Purpose",
        variants=[
            CatalogVariant("1b", "1B"),
            CatalogVariant("4b", "4B"),
            CatalogVariant("12b", "12B"),
            CatalogVariant("27b", "27B"),
        ],
    ),
    CatalogModel(
        name="mistral",
        description="Mistral 7B — fast and efficient with strong instruction following",
        category="General Purpose",
        variants=[
            CatalogVariant("7b", "7B"),
        ],
    ),
    CatalogModel(
        name="command-r",
        description="Cohere Command R — optimized for RAG and tool use",
        category="General Purpose",
        variants=[
            CatalogVariant("35b", "35B"),
        ],
    ),
    # Code
    CatalogModel(
        name="qwen2.5-coder",
        description="Qwen 2.5 Coder — specialized for code generation and understanding",
        category="Code",
        variants=[
            CatalogVariant("1.5b", "1.5B"),
            CatalogVariant("7b", "7B"),
            CatalogVariant("14b", "14B"),
            CatalogVariant("32b", "32B"),
        ],
    ),
    CatalogModel(
        name="deepseek-coder-v2",
        description="DeepSeek Coder V2 — high-performance code model",
        category="Code",
        variants=[
            CatalogVariant("16b", "16B"),
        ],
    ),
    CatalogModel(
        name="codellama",
        description="Meta's Code Llama — fine-tuned for code tasks",
        category="Code",
        variants=[
            CatalogVariant("7b", "7B"),
            CatalogVariant("13b", "13B"),
            CatalogVariant("34b", "34B"),
        ],
    ),
    # Reasoning
    CatalogModel(
        name="deepseek-r1",
        description="DeepSeek R1 — strong reasoning with chain-of-thought",
        category="Reasoning",
        variants=[
            CatalogVariant("1.5b", "1.5B"),
            CatalogVariant("7b", "7B"),
            CatalogVariant("8b", "8B"),
            CatalogVariant("14b", "14B"),
            CatalogVariant("32b", "32B"),
            CatalogVariant("70b", "70B"),
        ],
    ),
    CatalogModel(
        name="qwq",
        description="Qwen QwQ — reasoning-focused model with step-by-step thinking",
        category="Reasoning",
        variants=[
            CatalogVariant("32b", "32B"),
        ],
    ),
    # Chat/Instruct
    CatalogModel(
        name="phi4",
        description="Microsoft Phi-4 — small but capable chat model",
        category="Chat/Instruct",
        variants=[
            CatalogVariant("14b", "14B"),
        ],
    ),
    CatalogModel(
        name="phi3.5",
        description="Microsoft Phi-3.5 — efficient instruction-tuned model",
        category="Chat/Instruct",
        variants=[
            CatalogVariant("3.8b", "3.8B"),
        ],
    ),
    # Small/Fast
    CatalogModel(
        name="tinyllama",
        description="TinyLlama — ultra-compact 1.1B model for fast inference",
        category="Small/Fast",
        variants=[
            CatalogVariant("1.1b", "1.1B"),
        ],
    ),
    CatalogModel(
        name="qwen2.5",
        description="Qwen 2.5 — versatile model available in many sizes",
        category="Small/Fast",
        variants=[
            CatalogVariant("0.5b", "0.5B"),
            CatalogVariant("1.5b", "1.5B"),
            CatalogVariant("3b", "3B"),
            CatalogVariant("7b", "7B"),
            CatalogVariant("14b", "14B"),
            CatalogVariant("32b", "32B"),
            CatalogVariant("72b", "72B"),
        ],
    ),
    # Multilingual
    CatalogModel(
        name="aya",
        description="Cohere Aya — multilingual model supporting 100+ languages",
        category="Multilingual",
        variants=[
            CatalogVariant("8b", "8B"),
            CatalogVariant("35b", "35B"),
        ],
    ),
]
