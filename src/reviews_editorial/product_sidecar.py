"""Executável autossuficiente do núcleo para o Reviews Desktop.

Este módulo preserva a ponte pública existente e acrescenta somente o invólucro
de distribuição: diretórios por usuário, migrações com backup, materialização
dos recursos imutáveis e importação segura de instalações anteriores.
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
import shutil
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .constants import SYSTEM_VERSION
from .io import load_data, sha256_file
from .jobs import create_job as create_editorial_job
from .pipeline import advance_job as advance_editorial_job
from .pipeline import validate_pipeline
from .registry import EditorialRegistry
from .registry_validation import validate_registry
from .ui_bridge import (
    BRIDGE_SCHEMA_VERSION,
    ReviewsUiBridge,
    UiBridgeError,
    envelope,
)
from . import ui_bridge as ui_bridge_module


DESKTOP_VERSION = "0.1.0"
REGISTRY_SCHEMA_VERSION = "1"
PRODUCT_CONTRACT = {
    "desktop_version": DESKTOP_VERSION,
    "core_version": SYSTEM_VERSION,
    "bridge_protocol": BRIDGE_SCHEMA_VERSION,
    "registry_schema": REGISTRY_SCHEMA_VERSION,
}
PRODUCT_CONFIG_VERSION = "1"
MANAGED_RESOURCE_DIRS = (".codex", "editorial", "schemas", "scripts")
MANAGED_RESOURCE_FILES = ("AGENTS.md", "NOTICE.md", "README-OPERACIONAL.md")
LEGACY_SCRIPT_ALLOWLIST = {
    "audit_anti_ai.py",
    "audit_draft.py",
    "create_job.py",
    "document_presenter.py",
    "edition_router.py",
    "extract_evidence.py",
    "humanize_ptbr.py",
    "incorporate_feedback.py",
    "journalistic_framing.py",
    "research_provenance.py",
    "scientific_appraisal.py",
    "validate_feedback.py",
    "validate_framing.py",
    "validate_job.py",
    "validate_schema.py",
    "validate_scientific_appraisal.py",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resource_root() -> Path:
    override = os.environ.get("REVIEWS_RESOURCE_ROOT")
    if override:
        return Path(override).resolve()
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parents[2]


def core_commit() -> str:
    override = os.environ.get("REVIEWS_CORE_COMMIT")
    if override:
        return override
    build_info = resource_root() / "reviews-build-info.json"
    if build_info.is_file():
        try:
            value = json.loads(build_info.read_text(encoding="utf-8")).get(
                "core_commit"
            )
            if isinstance(value, str) and value:
                return value
        except (OSError, json.JSONDecodeError):
            pass
    return "development"


def _is_drive_root(path: Path) -> bool:
    return path.parent == path


def _unsafe_windows_roots() -> list[Path]:
    candidates = [
        os.environ.get("WINDIR"),
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    ]
    return [Path(value).resolve() for value in candidates if value]


def validate_mutable_root(path: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if _is_drive_root(resolved):
        raise UiBridgeError(
            "UNSAFE_STORAGE_PATH",
            f"{label} não pode ser a raiz de uma unidade.",
            action="Escolha uma pasta exclusiva do Reviews.",
            category="usage_error",
        )
    for forbidden in _unsafe_windows_roots():
        if resolved == forbidden or forbidden in resolved.parents:
            raise UiBridgeError(
                "UNSAFE_STORAGE_PATH",
                f"{label} não pode ficar dentro de {forbidden}.",
                action="Use a pasta recomendada em AppData ou Documentos.",
                category="usage_error",
            )
    return resolved


@dataclass(frozen=True)
class ProductPaths:
    data_root: Path
    documents_root: Path
    private_archive_root: Path
    profile_id: str = "default"

    @classmethod
    def from_values(
        cls,
        data_root: str | Path,
        documents_root: str | Path,
        private_archive_root: str | Path | None = None,
        profile_id: str = "default",
    ) -> "ProductPaths":
        if not profile_id or len(profile_id) > 48 or not all(
            character.isascii()
            and (character.isalnum() or character in {"-", "_"})
            for character in profile_id
        ):
            raise UiBridgeError(
                "INVALID_PROFILE_ID",
                "O identificador do perfil local é inválido.",
                action="Use apenas letras, números, hífen e sublinhado.",
                category="usage_error",
            )
        data = validate_mutable_root(Path(data_root), label="O diretório de dados")
        documents = validate_mutable_root(
            Path(documents_root), label="O diretório de documentos"
        )
        private_archive = validate_mutable_root(
            Path(private_archive_root)
            if private_archive_root
            else documents / "private-archive",
            label="O arquivo privado",
        )
        return cls(data, documents, private_archive, profile_id)

    @property
    def database_path(self) -> Path:
        return self.data_root / "database" / "editorial-registry.sqlite3"

    @property
    def backups_root(self) -> Path:
        return self.data_root / "database" / "backups"

    @property
    def editions_root(self) -> Path:
        return self.documents_root / "editions"

    @property
    def runtime_root(self) -> Path:
        return self.data_root / "runtime"

    @property
    def workspace_root(self) -> Path:
        return self.runtime_root / f"core-{SYSTEM_VERSION}" / "workspace"

    @property
    def runtime_bin(self) -> Path:
        return self.runtime_root / "bin"

    @property
    def config_path(self) -> Path:
        return self.data_root / "config.json"

    def as_dict(self) -> dict[str, str]:
        return {
            "data_root": str(self.data_root),
            "documents_root": str(self.documents_root),
            "private_archive_root": str(self.private_archive_root),
            "database_path": str(self.database_path),
            "editions_root": str(self.editions_root),
            "workspace_root": str(self.workspace_root),
            "runtime_bin": str(self.runtime_bin),
            "profile_id": self.profile_id,
        }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _copy_managed_resources(paths: ProductPaths) -> dict[str, Any]:
    source = resource_root()
    workspace = paths.workspace_root
    workspace.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in MANAGED_RESOURCE_DIRS:
        origin = source / name
        destination = workspace / name
        if not origin.is_dir():
            raise UiBridgeError(
                "PACKAGED_RESOURCE_MISSING",
                f"O recurso empacotado {name} não foi localizado.",
                action="Reinstale o Reviews usando um instalador íntegro.",
                category="environment_failure",
            )
        shutil.copytree(origin, destination, dirs_exist_ok=True)
        copied.append(name)
    for name in MANAGED_RESOURCE_FILES:
        origin = source / name
        if origin.is_file():
            shutil.copy2(origin, workspace / name)
            copied.append(name)
    (workspace / "corpus").mkdir(exist_ok=True)
    (workspace / "corpus" / "README.md").write_text(
        "# Corpus local\n\n"
        "O instalador não inclui histórico privado. Importe seus próprios dados "
        "pelo aplicativo; dados demonstrativos permanecem em perfil separado.\n",
        encoding="utf-8",
    )
    manifest = {
        "contract": PRODUCT_CONTRACT,
        "core_commit": core_commit(),
        "materialized_at": utc_now(),
        "managed_resources": copied,
        "private_corpus_included": False,
    }
    _write_json(workspace / "reviews-runtime.json", manifest)
    return manifest


def _ensure_directories(paths: ProductPaths) -> None:
    directories = [
        paths.data_root / "database",
        paths.data_root / "cache",
        paths.data_root / "logs",
        paths.data_root / "diagnostics",
        paths.data_root / "updates",
        paths.data_root / "codex",
        paths.backups_root,
        paths.runtime_bin,
        paths.documents_root,
        paths.editions_root,
        paths.documents_root / "sources",
        paths.private_archive_root,
        paths.documents_root / "exports",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def test_read_write(path: Path) -> dict[str, Any]:
    path.mkdir(parents=True, exist_ok=True)
    marker = path / f".reviews-write-test-{os.getpid()}"
    marker.write_text("reviews", encoding="utf-8")
    observed = marker.read_text(encoding="utf-8")
    marker.unlink()
    return {"path": str(path), "readable": observed == "reviews", "writable": True}


def _known_migrations(database_path: Path) -> set[str]:
    if not database_path.is_file():
        return set()
    try:
        connection = sqlite3.connect(
            f"file:{database_path.as_posix()}?mode=ro",
            uri=True,
        )
        try:
            rows = connection.execute("SELECT version FROM schema_migrations")
            return {str(row[0]) for row in rows}
        finally:
            connection.close()
    except sqlite3.Error:
        return set()


def _pending_migrations(paths: ProductPaths) -> list[str]:
    available = {
        item.name for item in (resource_root() / "migrations").glob("*.sql")
    }
    return sorted(available - _known_migrations(paths.database_path))


def backup_database(paths: ProductPaths, reason: str) -> str | None:
    if not paths.database_path.is_file():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = paths.backups_root / f"registry-{stamp}-{reason}.sqlite3"
    shutil.copy2(paths.database_path, destination)
    return str(destination)


@contextmanager
def runtime_environment(paths: ProductPaths) -> Iterator[None]:
    updates = {
        "REVIEWS_RESOURCE_ROOT": str(resource_root()),
        "REVIEWS_REGISTRY_PATH": str(paths.database_path),
        "REVIEWS_PRIVATE_ARCHIVE_ROOT": str(paths.private_archive_root),
    }
    previous = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def migrate(paths: ProductPaths) -> dict[str, Any]:
    _ensure_directories(paths)
    pending = _pending_migrations(paths)
    backup = backup_database(paths, "pre-migration") if pending else None
    with runtime_environment(paths):
        registry = EditorialRegistry(
            paths.database_path,
            storage_root=paths.private_archive_root,
            migrations_root=resource_root() / "migrations",
        )
        validation = validate_registry(
            registry,
            verify_files=False,
            repository_root=paths.workspace_root,
            require_external_storage=False,
        )
    if not validation.get("passed"):
        raise UiBridgeError(
            "REGISTRY_MIGRATION_INVALID",
            "O registro não passou na validação após a migração.",
            action="Restaure o backup indicado no diagnóstico.",
            category="environment_failure",
            details={"backup": backup, "issues": validation.get("issues", [])},
        )
    return {
        "pending_before": pending,
        "backup": backup,
        "validation": validation,
    }


def _install_python_shim(paths: ProductPaths) -> str | None:
    if not getattr(sys, "frozen", False):
        return None
    destination = paths.runtime_bin / "python.exe"
    source = Path(sys.executable).resolve()
    if destination.exists() and sha256_file(destination) == sha256_file(source):
        return str(destination)
    temporary = destination.with_suffix(".tmp.exe")
    if temporary.exists():
        temporary.unlink()
    try:
        os.link(source, temporary)
    except OSError:
        shutil.copy2(source, temporary)
    temporary.replace(destination)
    return str(destination)


def initialize(paths: ProductPaths, *, actor: str = "reviews-desktop") -> dict[str, Any]:
    _ensure_directories(paths)
    path_checks = [
        test_read_write(paths.data_root),
        test_read_write(paths.documents_root),
        test_read_write(paths.private_archive_root),
    ]
    runtime_manifest = _copy_managed_resources(paths)
    migration = migrate(paths)
    python_shim = _install_python_shim(paths)
    with runtime_environment(paths):
        registry = EditorialRegistry(
            paths.database_path,
            storage_root=paths.private_archive_root,
            migrations_root=resource_root() / "migrations",
        )
        registry.ensure_actor(actor, display_name=actor, role="editor")
    initial_backup = None
    if not migration["backup"]:
        initial_backup = backup_database(paths, "initial")
    config = {
        "config_version": PRODUCT_CONFIG_VERSION,
        "contract": PRODUCT_CONTRACT,
        "core_commit": core_commit(),
        "initialized_at": utc_now(),
        "paths": paths.as_dict(),
        "private_data_packaged": False,
    }
    _write_json(paths.config_path, config)
    return {
        "initialized": True,
        "contract": PRODUCT_CONTRACT,
        "core_commit": core_commit(),
        "paths": paths.as_dict(),
        "path_checks": path_checks,
        "runtime_manifest": runtime_manifest,
        "migration": migration,
        "initial_backup": initial_backup,
        "python_shim": python_shim,
    }


class ProductReviewsUiBridge(ReviewsUiBridge):
    """Ponte existente, vinculada aos diretórios gerenciados pelo produto."""

    def __init__(self, paths: ProductPaths) -> None:
        self.paths = paths
        ui_bridge_module.REPOSITORY_ROOT = paths.workspace_root
        ui_bridge_module.DEFAULT_DB = paths.database_path
        with runtime_environment(paths):
            super().__init__(
                database_path=paths.database_path,
                storage_root=paths.private_archive_root,
            )

    def workspace_info(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.paths.workspace_root),
            "system_version": SYSTEM_VERSION,
            "bridge_schema_version": BRIDGE_SCHEMA_VERSION,
            "registry_schema_version": REGISTRY_SCHEMA_VERSION,
            "desktop_version": DESKTOP_VERSION,
            "core_commit": core_commit(),
            "commit": core_commit(),
            "branch": None,
            "working_tree": {"clean": True, "changed_paths": []},
            "database": str(self.paths.database_path),
            "storage_root": str(self.paths.private_archive_root),
            "jobs_root": str(self.paths.editions_root),
            "documents_root": str(self.paths.documents_root),
            "data_root": str(self.paths.data_root),
            "distribution_mode": "packaged" if getattr(sys, "frozen", False) else "development",
            "roles_are_editorial_gates": True,
            "roles_are_authentication": False,
        }

    def bootstrap(self) -> dict[str, Any]:
        """Entrega a visão inicial em uma única inicialização do sidecar."""

        return {
            "dashboard": self.dashboard(),
            "editions": self.list_editions(),
            "doctor": self.doctor(),
            "validated_memory": self.search_memory("", tier="validated", limit=50),
            "historical_memory": self.search_memory("", tier="historical", limit=50),
            "lessons": self.list_lessons(),
            "classifications": self.list_classification_queue(),
            "drive_imports": self.list_drive_imports(),
            "agent_runs": self.list_agent_runs(),
        }

    def dispatch(
        self, command: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if command == "bootstrap":
            try:
                return envelope(command, data=self.bootstrap())
            except UiBridgeError:
                raise
            except (OSError, ValueError, RuntimeError) as exc:
                raise UiBridgeError(
                    "CORE_OPERATION_FAILED",
                    str(exc),
                    action="Revise o diagnóstico do perfil local.",
                    category="environment_failure",
                    retryable=True,
                ) from exc
        return super().dispatch(command, arguments)

    def doctor(self) -> dict[str, Any]:
        info = self.workspace_info()
        with self.registry.connection() as connection:
            migrations = [
                str(row["version"])
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
        checks = [
            self._doctor_check("sidecar", Path(sys.executable).is_file(), str(sys.executable)),
            self._doctor_check("contract", PRODUCT_CONTRACT == product_version()["contract"]),
            self._doctor_check("workspace", self.paths.workspace_root.is_dir(), str(self.paths.workspace_root)),
            self._doctor_check("database", self.paths.database_path.is_file(), str(self.paths.database_path)),
            self._doctor_check("documents", self.paths.documents_root.is_dir(), str(self.paths.documents_root)),
            self._doctor_check("private_archive", self.paths.private_archive_root.is_dir(), str(self.paths.private_archive_root)),
            self._doctor_check(
                "schemas",
                len(list((self.paths.workspace_root / "schemas").glob("*.schema.json"))) >= 29,
                "schemas versionados disponíveis",
            ),
            self._doctor_check(
                "skills",
                len(list((self.paths.workspace_root / ".codex" / "skills").glob("reviews-*"))) == 11,
                "11 skills esperadas",
            ),
            self._doctor_check("migrations", len(migrations) >= 2, migrations),
            self._doctor_check("private_data_packaged", True, "nenhum corpus privado incluído"),
        ]
        validation = validate_registry(
            self.registry,
            verify_files=False,
            repository_root=self.paths.workspace_root,
            require_external_storage=False,
        )
        checks.append(
            self._doctor_check(
                "registry_integrity",
                bool(validation.get("passed")),
                validation.get("issues") or "registro íntegro",
            )
        )
        return {
            "passed": not any(check["status"] == "error" for check in checks),
            "checks": checks,
            "workspace": info,
            "registry_validation": validation,
        }

    def list_jobs(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for job_file in sorted(self.paths.editions_root.glob("JOB-*/job.yml")):
            payload = load_data(job_file)
            payload["job_dir"] = str(job_file.parent)
            items.append(payload)
        items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
        return {"items": items, "total": len(items)}

    def create_job(
        self,
        *,
        sources: list[str],
        topic: str,
        edition_type: str = "analise",
        editor: str = "Reviews Desktop",
        notes: str | None = None,
        copy_inputs: bool = True,
    ) -> dict[str, Any]:
        if not sources:
            raise UiBridgeError(
                "SOURCE_REQUIRED",
                "Ao menos uma fonte é obrigatória para criar a edição.",
                action="Selecione um ou mais arquivos na pasta de fontes.",
                category="usage_error",
            )
        allowed_roots = [
            self.paths.documents_root.resolve(),
            self.paths.private_archive_root.resolve(),
        ]
        resolved_sources = [Path(source).expanduser().resolve() for source in sources]
        for source in resolved_sources:
            if not source.is_file() or not any(
                source == root or root in source.parents for root in allowed_roots
            ):
                raise UiBridgeError(
                    "UNSAFE_SOURCE_PATH",
                    "Uma fonte está ausente ou fora dos diretórios permitidos.",
                    action="Copie a fonte para Documentos\\Reviews\\sources ou selecione o arquivo privado configurado.",
                    category="usage_error",
                    details={"source": str(source)},
                )
        with runtime_environment(self.paths):
            job_dir = create_editorial_job(
                self.paths.editions_root,
                resolved_sources,
                topic=topic,
                requested_edition_type=edition_type,
                editor=editor,
                notes=notes,
                copy_inputs=copy_inputs,
            )
        return {
            "job_id": job_dir.name,
            "job_dir": str(job_dir),
            "state": "received",
        }

    def validate_job(
        self,
        job_id: str,
        *,
        target_state: str | None = None,
    ) -> dict[str, Any]:
        with runtime_environment(self.paths):
            return validate_pipeline(self._resolve_job(job_id), target_state=target_state)

    def advance_job(
        self,
        job_id: str,
        *,
        target_state: str | None = None,
        actor: str = "reviews-desktop",
        human_approval: bool = False,
    ) -> dict[str, Any]:
        if not target_state:
            raise UiBridgeError(
                "TARGET_STATE_REQUIRED",
                "O próximo estado é obrigatório.",
                action="Selecione o estado imediatamente seguinte.",
                category="usage_error",
            )
        with runtime_environment(self.paths):
            return advance_editorial_job(
                self._resolve_job(job_id),
                target_state,
                actor=actor,
                human_approval=human_approval,
            )

    def _resolve_job(self, job_id: str) -> Path:
        candidate = (self.paths.editions_root / job_id).resolve()
        jobs_root = self.paths.editions_root.resolve()
        if candidate.parent != jobs_root or not (candidate / "job.yml").is_file():
            raise UiBridgeError(
                "JOB_NOT_FOUND",
                "A edição solicitada não existe neste perfil.",
                action="Atualize a lista de edições e tente novamente.",
                category="usage_error",
                details={"job_id": job_id},
            )
        return candidate


def product_version() -> dict[str, Any]:
    return {
        "contract": PRODUCT_CONTRACT,
        "core_commit": core_commit(),
        "python_runtime": sys.version.split()[0],
        "frozen": bool(getattr(sys, "frozen", False)),
        "executable": str(Path(sys.executable).resolve()),
        "resource_root": str(resource_root()),
    }


def create_demo(paths: ProductPaths) -> dict[str, Any]:
    demo_paths = ProductPaths.from_values(
        paths.data_root / "demo",
        paths.documents_root / "demo",
        paths.documents_root / "demo" / "private-archive",
        profile_id="demo",
    )
    initialized = initialize(demo_paths, actor="demo-editor")
    bridge = ProductReviewsUiBridge(demo_paths)
    with bridge.registry.connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM editions").fetchone()[0]
    fixture = None
    if count == 0:
        fixture = bridge.registry.seed_minimum_example(actor_id="demo-editor")
        bridge.registry.register_generated_output(
            edition_id=fixture["edition_id"],
            actor_id="demo-editor",
            agent_name="Codex demonstrativo",
            model="simulação sem rede",
            purpose="Auditoria metodológica sintética",
            prompt="Fixture local: revisar proporcionalidade da conclusão.",
            context={"synthetic": True, "private_data": False},
            configuration={"network": False, "publication": "simulated"},
            result=(
                "Auditoria sintética: a conclusão revisada preserva a incerteza "
                "e explicita a redução energética como explicação concorrente."
            ),
            output_type="audit",
            document_title="Auditoria metodológica — demonstração",
        )
    return {
        "demo": True,
        "synthetic": True,
        "paths": demo_paths.as_dict(),
        "initialized": initialized["initialized"],
        "fixture": fixture,
    }


def import_existing(paths: ProductPaths, arguments: dict[str, Any]) -> dict[str, Any]:
    source_root = Path(str(arguments.get("source_root") or "")).expanduser().resolve()
    if not source_root.is_dir():
        raise UiBridgeError(
            "IMPORT_SOURCE_NOT_FOUND",
            "A instalação existente não foi localizada.",
            action="Selecione a pasta que contém .reviews e jobs.",
            category="usage_error",
        )
    source_db = source_root / ".reviews" / "editorial-registry.sqlite3"
    source_jobs = source_root / "jobs"
    if not source_jobs.is_dir():
        source_jobs = source_root / "editions"
    if not source_db.is_file() or not source_jobs.is_dir():
        raise UiBridgeError(
            "IMPORT_SOURCE_INVALID",
            "A pasta não contém banco e edições reconhecíveis.",
            action="Selecione a raiz da instalação anterior.",
            category="usage_error",
        )
    mode = str(arguments.get("mode") or "copy")
    if mode not in {"copy", "adopt"}:
        raise UiBridgeError(
            "IMPORT_MODE_INVALID",
            "O modo de importação deve ser copy ou adopt.",
            action="Use cópia segura ou adoção explícita.",
            category="usage_error",
        )
    with tempfile.TemporaryDirectory(prefix="reviews-import-check-") as temporary:
        check_db = Path(temporary) / "registry.sqlite3"
        shutil.copy2(source_db, check_db)
        registry = EditorialRegistry(
            check_db,
            storage_root=Path(temporary) / "storage",
            migrations_root=resource_root() / "migrations",
        )
        validation = validate_registry(
            registry,
            verify_files=False,
            repository_root=source_root,
            require_external_storage=False,
        )
    if not validation.get("passed"):
        raise UiBridgeError(
            "IMPORT_VALIDATION_FAILED",
            "A instalação existente não passou na validação.",
            action="Revise o diagnóstico antes de importar.",
            category="environment_failure",
            details={"issues": validation.get("issues", [])},
        )
    if mode == "adopt":
        return {
            "mode": "adopt",
            "source_unchanged": True,
            "database_path": str(source_db),
            "editions_root": str(source_jobs),
            "validation": validation,
        }
    _ensure_directories(paths)
    existing = list(paths.editions_root.glob("JOB-*"))
    if paths.database_path.exists() or existing:
        raise UiBridgeError(
            "IMPORT_DESTINATION_NOT_EMPTY",
            "O perfil de destino já contém dados.",
            action="Crie um perfil vazio ou exporte um backup antes de importar.",
            category="editorial_block",
        )
    backup_root = paths.data_root / "imports" / datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    backup_root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_db, backup_root / source_db.name)
    shutil.copytree(source_jobs, backup_root / "editions")
    shutil.copy2(source_db, paths.database_path)
    shutil.copytree(source_jobs, paths.editions_root, dirs_exist_ok=True)
    migration = migrate(paths)
    return {
        "mode": "copy",
        "source_unchanged": True,
        "backup": str(backup_root),
        "database_sha256": sha256_file(paths.database_path),
        "editions_imported": len(list(paths.editions_root.glob("JOB-*"))),
        "migration": migration,
    }


def smoke_test(paths: ProductPaths) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix="reviews-sidecar-smoke-",
        dir=paths.data_root / "cache" if paths.data_root.exists() else None,
    ) as temporary:
        root = Path(temporary)
        probe = ProductPaths.from_values(
            root / "data",
            root / "documents",
            root / "documents" / "private-archive",
            profile_id="smoke",
        )
        initialized = initialize(probe, actor="smoke-test")
        bridge = ProductReviewsUiBridge(probe)
        doctor = bridge.doctor()
        listing = bridge.dispatch("list-editions")
        return {
            "passed": bool(initialized["initialized"] and doctor["passed"] and listing["ok"]),
            "contract": PRODUCT_CONTRACT,
            "checks": {
                "initialize": initialized["initialized"],
                "doctor": doctor["passed"],
                "bridge": listing["ok"],
                "temporary_storage": True,
            },
        }


def _sidecar_error(command: str, error: Exception) -> tuple[dict[str, Any], int]:
    if isinstance(error, UiBridgeError):
        public = error
    else:
        public = UiBridgeError(
            "SIDECAR_INTERNAL_FAILURE",
            str(error) or type(error).__name__,
            action="Abra o diagnóstico e exporte os logs para suporte.",
            category="internal_failure",
            retryable=False,
        )
    return envelope(command, errors=[public.as_dict()]), 2


def _dispatch_product_command(
    command: str,
    paths: ProductPaths,
    arguments: dict[str, Any],
) -> Any:
    if command == "version":
        return product_version()
    if command == "test-paths":
        return {
            "checks": [
                test_read_write(paths.data_root),
                test_read_write(paths.documents_root),
                test_read_write(paths.private_archive_root),
            ]
        }
    if command == "initialize":
        return initialize(paths, actor=str(arguments.get("actor") or "reviews-desktop"))
    if command == "migrate":
        return migrate(paths)
    if command == "smoke-test":
        return smoke_test(paths)
    if command == "create-demo":
        return create_demo(paths)
    if command == "import-existing":
        return import_existing(paths, arguments)
    if not paths.config_path.is_file():
        raise UiBridgeError(
            "PRODUCT_NOT_INITIALIZED",
            "O Reviews ainda não foi inicializado neste perfil.",
            action="Conclua a primeira execução antes de abrir o acervo.",
            category="environment_failure",
        )
    migrate(paths)
    bridge = ProductReviewsUiBridge(paths)
    return bridge.dispatch(command, arguments)


def _run_legacy_script(argv: list[str]) -> int | None:
    if not argv or not argv[0].lower().endswith(".py"):
        return None
    requested = Path(argv[0]).resolve()
    if requested.name not in LEGACY_SCRIPT_ALLOWLIST:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "SCRIPT_NOT_ALLOWED",
                    "script": requested.name,
                },
                ensure_ascii=False,
            )
        )
        return 2
    allowed_roots = [
        resource_root() / "scripts",
        Path.cwd().resolve() / "scripts",
    ]
    if not requested.is_file() or not any(
        requested.parent == root.resolve() for root in allowed_roots if root.exists()
    ):
        print(
            json.dumps(
                {"ok": False, "error": "SCRIPT_PATH_INVALID"},
                ensure_ascii=False,
            )
        )
        return 2
    sys.argv = [str(requested), *argv[1:]]
    scripts_dir = str(requested.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        runpy.run_path(str(requested), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    legacy_result = _run_legacy_script(raw)
    if legacy_result is not None:
        return legacy_result
    parser = argparse.ArgumentParser(description="Reviews Core sidecar")
    parser.add_argument("--data-root")
    parser.add_argument("--documents-root")
    parser.add_argument("--private-archive-root")
    parser.add_argument("--profile-id", default="default")
    parser.add_argument("command")
    parser.add_argument("--arguments", default="{}")
    args = parser.parse_args(raw)
    command = str(args.command)
    try:
        arguments = json.loads(args.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("--arguments precisa ser um objeto JSON")
        if command == "version" and not args.data_root:
            payload = envelope(command, data=product_version())
        else:
            if not args.data_root or not args.documents_root:
                raise UiBridgeError(
                    "PRODUCT_PATHS_REQUIRED",
                    "Os diretórios de dados e documentos são obrigatórios.",
                    action="Use o aplicativo para escolher os diretórios.",
                    category="usage_error",
                )
            paths = ProductPaths.from_values(
                args.data_root,
                args.documents_root,
                args.private_archive_root,
                args.profile_id,
            )
            result = _dispatch_product_command(command, paths, arguments)
            payload = (
                result
                if isinstance(result, dict)
                and result.get("schema_version") == BRIDGE_SCHEMA_VERSION
                else envelope(command, data=result)
            )
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("ok") else 2
    except (UiBridgeError, OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        payload, code = _sidecar_error(command, error)
        print(json.dumps(payload, ensure_ascii=False))
        return code


if __name__ == "__main__":
    raise SystemExit(main())
