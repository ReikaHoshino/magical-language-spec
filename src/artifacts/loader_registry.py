"""Artifact-kind loaders selected from in-document identity, never filenames."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class ArtifactRegistryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


ArtifactLoader = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ArtifactLoaderRegistration:
    artifact_kind: str
    artifact_version: str
    loader: ArtifactLoader


class ArtifactLoaderRegistry:
    def __init__(self) -> None:
        self._loaders: dict[tuple[str, str], ArtifactLoaderRegistration] = {}

    def register(self, registration: ArtifactLoaderRegistration) -> None:
        key = (registration.artifact_kind, registration.artifact_version)
        if key in self._loaders:
            raise ArtifactRegistryError("DuplicateArtifactLoader", f"Duplicate artifact loader {key!r}.")
        self._loaders[key] = registration

    def load(self, document: dict[str, Any]) -> dict[str, Any]:
        kind = document.get("artifact_kind")
        version = document.get("artifact_version")
        registration = self._loaders.get((kind, version))
        if registration is None:
            known_kind = any(key[0] == kind for key in self._loaders)
            code = "UnknownArtifactVersion" if known_kind else "UnknownArtifactKind"
            raise ArtifactRegistryError(code, f"No loader for artifact {kind!r}@{version!r}.")
        return registration.loader(document)
