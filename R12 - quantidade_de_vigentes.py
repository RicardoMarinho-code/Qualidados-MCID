import pandas as pd


def regra_12(df):
    """
    Regra 12:
    mcmv_ogu_25_qtd_vigentes deve ser igual a
    mcmv_ogu_22_qtd_uh - mcmv_ogu_23_qtd_entregues -
    mcmv_ogu_24_qtd_distratadas.

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

    qtd_uh = converter(
        resultado["mcmv_ogu_22_qtd_uh"]
    )

    qtd_entregues = converter(
        resultado["mcmv_ogu_23_qtd_entregues"]
    )

    qtd_distratadas = converter(
        resultado["mcmv_ogu_24_qtd_distratadas"]
    )

    qtd_vigentes = converter(
        resultado["mcmv_ogu_25_qtd_vigentes"]
    )

    condicao = (
        qtd_vigentes ==
        (qtd_uh - qtd_entregues - qtd_distratadas)
    )

    resultado["Resultado_Teste_Regra_12"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado