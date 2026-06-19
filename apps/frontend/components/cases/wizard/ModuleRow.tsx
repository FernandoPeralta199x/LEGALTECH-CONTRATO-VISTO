"use client";

import { Badge } from "@/components/Badge";
import { Switch } from "@/components/Switch";
import { MODULOS, type Modulo, type ModuloConfig } from "@/lib/produtoConfig";

type ModuleRowProps = {
  modulo: Modulo;
  config: ModuloConfig;
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
};

export function ModuleRow({
  modulo,
  config,
  checked,
  onCheckedChange
}: ModuleRowProps) {
  const meta = MODULOS[modulo];

  return (
    <div className="cv-form-card flex items-start justify-between gap-4 px-5 py-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-[var(--text)]">{meta.titulo}</h3>
          {config.obrigatorio && <Badge tone="orange">Fixo no roteiro</Badge>}
          {config.recomendado && !config.obrigatorio && (
            <Badge tone="teal">Sugerido na simulação</Badge>
          )}
        </div>
        <p className="mt-1 text-xs leading-5 text-[var(--text2)]">{meta.descricao}</p>
        <p className="mt-1.5 text-[11px] text-[var(--text3)]">
          Referência simulada: R$ {(meta.precoCents / 100).toFixed(2).replace(".", ",")}
        </p>
      </div>

      <Switch
        checked={checked}
        disabled={config.bloqueado}
        label={`Incluir na simulação: ${meta.titulo}`}
        onCheckedChange={onCheckedChange}
      />
    </div>
  );
}
