from typing import Final


CLIENTS_READ: Final = "clients:read"
CLIENTS_WRITE: Final = "clients:write"
CASES_READ: Final = "cases:read"
CASES_WRITE: Final = "cases:write"
CASES_SUBMIT: Final = "cases:submit"
CASE_PARTIES_READ: Final = "case_parties:read"
CASE_PARTIES_WRITE: Final = "case_parties:write"
CASE_PARTIES_DELETE: Final = "case_parties:delete"
DOCUMENTS_READ: Final = "documents:read"
DOCUMENTS_WRITE: Final = "documents:write"
DOCUMENTS_UPLOAD: Final = "documents:upload"
DOCUMENTS_DOWNLOAD: Final = "documents:download"
DOCUMENTS_PROCESS: Final = "documents:process"
DOCUMENTS_DELETE: Final = "documents:delete"
DOCUMENT_CHUNKS_READ: Final = "document_chunks:read"
USERS_READ: Final = "users:read"
USERS_WRITE: Final = "users:write"
USERS_INVITE: Final = "users:invite"
USERS_DEACTIVATE: Final = "users:deactivate"
ORGANIZATIONS_READ: Final = "organizations:read"
ORGANIZATIONS_WRITE: Final = "organizations:write"
ROLES_PERMISSIONS_READ: Final = "roles_permissions:read"
ROLES_PERMISSIONS_WRITE: Final = "roles_permissions:write"
AUDIT_READ: Final = "audit:read"
AGENTS_READ: Final = "agents:read"
AGENTS_START: Final = "agents:start"
AGENTS_RETRY: Final = "agents:retry"
REPORTS_READ: Final = "reports:read"
REPORTS_WRITE: Final = "reports:write"
REPORTS_APPROVE: Final = "reports:approve"
REPORTS_DOWNLOAD: Final = "reports:download"
HUMAN_REVIEWS_READ: Final = "human_reviews:read"
HUMAN_REVIEWS_APPROVE: Final = "human_reviews:approve"
HUMAN_REVIEWS_REJECT: Final = "human_reviews:reject"
HUMAN_REVIEWS_REQUEST_ADJUSTMENT: Final = "human_reviews:request_adjustment"
EXTERNAL_QUERIES_READ: Final = "external_queries:read"
EXTERNAL_QUERIES_WRITE: Final = "external_queries:write"

ALL_BASE_PERMISSIONS: Final[frozenset[str]] = frozenset(
    {
        CLIENTS_READ,
        CLIENTS_WRITE,
        CASES_READ,
        CASES_WRITE,
        CASES_SUBMIT,
        CASE_PARTIES_READ,
        CASE_PARTIES_WRITE,
        CASE_PARTIES_DELETE,
        DOCUMENTS_READ,
        DOCUMENTS_WRITE,
        DOCUMENTS_UPLOAD,
        DOCUMENTS_DOWNLOAD,
        DOCUMENTS_PROCESS,
        DOCUMENTS_DELETE,
        DOCUMENT_CHUNKS_READ,
        USERS_READ,
        USERS_WRITE,
        USERS_INVITE,
        USERS_DEACTIVATE,
        ORGANIZATIONS_READ,
        ORGANIZATIONS_WRITE,
        ROLES_PERMISSIONS_READ,
        ROLES_PERMISSIONS_WRITE,
        AUDIT_READ,
        AGENTS_READ,
        AGENTS_START,
        AGENTS_RETRY,
        REPORTS_READ,
        REPORTS_WRITE,
        REPORTS_APPROVE,
        REPORTS_DOWNLOAD,
        HUMAN_REVIEWS_READ,
        HUMAN_REVIEWS_APPROVE,
        HUMAN_REVIEWS_REJECT,
        HUMAN_REVIEWS_REQUEST_ADJUSTMENT,
        EXTERNAL_QUERIES_READ,
        EXTERNAL_QUERIES_WRITE,
    }
)

BASE_ROLE_PERMISSIONS: Final[dict[str, frozenset[str]]] = {
    "owner": ALL_BASE_PERMISSIONS,
    "admin": frozenset(
        {
            CLIENTS_READ,
            CLIENTS_WRITE,
            CASES_READ,
            CASES_WRITE,
            CASES_SUBMIT,
            CASE_PARTIES_READ,
            CASE_PARTIES_WRITE,
            CASE_PARTIES_DELETE,
            DOCUMENTS_READ,
            DOCUMENTS_WRITE,
            DOCUMENTS_UPLOAD,
            DOCUMENTS_DOWNLOAD,
            DOCUMENTS_PROCESS,
            DOCUMENTS_DELETE,
            DOCUMENT_CHUNKS_READ,
            USERS_READ,
            USERS_WRITE,
            USERS_INVITE,
            USERS_DEACTIVATE,
            ORGANIZATIONS_READ,
            ROLES_PERMISSIONS_READ,
            AUDIT_READ,
            AGENTS_READ,
            AGENTS_START,
            AGENTS_RETRY,
            REPORTS_READ,
            REPORTS_WRITE,
            REPORTS_APPROVE,
            REPORTS_DOWNLOAD,
            HUMAN_REVIEWS_READ,
            HUMAN_REVIEWS_APPROVE,
            HUMAN_REVIEWS_REJECT,
            HUMAN_REVIEWS_REQUEST_ADJUSTMENT,
            EXTERNAL_QUERIES_READ,
            EXTERNAL_QUERIES_WRITE,
        }
    ),
    "analyst": frozenset(
        {
            CLIENTS_READ,
            CASES_READ,
            CASES_WRITE,
            CASES_SUBMIT,
            CASE_PARTIES_READ,
            CASE_PARTIES_WRITE,
            DOCUMENTS_READ,
            DOCUMENTS_WRITE,
            DOCUMENTS_UPLOAD,
            DOCUMENTS_DOWNLOAD,
            DOCUMENTS_PROCESS,
            DOCUMENT_CHUNKS_READ,
            AGENTS_READ,
            AGENTS_START,
            AGENTS_RETRY,
            REPORTS_READ,
            REPORTS_WRITE,
            HUMAN_REVIEWS_READ,
            HUMAN_REVIEWS_APPROVE,
            HUMAN_REVIEWS_REJECT,
            HUMAN_REVIEWS_REQUEST_ADJUSTMENT,
            EXTERNAL_QUERIES_READ,
            EXTERNAL_QUERIES_WRITE,
        }
    ),
    "client": frozenset(
        {
            CLIENTS_READ,
            CASES_READ,
            CASES_WRITE,
            CASES_SUBMIT,
            CASE_PARTIES_READ,
            CASE_PARTIES_WRITE,
            DOCUMENTS_READ,
            DOCUMENTS_WRITE,
            DOCUMENTS_UPLOAD,
            DOCUMENTS_DOWNLOAD,
            DOCUMENTS_DELETE,
            REPORTS_READ,
            REPORTS_DOWNLOAD,
        }
    ),
    "support": frozenset(
        {
            CLIENTS_READ,
            CASES_READ,
            CASE_PARTIES_READ,
            DOCUMENTS_READ,
            DOCUMENTS_DOWNLOAD,
            USERS_READ,
            REPORTS_READ,
        }
    ),
}

BASE_ROLES: Final[tuple[str, ...]] = tuple(BASE_ROLE_PERMISSIONS.keys())
