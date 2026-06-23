/**
 * Catálogo de produtos, módulos e matriz produto × módulo.
 *
 * Mapeamento canônico do wizard de criação de caso.  No modelo unificado,
 * produtos não têm preço fixo próprio: o preço base de cada produto é a
 * soma dos módulos obrigatórios (`obrigatorio: true`) na matriz.  A tabela
 * administrável de "Preços de Módulos" é a única fonte de valores.
 *
 * As chaves de Produto (`dados_partes` | `consulta_objeto` |
 * `analise_contratual` | `reuniao_equipe`) coincidem com o `ProductType` já
 * usado em `services/cases.ts` e `types/index.ts`.
 */

export type Produto =
  | "dados_partes"
  | "consulta_objeto"
  | "analise_contratual"
  | "reuniao_equipe";

export type Modulo =
  | "escavador"
  | "targetdata"
  | "ia_deepseek"
  | "serasa_procon"
  | "analise_contratual_ia"
  | "revisao_humana"
  | "reuniao_equipe";

export type ProdutoMeta = {
  code: string;
  titulo: string;
  descricao: string;
  inclui: string[];
  slaHoras: number;
};

export type ModuloMeta = {
  code: string;
  titulo: string;
  descricao: string;
  precoCents: number;
};

export const PRODUTOS: Record<Produto, ProdutoMeta> = {
  dados_partes: {
    code: "dados_partes",
    titulo: "Dados das partes",
    descricao: "Simulação local dos dados das partes para preparar futuras consultas.",
    inclui: ["Critério cadastral simulado", "Histórico jurídico futuro", "Reputação pública futura"],
    slaHoras: 24
  },
  consulta_objeto: {
    code: "consulta_objeto",
    titulo: "Consulta do objeto",
    descricao: "Composição local do objeto contratual e critérios de análise futura.",
    inclui: ["Critério simulado do objeto", "Pesquisa pública futura", "Resumo por IA planejada"],
    slaHoras: 24
  },
  analise_contratual: {
    code: "analise_contratual",
    titulo: "Análise contratual",
    descricao: "Simulação local de critérios para leitura contratual e riscos.",
    inclui: ["IA planejada", "Critérios de risco simulados", "Mapeamento simulado de obrigações"],
    slaHoras: 48
  },
  reuniao_equipe: {
    code: "reuniao_equipe",
    titulo: "Reunião com advogado",
    descricao: "Preparação local para uma futura etapa com profissional jurídico.",
    inclui: ["Critérios prévios", "Reunião planejada", "Roteiro para parecer futuro"],
    slaHoras: 72
  }
};

export const MODULOS: Record<Modulo, ModuloMeta> = {
  escavador: {
    code: "escavador",
    titulo: "Escavador",
    descricao: "Conector planejado para processos judiciais, histórico jurídico e dados públicos.",
    precoCents: 6000
  },
  targetdata: {
    code: "targetdata",
    titulo: "TargetData",
    descricao: "Conector planejado para dados cadastrais, comerciais e enriquecimento.",
    precoCents: 3900
  },
  ia_deepseek: {
    code: "ia_deepseek",
    titulo: "IA planejada",
    descricao: "Módulo planejado para organizar dados, resumir informações e apoiar riscos.",
    precoCents: 2900
  },
  serasa_procon: {
    code: "serasa_procon",
    titulo: "Serasa / Procon",
    descricao: "Conector planejado para indicadores futuros de score, restrições, reputação e reclamações.",
    precoCents: 5900
  },
  analise_contratual_ia: {
    code: "analise_contratual_ia",
    titulo: "Análise contratual assistida planejada",
    descricao: "Módulo planejado para apoiar leitura, riscos e obrigações contratuais.",
    precoCents: 7900
  },
  revisao_humana: {
    code: "revisao_humana",
    titulo: "Revisão humana planejada",
    descricao: "Etapa preparada para futura avaliação da equipe ou advogado responsável.",
    precoCents: 12900
  },
  reuniao_equipe: {
    code: "reuniao_equipe",
    titulo: "Reunião com advogado",
    descricao: "Preparação local para uma futura etapa com profissional jurídico.",
    precoCents: 49000
  }
};

export type ModuloConfig = {
  /** Estado inicial do switch ao entrar na etapa. */
  default: boolean;
  /** Mostra o badge "Recomendado". */
  recomendado?: boolean;
  /** Mostra o badge "Obrigatório" — sempre ativo e bloqueado. */
  obrigatorio?: boolean;
  /** Impede o usuário de alterar o switch (par com obrigatório, ou para módulos indisponíveis). */
  bloqueado?: boolean;
};

export const MATRIZ: Record<Produto, Record<Modulo, ModuloConfig>> = {
  dados_partes: {
    escavador: { default: true, obrigatorio: true, bloqueado: true },
    targetdata: { default: true, obrigatorio: true, bloqueado: true },
    ia_deepseek: { default: true, obrigatorio: true, bloqueado: true },
    serasa_procon: { default: false, recomendado: true },
    analise_contratual_ia: { default: false },
    revisao_humana: { default: false },
    reuniao_equipe: { default: false }
  },
  consulta_objeto: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, obrigatorio: true, bloqueado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: false },
    revisao_humana: { default: false },
    reuniao_equipe: { default: false }
  },
  analise_contratual: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, obrigatorio: true, bloqueado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: true, obrigatorio: true, bloqueado: true },
    revisao_humana: { default: true, recomendado: true },
    reuniao_equipe: { default: false }
  },
  reuniao_equipe: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, recomendado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: false, recomendado: true },
    revisao_humana: { default: false, obrigatorio: true },
    reuniao_equipe: { default: false, obrigatorio: true }
  }
};

export type Papel =
  | "contratante"
  | "contratada"
  | "comprador"
  | "vendedor"
  | "locador"
  | "locatario"
  | "avalista"
  | "fiador"
  | "testemunha"
  | "outro";

export const PAPEIS: { id: Papel; label: string }[] = [
  { id: "contratante", label: "Contratante" },
  { id: "contratada", label: "Contratada" },
  { id: "comprador", label: "Comprador" },
  { id: "vendedor", label: "Vendedor" },
  { id: "locador", label: "Locador" },
  { id: "locatario", label: "Locatário" },
  { id: "avalista", label: "Avalista" },
  { id: "fiador", label: "Fiador" },
  { id: "testemunha", label: "Testemunha" },
  { id: "outro", label: "Outro" }
];

export type TipoPessoa = "pf" | "pj";

/** Soma dos preços dos módulos obrigatórios de um produto. */
export function computeProductBasePrice(produto: Produto): number {
  const matriz = MATRIZ[produto];
  return Object.entries(matriz).reduce((total, [modulo, config]) => {
    if (config.obrigatorio) {
      return total + MODULOS[modulo as Modulo].precoCents;
    }
    return total;
  }, 0);
}

export function estimarPrazoHoras(produto: Produto, modulosAtivos: Modulo[]): number {
  const base = PRODUTOS[produto].slaHoras;
  const ajusteRevisao = modulosAtivos.includes("revisao_humana") ? 24 : 0;
  const ajusteReuniao = produto === "reuniao_equipe" ? 24 : 0;
  return base + ajusteRevisao + ajusteReuniao;
}
