import pandas as pd


def regra_8(df):
    """
    Regra 8:
    mcmv_ogu_33_vlr_desembolsado_no_ano_dt_referencia
    deve ser menor ou igual a
    mcmv_ogu_21_val_desembolsado.

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
                  .str.strip()
                  .replace(["", "nan", "NaN", "None"], "0")
        )

        return pd.to_numeric(
            coluna.str.replace(".", "", regex=False)
                  .str.replace(",", ".", regex=False),
            errors="coerce"
        ).fillna(0)

    desembolsado_ano = converter(
        resultado["mcmv_ogu_33_vlr_desembolsado_no_ano_dt_referencia"]
    )

    desembolsado_total = converter(
        resultado["mcmv_ogu_21_val_desembolsado"]
    )

    condicao = (
        desembolsado_ano.round(2)
        <= desembolsado_total.round(2)
    )

    resultado["Resultado_Teste_Regra_8"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado