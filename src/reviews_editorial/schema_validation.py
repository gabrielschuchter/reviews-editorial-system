"""Validador pequeno para o subconjunto de JSON Schema usado pelo projeto."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


TYPE_CHECKS = {
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "null": lambda value: value is None,
}


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"somente referências JSON Pointer locais são suportadas: {reference}")
    node: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"$ref não resolvido: {reference}")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"$ref não aponta para um schema: {reference}")
    return node


def _format_valid(value: str, format_name: str) -> bool:
    try:
        if format_name == "date-time":
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        if format_name == "date":
            date.fromisoformat(value)
            return True
        if format_name == "uri":
            parsed = urlparse(value)
            return bool(parsed.scheme and (parsed.netloc or parsed.scheme == "urn"))
    except ValueError:
        return False
    return True


def validate(
    instance: Any,
    schema: dict[str, Any],
    path: str = "$",
    *,
    root_schema: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    """Validar o subconjunto de JSON Schema usado nos contratos do projeto."""

    root = root_schema or schema
    issues: list[ValidationIssue] = []
    if reference := schema.get("$ref"):
        try:
            referenced = _resolve_local_ref(root, reference)
        except ValueError as exc:
            return [ValidationIssue(path, str(exc))]
        issues.extend(validate(instance, referenced, path, root_schema=root))

    declared_type = schema.get("type")
    if declared_type:
        accepted = declared_type if isinstance(declared_type, list) else [declared_type]
        unknown_types = [kind for kind in accepted if kind not in TYPE_CHECKS]
        if unknown_types:
            return [ValidationIssue(path, f"tipo(s) de schema desconhecido(s): {unknown_types}")]
        if not any(TYPE_CHECKS[kind](instance) for kind in accepted):
            return [ValidationIssue(path, f"tipo inválido; esperado {accepted}")]

    if "const" in schema and instance != schema["const"]:
        issues.append(ValidationIssue(path, f"valor deve ser {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        issues.append(ValidationIssue(path, f"valor fora do enum permitido: {schema['enum']}"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            issues.append(ValidationIssue(path, "texto menor que minLength"))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            issues.append(ValidationIssue(path, "texto maior que maxLength"))
        if pattern := schema.get("pattern"):
            if re.search(pattern, instance) is None:
                issues.append(ValidationIssue(path, f"texto não corresponde ao padrão {pattern!r}"))
        if format_name := schema.get("format"):
            if not _format_valid(instance, str(format_name)):
                issues.append(ValidationIssue(path, f"texto não corresponde ao formato {format_name}"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            issues.append(ValidationIssue(path, f"valor abaixo de {schema['minimum']}"))
        if "maximum" in schema and instance > schema["maximum"]:
            issues.append(ValidationIssue(path, f"valor acima de {schema['maximum']}"))
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            issues.append(
                ValidationIssue(path, f"valor deve ser maior que {schema['exclusiveMinimum']}")
            )
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            issues.append(
                ValidationIssue(path, f"valor deve ser menor que {schema['exclusiveMaximum']}")
            )

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            issues.append(ValidationIssue(path, "lista menor que minItems"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            issues.append(ValidationIssue(path, "lista maior que maxItems"))
        if schema.get("uniqueItems"):
            serialized = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
                for item in instance
            ]
            if len(serialized) != len(set(serialized)):
                issues.append(ValidationIssue(path, "lista contém itens duplicados"))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                issues.extend(
                    validate(item, item_schema, f"{path}[{index}]", root_schema=root)
                )
        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict):
            matching_items = sum(
                not validate(item, contains_schema, f"{path}[{index}]", root_schema=root)
                for index, item in enumerate(instance)
            )
            minimum_contains = schema.get("minContains", 1)
            maximum_contains = schema.get("maxContains")
            if matching_items < minimum_contains:
                issues.append(
                    ValidationIssue(
                        path,
                        f"lista contém {matching_items} itens compatíveis; mínimo {minimum_contains}",
                    )
                )
            if maximum_contains is not None and matching_items > maximum_contains:
                issues.append(
                    ValidationIssue(
                        path,
                        f"lista contém {matching_items} itens compatíveis; máximo {maximum_contains}",
                    )
                )

    if isinstance(instance, dict):
        if len(instance) < schema.get("minProperties", 0):
            issues.append(ValidationIssue(path, "objeto menor que minProperties"))
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            issues.append(ValidationIssue(path, "objeto maior que maxProperties"))
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                issues.append(ValidationIssue(path, f"campo obrigatório ausente: {key}"))
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                issues.extend(
                    validate(value, properties[key], child_path, root_schema=root)
                )
            elif schema.get("additionalProperties") is False:
                issues.append(ValidationIssue(child_path, "campo adicional não permitido"))
            elif isinstance(schema.get("additionalProperties"), dict):
                issues.extend(
                    validate(
                        value,
                        schema["additionalProperties"],
                        child_path,
                        root_schema=root,
                    )
                )
        for dependency, dependent_keys in schema.get("dependentRequired", {}).items():
            if dependency in instance:
                for dependent_key in dependent_keys:
                    if dependent_key not in instance:
                        issues.append(
                            ValidationIssue(
                                path,
                                f"{dependent_key} é obrigatório quando {dependency} existe",
                            )
                        )

    for subschema in schema.get("allOf", []):
        issues.extend(validate(instance, subschema, path, root_schema=root))
    if variants := schema.get("oneOf"):
        valid_count = sum(
            not validate(instance, variant, path, root_schema=root)
            for variant in variants
        )
        if valid_count != 1:
            issues.append(ValidationIssue(path, "deve corresponder a exatamente um item de oneOf"))
    if variants := schema.get("anyOf"):
        if not any(
            not validate(instance, variant, path, root_schema=root)
            for variant in variants
        ):
            issues.append(ValidationIssue(path, "deve corresponder a ao menos um item de anyOf"))
    if subschema := schema.get("not"):
        if not validate(instance, subschema, path, root_schema=root):
            issues.append(ValidationIssue(path, "corresponde a um schema proibido por not"))
    if condition := schema.get("if"):
        condition_matches = not validate(instance, condition, path, root_schema=root)
        branch = schema.get("then") if condition_matches else schema.get("else")
        if isinstance(branch, dict):
            issues.extend(validate(instance, branch, path, root_schema=root))
    return issues
