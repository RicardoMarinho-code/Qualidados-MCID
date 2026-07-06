import pandas as pd


def regra_11(df):
    """
    Regra 11:
    mcmv_ogu_23_qtd_entregues deve ser menor ou igual a
    mcmv_ogu_22_qtd_uh.

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

    qtd_entregues = converter(
        resultado["mcmv_ogu_23_qtd_entregues"]
    )

    qtd_uh = converter(
        resultado["mcmv_ogu_22_qtd_uh"]
    )

    condicao = (
        qtd_entregues <= qtd_uh
    )

    resultado["Resultado_Teste_Regra_11"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado