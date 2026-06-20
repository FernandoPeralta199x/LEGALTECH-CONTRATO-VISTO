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

-- Senha: NovaSenha123!
-- Gerado via PBKDF2-SHA256 com 100k iteracoes (mesmo algoritmo do AuthService local).
INSERT INTO users (
    id,
    organization_id,
    email,
    name,
    role,
    status,
    password_hash,
    email_verified_at,
    external_auth_id,
    metadata
)
VALUES (
    'df227d35-44bc-4636-b94c-85562c317969',
    '11111111-1111-4111-8111-111111111111',
    'fernando.augusto.peralta@gmail.com',
    'Fernando Augusto',
    'admin',
    'active',
    'pbkdf2_sha256$03afb9d25ffe87305563d3a5f0329de1$8e1f908b15688ae9d66674e2e7f8a32610f5c3030fd329bcf8f9793de2d793a2',
    NOW(),
    'local-dev-user',
    '{"source": "local_dev_seed"}'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    organization_id = EXCLUDED.organization_id,
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    status = EXCLUDED.status,
    password_hash = EXCLUDED.password_hash,
    email_verified_at = EXCLUDED.email_verified_at,
    external_auth_id = EXCLUDED.external_auth_id,
    metadata = EXCLUDED.metadata;
