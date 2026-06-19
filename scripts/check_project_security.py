"""Run lightweight local checks for secrets and unsafe project artifacts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".terraform",
    ".venv",
    "__pycache__",
    "build",
    "cdk.out",
    "dist",
    "env",
    "htmlcov",
    "node_modules",
    "out",
    "venv",
}

ALLOWED_ENV_EXAMPLES = {
    ".env.example",
    ".env.example.local",
    "env.example",
}

REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".env.*",
    "!.env.example",
    "!.env.example.local",
    "*.pem",
    "*.key",
    "apps/api/storage/local_uploads/",
    "apps/api/storage/local_queue/",
]

SECRET_PATTERNS = [
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "aws_secret_access_key",
        re.compile(
            r"(?i)\baws_secret_access_key\s*=\s*(?!example|placeholder|fictitious)[^\s#]+"
        ),
    ),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("openai_api_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("jwt_literal", re.compile(r"Bearer\s+eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]


def should_skip_dir(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(SKIP_DIRS):
        return True

    normalized = "/".join(path.parts).replace("\\", "/")
    return (
        "apps/api/storage/local_uploads" in normalized
        or "apps/api/storage/local_queue" in normalized
    )


def is_text_file(path: Path) -> bool:
    if path.stat().st_size > 2_000_000:
        return False

    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    return True


def check_gitignore(root: Path, errors: list[str]) -> None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        errors.append(".gitignore nao encontrado na raiz do projeto")
        return

    content = gitignore.read_text(encoding="utf-8")
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        if pattern not in content:
            errors.append(f".gitignore nao contem padrao obrigatorio: {pattern}")


def check_sensitive_filenames(root: Path, warnings: list[str]) -> None:
    for path in root.rglob("*"):
        if path.is_dir():
            continue

        relative = path.relative_to(root)
        if should_skip_dir(relative.parent):
            continue

        name = path.name.lower()
        suffix = path.suffix.lower()

        if name.startswith(".env") and name not in ALLOWED_ENV_EXAMPLES:
            warnings.append(
                f"arquivo de ambiente local encontrado, confirme que esta ignorado: {relative}"
            )
        elif name in {"credentials", "credentials.json"}:
            warnings.append(f"arquivo de credenciais suspeito encontrado: {relative}")
        elif suffix in {".pem", ".p12", ".pfx", ".key"}:
            warnings.append(f"arquivo de chave/certificado suspeito encontrado: {relative}")


def check_secret_patterns(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if path.is_dir():
            continue

        relative = path.relative_to(root)
        if should_skip_dir(relative.parent):
            continue

        if not is_text_file(path):
            continue

        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{relative}:{line_number}: possivel segredo: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    check_gitignore(root, errors)
    check_sensitive_filenames(root, warnings)
    check_secret_patterns(root, errors)

    for warning in warnings:
        print(f"AVISO: {warning}")

    if errors:
        for error in errors:
            print(f"ERRO: {error}")
        return 1

    print("OK: nenhuma evidencia bloqueante de segredo ou arquivo sensivel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
