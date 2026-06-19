import type {
  AgentExecution,
  AuditLog,
  Case,
  CaseParty,
  Client,
  Document,
  Organization,
  Report,
  Review,
  TimelineEvent,
  User
} from "@/types";

// ─── Organizations ─────────────────────────────────────────────────────────────

export const mockOrganizations: Organization[] = [
  {
    id: "org-001",
    name: "Escritório Jurídico Alpha",
    cnpj: "00.000.000/0001-00",
    plan: "professional",
    casesLimit: 50,
    casesUsed: 5,
    createdAt: "2026-01-10T09:00:00.000Z",
    status: "active"
  },
  {
    id: "org-002",
    name: "Consultoria Beta Jurídica",
    cnpj: "00.000.000/0002-00",
    plan: "starter",
    casesLimit: 10,
    casesUsed: 2,
    createdAt: "2026-03-15T12:00:00.000Z",
    status: "active"
  }
];

// ─── Users ─────────────────────────────────────────────────────────────────────

export const mockUsers: User[] = [
  {
    id: "user-001",
    name: "Dr. Fernando Augusto",
    email: "fernando@escritoriojuridico.test",
    role: "admin",
    organizationId: "org-001",
    organizationName: "Escritório Jurídico Alpha",
    avatarInitials: "FA",
    createdAt: "2026-01-10T09:00:00.000Z",
    lastLoginAt: "2026-05-24T08:30:00.000Z",
    status: "active"
  },
  {
    id: "user-002",
    name: "Dra. Mariana Costa",
    email: "mariana.analista@escritoriojuridico.test",
    role: "analyst",
    organizationId: "org-001",
    organizationName: "Escritório Jurídico Alpha",
    avatarInitials: "MC",
    createdAt: "2026-02-01T09:00:00.000Z",
    lastLoginAt: "2026-05-24T09:15:00.000Z",
    status: "active"
  },
  {
    id: "user-003",
    name: "Carlos Eduardo",
    email: "carlos.cliente@empresabeta.test",
    role: "client",
    organizationId: "org-002",
    organizationName: "Consultoria Beta Jurídica",
    avatarInitials: "CE",
    createdAt: "2026-03-20T14:00:00.000Z",
    lastLoginAt: "2026-05-23T16:40:00.000Z",
    status: "active"
  }
];

// ─── Clients ───────────────────────────────────────────────────────────────────

export const mockClients: Client[] = [
  {
    id: "client-001",
    name: "Construtora Alpha Ltda",
    documentLabel: "CNPJ protegido",
    email: "juridico@construtoraalpha.test",
    phone: "+55 11 98765-0000",
    status: "active",
    riskLevel: "low",
    casesCount: 3,
    organizationId: "org-001",
    createdAt: "2026-02-15T09:00:00.000Z"
  },
  {
    id: "client-002",
    name: "Tech Solutions Beta S.A.",
    documentLabel: "CNPJ protegido",
    email: "contratos@techbeta.test",
    phone: "+55 11 97654-0000",
    status: "review",
    riskLevel: "medium",
    casesCount: 2,
    organizationId: "org-001",
    createdAt: "2026-03-10T11:00:00.000Z"
  },
  {
    id: "client-003",
    name: "João Marcos Rodrigues",
    documentLabel: "CPF protegido",
    email: "joao.rodrigues@email.test",
    phone: "+55 21 96543-0000",
    status: "active",
    riskLevel: "high",
    casesCount: 1,
    organizationId: "org-002",
    createdAt: "2026-04-05T14:30:00.000Z"
  }
];

// ─── Case Parties ──────────────────────────────────────────────────────────────

export const mockParties: CaseParty[] = [
  {
    id: "party-001",
    caseId: "case-001",
    name: "Construtora Alpha Ltda",
    document: "CNPJ protegido",
    type: "contratante",
    email: "juridico@construtoraalpha.test",
    phone: "+55 11 98765-0000",
    notes: "Parte compradora no contrato de aquisição de terreno."
  },
  {
    id: "party-002",
    caseId: "case-001",
    name: "Incorporadora Mega Empreendimentos",
    document: "CNPJ protegido",
    type: "contratada",
    email: "vendas@megaempreendimentos.test",
    phone: "+55 11 94321-0000",
    notes: "Parte vendedora. Verificar situação cadastral."
  },
  {
    id: "party-003",
    caseId: "case-002",
    name: "Tech Solutions Beta S.A.",
    document: "CNPJ protegido",
    type: "contratante",
    email: "contratos@techbeta.test",
    phone: "+55 11 97654-0000",
    notes: "Contratante de serviços de consultoria tecnológica."
  }
];

// ─── Cases ─────────────────────────────────────────────────────────────────────

export const mockCases: Case[] = [
  {
    id: "case-001",
    code: "CASO-2026-001",
    clientId: "client-001",
    clientName: "Construtora Alpha Ltda",
    caseType: "compra_venda",
    product: "analise_contratual",
    status: "revisao_humana",
    priority: "high",
    documentsCount: 6,
    progressPercent: 87,
    assignedTo: "Dra. Mariana Costa",
    notes: "Análise prioritária — cláusulas de rescisão e índice de correção.",
    estimatedValue: 4500000,
    parties: mockParties.filter((p) => p.caseId === "case-001"),
    updatedAt: "2026-05-24T10:30:00.000Z",
    createdAt: "2026-05-10T09:00:00.000Z",
    submittedAt: "2026-05-10T09:45:00.000Z"
  },
  {
    id: "case-002",
    code: "CASO-2026-002",
    clientId: "client-002",
    clientName: "Tech Solutions Beta S.A.",
    caseType: "prestacao_servicos",
    product: "dados_partes",
    status: "analise_contratual",
    priority: "normal",
    documentsCount: 3,
    progressPercent: 62,
    assignedTo: "Dra. Mariana Costa",
    notes: "Due diligence do contrato de TI com cláusula de propriedade intelectual.",
    parties: mockParties.filter((p) => p.caseId === "case-002"),
    updatedAt: "2026-05-23T16:10:00.000Z",
    createdAt: "2026-05-15T14:00:00.000Z",
    submittedAt: "2026-05-15T15:00:00.000Z"
  },
  {
    id: "case-003",
    code: "CASO-2026-003",
    clientId: "client-003",
    clientName: "João Marcos Rodrigues",
    caseType: "compra_venda",
    product: "consulta_objeto",
    status: "processamento_documental",
    priority: "normal",
    documentsCount: 2,
    progressPercent: 40,
    assignedTo: null,
    notes: "Consulta de imóvel residencial — matrícula e certidões.",
    estimatedValue: 850000,
    parties: [],
    updatedAt: "2026-05-22T09:45:00.000Z",
    createdAt: "2026-05-20T11:00:00.000Z",
    submittedAt: "2026-05-20T11:30:00.000Z"
  },
  {
    id: "case-004",
    code: "CASO-2026-004",
    clientId: "client-002",
    clientName: "Tech Solutions Beta S.A.",
    caseType: "confidencialidade",
    product: "analise_contratual",
    status: "delivered",
    priority: "low",
    documentsCount: 4,
    progressPercent: 100,
    assignedTo: "Dra. Mariana Costa",
    notes: "NDA entre parceiros — análise concluída e relatório entregue.",
    parties: [],
    updatedAt: "2026-05-18T17:00:00.000Z",
    createdAt: "2026-05-05T10:00:00.000Z",
    submittedAt: "2026-05-05T10:30:00.000Z"
  },
  {
    id: "case-005",
    code: "CASO-2026-005",
    clientId: "client-001",
    clientName: "Construtora Alpha Ltda",
    caseType: "locacao",
    product: "analise_contratual",
    status: "draft",
    priority: "low",
    documentsCount: 0,
    progressPercent: 5,
    assignedTo: null,
    notes: "",
    parties: [],
    updatedAt: "2026-05-24T08:00:00.000Z",
    createdAt: "2026-05-24T08:00:00.000Z",
    submittedAt: null
  }
];

// ─── Documents ─────────────────────────────────────────────────────────────────

export const mockDocuments: Document[] = [
  {
    id: "doc-001",
    filename: "contrato-compra-venda-alpha.pdf",
    caseId: "case-001",
    caseCode: "CASO-2026-001",
    contentType: "application/pdf",
    status: "processed",
    sizeLabel: "2.3 MB",
    uploadedAt: "2026-05-10T10:00:00.000Z",
    processedAt: "2026-05-10T10:12:00.000Z",
    notes: "Contrato principal de compra e venda."
  },
  {
    id: "doc-002",
    filename: "matricula-imovel.pdf",
    caseId: "case-001",
    caseCode: "CASO-2026-001",
    contentType: "application/pdf",
    status: "processed",
    sizeLabel: "880 KB",
    uploadedAt: "2026-05-10T10:05:00.000Z",
    processedAt: "2026-05-10T10:18:00.000Z",
    notes: "Matrícula atualizada do cartório."
  },
  {
    id: "doc-003",
    filename: "certidao-negativa-construtora.pdf",
    caseId: "case-001",
    caseCode: "CASO-2026-001",
    contentType: "application/pdf",
    status: "validated",
    sizeLabel: "420 KB",
    uploadedAt: "2026-05-11T09:00:00.000Z",
    processedAt: "2026-05-11T09:08:00.000Z",
    notes: "CND Federal e FGTS."
  },
  {
    id: "doc-004",
    filename: "contrato-servicos-ti.docx",
    caseId: "case-002",
    caseCode: "CASO-2026-002",
    contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    status: "processing",
    sizeLabel: "1.1 MB",
    uploadedAt: "2026-05-15T15:20:00.000Z",
    processedAt: null,
    notes: "Contrato de prestação de serviços TI com SLAs."
  },
  {
    id: "doc-005",
    filename: "proposta-comercial.pdf",
    caseId: "case-003",
    caseCode: "CASO-2026-003",
    contentType: "application/pdf",
    status: "uploaded",
    sizeLabel: "650 KB",
    uploadedAt: "2026-05-20T12:00:00.000Z",
    processedAt: null,
    notes: ""
  }
];

// ─── Agent Executions ──────────────────────────────────────────────────────────

export const mockAgentExecutions: AgentExecution[] = [
  {
    id: "exec-001",
    caseId: "case-001",
    agentName: "Agente de Triagem",
    agentType: "triagem",
    status: "completed",
    startedAt: "2026-05-10T09:50:00.000Z",
    finishedAt: "2026-05-10T09:53:00.000Z",
    durationMs: 180000,
    outputSummary: "Triagem demonstrativa registrada. 6 documentos indicados para preparação local.",
    errorMessage: null
  },
  {
    id: "exec-002",
    caseId: "case-001",
    agentName: "Processador Documental",
    agentType: "doc_processor",
    status: "completed",
    startedAt: "2026-05-10T10:00:00.000Z",
    finishedAt: "2026-05-10T10:28:00.000Z",
    durationMs: 1680000,
    outputSummary: "5 documentos marcados no mock, com trechos demonstrativos preparados para visualização.",
    errorMessage: null
  },
  {
    id: "exec-003",
    caseId: "case-001",
    agentName: "Analisador Contratual",
    agentType: "contrato_analyzer",
    status: "completed",
    startedAt: "2026-05-10T10:30:00.000Z",
    finishedAt: "2026-05-10T11:05:00.000Z",
    durationMs: 2100000,
    outputSummary: "Roteiro de análise local preparado. 3 indicadores simulados e 5 recomendações demonstrativas.",
    errorMessage: null
  },
  {
    id: "exec-004",
    caseId: "case-001",
    agentName: "Agente de Compliance",
    agentType: "compliance",
    status: "completed",
    startedAt: "2026-05-10T11:10:00.000Z",
    finishedAt: "2026-05-10T11:25:00.000Z",
    durationMs: 900000,
    outputSummary: "Verificação demonstrativa de conformidade registrada. Sem pendências críticas no mock.",
    errorMessage: null
  },
  {
    id: "exec-005",
    caseId: "case-001",
    agentName: "Gerador de Relatório",
    agentType: "report_writer",
    status: "completed",
    startedAt: "2026-05-10T11:30:00.000Z",
    finishedAt: "2026-05-10T11:48:00.000Z",
    durationMs: 1080000,
    outputSummary: "Resumo demonstrativo preparado. Revisão humana planejada no roadmap.",
    errorMessage: null
  },
  {
    id: "exec-006",
    caseId: "case-002",
    agentName: "Agente de Triagem",
    agentType: "triagem",
    status: "completed",
    startedAt: "2026-05-15T15:30:00.000Z",
    finishedAt: "2026-05-15T15:33:00.000Z",
    durationMs: 180000,
    outputSummary: "Triagem demonstrativa registrada. 3 documentos indicados no roteiro local.",
    errorMessage: null
  },
  {
    id: "exec-007",
    caseId: "case-002",
    agentName: "Analisador Contratual",
    agentType: "contrato_analyzer",
    status: "running",
    startedAt: "2026-05-23T14:00:00.000Z",
    finishedAt: null,
    durationMs: null,
    outputSummary: null,
    errorMessage: null
  }
];

// ─── Reports ───────────────────────────────────────────────────────────────────

export const mockReports: Report[] = [
  {
    id: "report-001",
    caseId: "case-001",
    caseCode: "CASO-2026-001",
    status: "in_review",
    title: "Relatório de Análise Contratual — Compra e Venda",
    summary:
      "O contrato de compra e venda apresenta estrutura jurídica adequada, com três pontos de atenção identificados referentes a cláusulas de rescisão, correção monetária e prazo de registro. A due diligence documental não identificou restrições cadastrais impeditivas. Recomenda-se ajuste nas cláusulas 8.2 e 12.1 antes da assinatura.",
    risks: [
      {
        id: "risk-001",
        level: "high",
        title: "Cláusula de rescisão unilateral sem multa",
        description:
          "A cláusula 8.2 permite rescisão unilateral sem previsão de multa compensatória, expondo o comprador a risco financeiro expressivo."
      },
      {
        id: "risk-002",
        level: "medium",
        title: "Índice de correção monetária não especificado",
        description:
          "O contrato menciona 'índice de mercado' sem especificar o índice aplicável, podendo gerar divergências futuras."
      },
      {
        id: "risk-003",
        level: "low",
        title: "Prazo de registro em cartório omitido",
        description:
          "Não há previsão expressa do prazo para registro do imóvel em cartório após a assinatura."
      }
    ],
    recommendations: [
      "Revisar a cláusula 8.2 para incluir multa rescisória de 10% sobre o valor do contrato.",
      "Substituir 'índice de mercado' pelo INCC ou IGPM na cláusula 12.1.",
      "Incluir prazo de 30 dias para registro em cartório após a assinatura.",
      "Solicitar certidão de ônus reais atualizada do imóvel.",
      "Verificar pendências de IPTU nos últimos 5 anos."
    ],
    generatedAt: "2026-05-10T11:48:00.000Z",
    approvedAt: null,
    approvedBy: null,
    version: 1
  },
  {
    id: "report-002",
    caseId: "case-004",
    caseCode: "CASO-2026-004",
    status: "delivered",
    title: "Relatório de Análise — NDA Tech Solutions",
    summary:
      "O Acordo de Não Divulgação (NDA) apresenta estrutura adequada para proteger informações sensíveis entre as partes. Foram identificadas oportunidades de melhoria nas definições de informação confidencial e no prazo de vigência.",
    risks: [
      {
        id: "risk-004",
        level: "medium",
        title: "Definição ampla de informação confidencial",
        description:
          "A definição pode incluir informações já de domínio público, gerando conflitos de interpretação."
      }
    ],
    recommendations: [
      "Delimitar claramente o escopo das informações confidenciais.",
      "Incluir prazo de vigência pós-término do contrato (mínimo 24 meses).",
      "Prever jurisdição competente em caso de litígio."
    ],
    generatedAt: "2026-05-15T14:00:00.000Z",
    approvedAt: "2026-05-18T16:30:00.000Z",
    approvedBy: "Dra. Mariana Costa",
    version: 2
  },
  {
    id: "report-003",
    caseId: "case-002",
    caseCode: "CASO-2026-002",
    status: "draft",
    title: "Rascunho — Análise de Contrato de Prestação de Serviços TI",
    summary: "Análise demonstrativa em andamento. Preparação documental local pendente.",
    risks: [],
    recommendations: [],
    generatedAt: "2026-05-23T14:00:00.000Z",
    approvedAt: null,
    approvedBy: null,
    version: 1
  }
];

// ─── Reviews ───────────────────────────────────────────────────────────────────

export const mockReviews: Review[] = [
  {
    id: "review-001",
    caseId: "case-001",
    reportId: "report-001",
    status: "pending",
    assignedTo: "Dra. Mariana Costa",
    checklist: [
      { id: "ck-001", label: "Verificar identidade das partes", checked: true },
      { id: "ck-002", label: "Confirmar riscos identificados", checked: true },
      { id: "ck-003", label: "Validar recomendações jurídicas", checked: false },
      { id: "ck-004", label: "Revisar linguagem do relatório", checked: false },
      { id: "ck-005", label: "Confirmar ausência de dados sensíveis expostos", checked: true },
      { id: "ck-006", label: "Aprovar para entrega ao cliente", checked: false }
    ],
    observations: "",
    createdAt: "2026-05-10T12:00:00.000Z",
    reviewedAt: null
  }
];

// ─── Timeline ──────────────────────────────────────────────────────────────────

export const mockTimeline: TimelineEvent[] = [
  {
    id: "tl-001",
    caseId: "case-001",
    status: "draft",
    label: "Registro local de caso",
    description: "Caso demonstrativo iniciado pelo cliente via plataforma.",
    actor: "Carlos Eduardo (cliente)",
    createdAt: "2026-05-10T09:00:00.000Z"
  },
  {
    id: "tl-002",
    caseId: "case-001",
    status: "submitted",
    label: "Marcado para triagem local",
    description: "Cliente confirmou dados na simulação local para preparação do roteiro.",
    actor: "Carlos Eduardo (cliente)",
    createdAt: "2026-05-10T09:45:00.000Z"
  },
  {
    id: "tl-003",
    caseId: "case-001",
    status: "triagem_pendente",
    label: "Triagem iniciada",
    description: "Roteiro de triagem local indicado para classificar documentos demonstrativos.",
    actor: "Sistema",
    createdAt: "2026-05-10T09:50:00.000Z"
  },
  {
    id: "tl-004",
    caseId: "case-001",
    status: "processamento_documental",
    label: "Preparação documental local",
    description: "Trechos demonstrativos preparados para visualização local.",
    actor: "Agente Documental",
    createdAt: "2026-05-10T10:00:00.000Z"
  },
  {
    id: "tl-005",
    caseId: "case-001",
    status: "analise_contratual",
    label: "Triagem contratual local",
    description: "Roteiro de IA planejada indicado para cláusulas, riscos e conformidade.",
    actor: "Agente Contratual",
    createdAt: "2026-05-10T10:30:00.000Z"
  },
  {
    id: "tl-006",
    caseId: "case-001",
    status: "minuta_relatorio",
    label: "Resumo demonstrativo preparado",
    description: "Roteiro de relatório preparado na simulação local.",
    actor: "Agente Relator",
    createdAt: "2026-05-10T11:30:00.000Z"
  },
  {
    id: "tl-007",
    caseId: "case-001",
    status: "revisao_humana",
    label: "Revisão humana planejada",
    description: "Etapa futura indicada no roteiro demonstrativo.",
    actor: "Sistema",
    createdAt: "2026-05-10T12:00:00.000Z"
  }
];

// ─── Audit Logs ────────────────────────────────────────────────────────────────

export const mockAuditLogs: AuditLog[] = [
  {
    id: "audit-001",
    caseId: "case-001",
    userId: "user-003",
    userName: "Carlos Eduardo",
    action: "case_created",
    description: "Caso CASO-2026-001 criado.",
    metadata: { caseCode: "CASO-2026-001" },
    createdAt: "2026-05-10T09:00:00.000Z"
  },
  {
    id: "audit-002",
    caseId: "case-001",
    userId: "user-003",
    userName: "Carlos Eduardo",
    action: "document_uploaded",
    description: "Documento contrato-compra-venda-alpha.pdf enviado.",
    metadata: { documentId: "doc-001", filename: "contrato-compra-venda-alpha.pdf" },
    createdAt: "2026-05-10T10:00:00.000Z"
  },
  {
    id: "audit-003",
    caseId: "case-001",
    userId: "user-003",
    userName: "Carlos Eduardo",
    action: "case_submitted",
    description: "Caso marcado para triagem local.",
    metadata: { caseCode: "CASO-2026-001" },
    createdAt: "2026-05-10T09:45:00.000Z"
  },
  {
    id: "audit-004",
    caseId: "case-001",
    userId: "user-002",
    userName: "Dra. Mariana Costa",
    action: "status_changed",
    description: "Status alterado para Revisão Humana.",
    metadata: { from: "minuta_relatorio", to: "revisao_humana" },
    createdAt: "2026-05-10T12:00:00.000Z"
  },
  {
    id: "audit-005",
    caseId: null,
    userId: "user-001",
    userName: "Dr. Fernando Augusto",
    action: "user_login",
    description: "Login realizado no sistema.",
    metadata: { ip: "127.0.0.1" },
    createdAt: "2026-05-24T08:30:00.000Z"
  }
];
