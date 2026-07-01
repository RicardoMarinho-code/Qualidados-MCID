import pandas as pd


def regra_2(df):
    """
    Regra 2:
    Se mcmv_ogu_35_txt_situacao_obra_agrupada = "distratado" ou "distratada",
    então mcmv_ogu_24_qtd_distratadas deve ser maior que 0.

    Valores nulos, vazios ou inválidos são tratados como 0.
    """

    resultado = df.copy()

    resultado["Regra_Testada"] = "Regra 2"

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

    situacao = (
        resultado["mcmv_ogu_35_txt_situacao_obra_agrupada"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    qtd_distratadas = converter(
        resultado["mcmv_ogu_24_qtd_distratadas"]
    )

    condicao = (
        (~situacao.isin(["distratado", "distratada"])) |
        (qtd_distratadas > 0)
    )

    resultado["Resultado_Teste"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado