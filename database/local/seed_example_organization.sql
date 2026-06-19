INSERT INTO organizations (id, name, status, metadata)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    'Organizacao Local Exemplo',
    'active',
    '{}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (
    id,
    organization_id,
    email,
    name,
    role,
    status,
    external_auth_id,
    metadata
)
VALUES (
    '22222222-2222-4222-8222-222222222222',
    '11111111-1111-4111-8111-111111111111',
    'dev.local@example.test',
    'Usuario Local Exemplo',
    'admin',
    'active',
    'local-dev-user',
    '{}'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    organization_id = EXCLUDED.organization_id,
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    status = EXCLUDED.status,
    external_auth_id = EXCLUDED.external_auth_id,
    metadata = EXCLUDED.metadata;
