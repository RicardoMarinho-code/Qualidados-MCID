import pandas as pd


def regra_4(df):
    """
    Regra 4:
    Se mcmv_ogu_26_dt_termino estiver preenchida,
    ela deve ser menor ou igual a
    mcmv_ogu_01_dt_referencia.

    Caso mcmv_ogu_26_dt_termino não esteja preenchida,
    considera-se Sucesso.
    """

    resultado = df.copy()

    dt_termino = pd.to_datetime(
        resultado["mcmv_ogu_26_dt_termino"],
        errors="coerce",
        dayfirst=True
    )

    dt_referencia = pd.to_datetime(
        resultado["mcmv_ogu_01_dt_referencia"],
        errors="coerce",
        dayfirst=True
    )

    condicao = (
        dt_termino.isna() |
        (
            dt_referencia.notna() &
            (dt_termino <= dt_referencia)
        )
    )

    resultado["Resultado_Teste_Regra_4"] = condicao.map({
        True: "Sucesso",
        False: "Insucesso"
    })

    return resultado