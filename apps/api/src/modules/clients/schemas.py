from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


ClientPersonType = Literal["individual", "company"]
ClientContractRole = Literal[
    "contractor",
    "contracted",
    "intervening",
    "guarantor",
    "witness",
    "other",
]
ClientDocumentType = Literal["cpf", "cnpj", "rg", "unknown"]
SourceMode = Literal["local", "mock", "simulated", "real", "hybrid"]


class ClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    person_type: ClientPersonType | None = None
    contract_role: ClientContractRole | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    trade_name: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    document_type: ClientDocumentType | None = None
    document_number: str | None = Field(default=None, max_length=32)
    document: str | None = Field(default=None, max_length=32)
    cpf: str | None = Field(default=None, max_length=32)
    cnpj: str | None = Field(default=None, max_length=32)
    rg: str | None = Field(default=None, max_length=32)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=500)
    source_mode: SourceMode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_person_specific_fields(self) -> "ClientCreate":
        has_legacy_name = bool(self.name and self.name.strip())
        if self.person_type is None:
            if not has_legacy_name:
                raise ValueError("Informe o nome do cliente.")
            return self

        if self.contract_role is None:
            raise ValueError("Selecione o papel no contrato.")

        if self.person_type == "individual":
            if not (self.full_name or self.name):
                raise ValueError("Informe o nome completo.")
            return self

        if not (self.legal_name or self.company_name or self.name):
            raise ValueError("Informe a razão social.")
        return self


class ClientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    person_type: ClientPersonType | None = None
    contract_role: ClientContractRole | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    trade_name: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    document_type: ClientDocumentType | None = None
    document_number: str | None = Field(default=None, max_length=32)
    document: str | None = Field(default=None, max_length=32)
    cpf: str | None = Field(default=None, max_length=32)
    cnpj: str | None = Field(default=None, max_length=32)
    rg: str | None = Field(default=None, max_length=32)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=500)
    source_mode: SourceMode | None = None
    metadata: dict[str, Any] | None = None


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID | None = None
    name: str
    document: str | None = None
    document_masked: str | None = None
    document_type: ClientDocumentType | None = None
    person_type: ClientPersonType | None = None
    contract_role: ClientContractRole | None = None
    full_name: str | None = None
    legal_name: str | None = None
    company_name: str | None = None
    trade_name: str | None = None
    display_name: str | None = None
    document_number: str | None = None
    cpf: str | None = None
    cnpj: str | None = None
    rg: str | None = None
    birth_date: date | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    source_mode: SourceMode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class ClientListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
