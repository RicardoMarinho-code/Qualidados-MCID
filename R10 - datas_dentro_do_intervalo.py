import pandas as pd


def regra_10(df):
    """
    Regra 10:
    As datas

    - mcmv_ogu_26_dt_termino
    - mcmv_ogu_16_dt_contratacao
    - mcmv_ogu_02_dt_geracao
    - mcmv_ogu_01_dt_referencia

    devem estar entre 01/01/2009 e
    mcmv_ogu_01_dt_referencia.

    Datas não preenchidas são consideradas Sucesso.
    Datas inválidas ou fora do intervalo resultam em Insucesso.
    """

    resultado = df.copy()

    data_minima = pd.Timestamp("2009-01-01")

    data_referencia = pd.to_datetime(
        resultado["mcmv_ogu_01_dt_referencia"],
        errors="coerce",
        dayfirst=True
    )

    colunas_data = [
        "mcmv_ogu_26_dt_termino",
        "mcmv_ogu_16_dt_contratacao",
        "mcmv_ogu_02_dt_geracao",
        "mcmv_ogu_01_dt_referencia"
    ]

    for coluna in colunas_data:

        data = pd.to_datetime(
            resultado[coluna],
            errors="coerce",
            dayfirst=True
        )

        condicao = (
            data.isna() |
            (
                data_referencia.notna() &
                (data >= data_minima) &
                (data <= data_referencia)
            )
        )

        resultado[f"Resultado_Teste_Regra_10_{coluna}"] = condicao.map({
            True: "Sucesso",
            False: "Insucesso"
        })

    return resultado