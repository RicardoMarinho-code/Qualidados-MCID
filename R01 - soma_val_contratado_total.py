import pandas as pd


def regra_1(df):
    """
    Regra 1:
    A soma de mcmv_ogu_18_val_contratado_original +
    mcmv_ogu_19_val_aporte_adicional deve ser igual a
    mcmv_ogu_20_val_contratado_total.

    Valores nulos, vazios ou inválidos são tratados como 0.
    """

    resultado = df.copy()

    def converter(coluna):
        # Se já for numérica, apenas trata valores nulos
        if pd.api.types.is_numeric_dtype(coluna):
            return coluna.fillna(0).astype(float)

        # Se for texto, faz a limpeza antes da conversão
        coluna = (
            coluna.astype(str)
                  .str.strip()                         # Remove espaços
                  .replace(["", "nan", "NaN", "None"], "0")  # Trata valores vazios
        )

        return pd.to_numeric(
            coluna.str.replace(".", "", regex=False)   # Remove separador de milhar
                  .str.replace(",", ".", regex=False), # Troca decimal
            errors="coerce"
        ).fillna(0)

    valor_original = converter(
        resultado["mcmv_ogu_18_val_contratado_original"]
    )

    aporte_adicional = converter(
        resultado["mcmv_ogu_19_val_aporte_adicional"]
    )

    valor_total = converter(
        resultado["mcmv_ogu_20_val_contratado_total"]
    )

    # Comparação considerando duas casas decimais
    condicao = (
        (valor_original + aporte_adicional).round(2)
        == valor_total.round(2)
    )

    resultado["Resultado_Teste_Regra_1"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado