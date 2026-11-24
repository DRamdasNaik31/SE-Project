"""Genuine LoRA/QLoRA fine-tuning entry point for Agent 1.

This command requires the optional ML dependencies and a reviewed base-model
license/configuration. It does not silently fall back to prompting.
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=Path("data/training/train.jsonl"))
    parser.add_argument("--validation", type=Path, default=Path("data/training/validation.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("models/agent1_lora"))
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--epochs", type=float, default=1.0)
    args = parser.parse_args()
    if not args.train.is_file() or not args.validation.is_file():
        raise SystemExit("Training and validation JSONL files are required.")
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit("Install requirements-ml.txt before running genuine PEFT training.") from exc

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = None
    if torch.cuda.is_available():
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quantization,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    peft_model = get_peft_model(
        model,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules="all-linear",
            task_type=TaskType.CAUSAL_LM,
        ),
    )

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train), "validation": str(args.validation)},
    )

    def format_row(row: dict[str, object]) -> dict[str, str]:
        return {
            "text": (
                "Instruction:\n" + str(row["instruction"]) +
                "\nEvidence:\n" + str(row["context"]) +
                "\nResponse:\n" + json.dumps(row["response"], ensure_ascii=False)
            )
        }

    formatted = dataset.map(format_row)

    def tokenize(batch: dict[str, list[str]]) -> dict[str, object]:
        return tokenizer(batch["text"], truncation=True, max_length=768)

    tokenized = formatted.map(tokenize, batched=True, remove_columns=formatted["train"].column_names)
    args.output.mkdir(parents=True, exist_ok=True)
    trainer = Trainer(
        model=peft_model,
        args=TrainingArguments(
            output_dir=str(args.output),
            num_train_epochs=args.epochs,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=2e-4,
            logging_steps=5,
            eval_strategy="epoch",
            save_strategy="epoch",
            fp16=torch.cuda.is_available(),
            report_to="none",
        ),
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    peft_model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"Saved genuine LoRA adapter to {args.output}")


if __name__ == "__main__":
    main()
