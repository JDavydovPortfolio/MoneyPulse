"""Headless entry point: python -m src.cli {doctor,process}."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from .config import DEFAULT_CONFIG, PROVIDERS, load_config, validate_config
from .ocr import SUPPORTED_EXTENSIONS
from .pipeline import DocumentPipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="MoneyPulse local document processing. All extractions require human review.")
    parser.add_argument("command", choices=("doctor", "process"))
    parser.add_argument("inputs", nargs="*", help="Document paths or directories (process only)")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--provider", choices=sorted(PROVIDERS))
    parser.add_argument("--host")
    parser.add_argument("--model", help="Exact identifier exposed by your provider")
    parser.add_argument("--output", default="output")
    args = parser.parse_args(argv)
    try:
        if args.command == "process" and not args.inputs:
            parser.error("process requires at least one document or directory")
        if args.command == "doctor" and args.inputs:
            parser.error("doctor does not accept input documents")
        if not Path(args.config).exists() and args.config != "config.yaml":
            raise ValueError(f"Configuration file not found: {args.config}")
        config = {**DEFAULT_CONFIG, **load_config(args.config)}
        for option, key in ((args.provider, "llm_provider"), (args.host, "llm_host"), (args.model, "model")):
            if option is not None:
                config[key] = option
        validate_config(config)
        paths = []
        for item in args.inputs:
            path = Path(item)
            if not path.exists():
                raise ValueError(f"Input path not found: {path}")
            candidates = sorted(path.iterdir()) if path.is_dir() else [path]
            for candidate in candidates:
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
                    if candidate.resolve() not in paths:
                        paths.append(candidate.resolve())
                elif not path.is_dir():
                    raise ValueError(f"Unsupported input: {path}")
        if args.command == "process" and not paths:
            raise ValueError("No supported PDF, PNG, JPG, or JPEG documents found")
        pipeline = DocumentPipeline(output_dir=args.output, config=config)
        checks = pipeline.test_system_components()
        needs_pdf = args.command == "doctor" or any(path.suffix.lower() == ".pdf" for path in paths)
        if needs_pdf:
            missing = [tool for tool in ("pdfinfo", "pdftoppm") if not shutil.which(tool)]
            checks["pdf_renderer"] = {"status": "error" if missing else "ok", "details": f"Missing: {', '.join(missing)}" if missing else "Poppler is on PATH"}
        if args.command == "doctor" or any(check["status"] != "ok" for check in checks.values()):
            print(json.dumps({"component_checks": checks}, indent=2))
            return int(any(check["status"] != "ok" for check in checks.values()))
        documents = [pipeline.process_single_document(str(path)) for path in paths]
        csv_path = pipeline.crm.generate_csv_summary(documents)
        print(json.dumps({
            "documents": [{key: doc.get(key) for key in ("source_file", "processing_status", "validation_status", "review_state", "output_result", "error")} for doc in documents],
            "csv_file": csv_path,
            "destination": "local_only",
        }, indent=2))
        return int(any(doc.get("processing_status") != "completed" or doc.get("validation_status") != "passed" for doc in documents))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"MoneyPulse: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
