/**
 * Catálogo de produtos, módulos e matriz produto × módulo.
 *
 * Mapeamento canônico do wizard de criação de caso. As chaves de Produto
 * (`dados_partes` | `consulta_objeto` | `analise_contratual` | `reuniao_equipe`)
 * coincidem com o `ProductType` já usado em `services/cases.ts` e
 * `types/index.ts`. No MVP local, os módulos compõem uma simulação frontend-first.
 * A visão futura inclui IA, OCR, conectores externos, storage cloud e processamento
 * assíncrono, sem acionar integrações reais nesta versão.
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
  | "revisao_humana";

export type ProdutoMeta = {
  titulo: string;
  descricao: string;
  inclui: string[];
  precoBaseCents: number;
  slaHoras: number;
};

export type ModuloMeta = {
  titulo: string;
  descricao: string;
  precoCents: number;
};

export const PRODUTOS: Record<Produto, ProdutoMeta> = {
  dados_partes: {
    titulo: "Dados das partes",
    descricao: "Simulação local dos dados das partes para preparar futuras consultas.",
    inclui: ["Critério cadastral simulado", "Histórico jurídico futuro", "Reputação pública futura"],
    precoBaseCents: 18700,
    slaHoras: 24
  },
  consulta_objeto: {
    titulo: "Consulta do objeto",
    descricao: "Composição local do objeto contratual e critérios de análise futura.",
    inclui: ["Critério simulado do objeto", "Pesquisa pública futura", "Resumo por IA planejada"],
    precoBaseCents: 14900,
    slaHoras: 24
  },
  analise_contratual: {
    titulo: "Análise contratual",
    descricao: "Simulação local de critérios para leitura contratual e riscos.",
    inclui: ["IA planejada", "Critérios de risco simulados", "Mapeamento simulado de obrigações"],
    precoBaseCents: 28900,
    slaHoras: 48
  },
  reuniao_equipe: {
    titulo: "Reunião com advogado",
    descricao: "Preparação local para uma futura etapa com profissional jurídico.",
    inclui: ["Critérios prévios", "Reunião planejada", "Roteiro para parecer futuro"],
    precoBaseCents: 49000,
    slaHoras: 72
  }
};

export const MODULOS: Record<Modulo, ModuloMeta> = {
  escavador: {
    titulo: "Escavador",
    descricao:
      "Conector planejado para processos judiciais, histórico jurídico e dados públicos.",
    precoCents: 4900
  },
  targetdata: {
    titulo: "TargetData",
    descricao: "Conector planejado para dados cadastrais, comerciais e enriquecimento.",
    precoCents: 3900
  },
  ia_deepseek: {
    titulo: "IA planejada",
    descricao: "Módulo planejado para organizar dados, resumir informações e apoiar riscos.",
    precoCents: 2900
  },
  serasa_procon: {
    titulo: "Serasa / Procon",
    descricao:
      "Conector planejado para indicadores futuros de score, restrições, reputação e reclamações.",
    precoCents: 5900
  },
  analise_contratual_ia: {
    titulo: "Análise contratual assistida planejada",
    descricao: "Módulo planejado para apoiar leitura, riscos e obrigações contratuais.",
    precoCents: 7900
  },
  revisao_humana: {
    titulo: "Revisão humana planejada",
    descricao: "Etapa preparada para futura avaliação da equipe ou advogado responsável.",
    precoCents: 12900
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
    revisao_humana: { default: false }
  },
  consulta_objeto: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, obrigatorio: true, bloqueado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: false },
    revisao_humana: { default: false }
  },
  analise_contratual: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, obrigatorio: true, bloqueado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: true, obrigatorio: true, bloqueado: true },
    revisao_humana: { default: true, recomendado: true }
  },
  reuniao_equipe: {
    escavador: { default: false },
    targetdata: { default: false },
    ia_deepseek: { default: true, recomendado: true },
    serasa_procon: { default: false },
    analise_contratual_ia: { default: false, recomendado: true },
    revisao_humana: { default: true, obrigatorio: true, bloqueado: true }
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

export function estimarValor(produto: Produto, modulosAtivos: Modulo[]): number {
  const base = PRODUTOS[produto].precoBaseCents;
  const adicionais = modulosAtivos.reduce(
    (sum, m) => sum + (MODULOS[m]?.precoCents ?? 0),
    0
  );
  return base + adicionais;
}

export function estimarPrazoHoras(produto: Produto, modulosAtivos: Modulo[]): number {
  const base = PRODUTOS[produto].slaHoras;
  const ajusteRevisao = modulosAtivos.includes("revisao_humana") ? 24 : 0;
  const ajusteReuniao = produto === "reuniao_equipe" ? 24 : 0;
  return base + ajusteRevisao + ajusteReuniao;
}
