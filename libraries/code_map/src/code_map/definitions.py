from typing import Literal

from pydantic import BaseModel, Field


ImportCrossingType = Literal["module", "symbol"]
SourceVisibility = Literal["public", "protected", "private"]
SourceSignatureKind = Literal["call", "construct", "index"]


class SourceImport(BaseModel):
    path: str
    is_relative: bool
    normalized_path: str
    imported_name: str
    is_aliased: bool
    crossing_type: ImportCrossingType
    file_barrier_crossed: bool
    statement_id: int
    join_key: str
    uses_joined_import: bool


class SourceFunction(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declared_args: int
    optional_args: int


class SourceClassMethod(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declared_args: int
    optional_args: int


class SourceClassProperty(BaseModel):
    name: str
    is_optional: bool


class SourceSignature(BaseModel):
    kind: SourceSignatureKind
    line_count: int
    declared_args: int
    optional_args: int


class SourceClass(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
    line_count: int


class SourceInterface(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
    line_count: int


class SourceType(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    properties: list[SourceClassProperty]
    signatures: list[SourceSignature]
    line_count: int


class SourceAbstractClass(BaseModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    abstract_methods: list[SourceClassMethod]
    concrete_methods: list[SourceClassMethod]
    properties: list[SourceClassProperty]
    line_count: int


class SourceFile(BaseModel):
    imports: list[SourceImport]
    classes: list[SourceClass]
    interfaces: list[SourceInterface] = Field(default_factory=list)
    types: list[SourceType] = Field(default_factory=list)
    abstract_classes: list[SourceAbstractClass] = Field(default_factory=list)
    functions: list[SourceFunction]
    line_count: int
    code_line_count: int
    public_symbol_count: int
