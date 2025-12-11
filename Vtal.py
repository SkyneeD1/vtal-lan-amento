import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lançamentos", page_icon="🧠", layout="centered")

st.title("🧠 Lançamentos")
st.subheader("📋 Cole sua tabela:")

texto = st.text_area("Cole aqui:", height=300)

if st.button("🚀 Processar"):
    if texto.strip() == "":
        st.warning("⚠️ Cole os dados no campo acima.")
    else:
        linhas = texto.strip().splitlines()

        # 🔥 Junta linhas quebradas
        linhas_corrigidas = []
        linha_acumulada = ""

        for linha in linhas:
            linha_check = linha.strip()
            if any(x in linha_check.upper() for x in ["CÁLCULO LIQUIDADO", "VERSÃO", "PÁG", "DESCRIÇÃO DO BRUTO"]):
                continue  # Ignorar cabeçalhos e rodapés

            numeros = re.findall(r'[\d\.,]+', linha_check)
            if len(numeros) >= 3:  # agora há pelo menos Valor Corrigido, Juros e Total
                if linha_acumulada:
                    linha_completa = linha_acumulada + " " + linha_check
                    linhas_corrigidas.append(linha_completa.strip())
                    linha_acumulada = ""
                else:
                    linhas_corrigidas.append(linha_check.strip())
            else:
                linha_acumulada += " " + linha_check

        if linha_acumulada:
            linhas_corrigidas.append(linha_acumulada.strip())

        # 🏗️ Processamento das linhas corrigidas
        dados = []
        for linha in linhas_corrigidas:
            numeros = re.findall(r'[\d\.,]+', linha)

            if len(numeros) >= 3:
                valor_corrigido = numeros[-3]
                juros = numeros[-2]

                try:
                    valor_corrigido = float(valor_corrigido.replace('.', '').replace(',', '.'))
                    juros = float(juros.replace('.', '').replace(',', '.'))
                except:
                    valor_corrigido, juros = 0.0, 0.0

                descricao = linha
                for num in numeros[-3:]:
                    descricao = descricao.rsplit(num, 1)[0]
                descricao = descricao.strip().upper()

                dados.append([descricao, valor_corrigido, juros])

        df = pd.DataFrame(dados, columns=['Descricao', 'Valor Corrigido', 'Juros'])

        # 🔥 Agrupamento por verba consolidada
        def agrupar_verba(descricao):
            desc = descricao.upper()

            # FGTS puro
            if "FGTS" in desc and "MULTA" not in desc:
                return "FGTS"

            # Multa de 40% sobre FGTS (várias formas de escrever)
            if ("MULTA SOBRE FGTS" in desc) or ("MULTA DE 40%" in desc and "FGTS" in desc):
                return "MULTA FGTS"

            prefixos_reflexos = ["13º", "FÉRIAS", "AVISO", "REPOUSO"]

            if any(desc.startswith(prefixo) for prefixo in prefixos_reflexos):
                if "SOBRE" in desc:
                    partes = desc.split("SOBRE", 1)
                    verba = partes[1].strip()
                    return verba
                else:
                    return desc
            else:
                return desc

        df['Verba Consolidada'] = df['Descricao'].apply(agrupar_verba)

        resultado = df.groupby('Verba Consolidada')[['Valor Corrigido', 'Juros']].sum().reset_index()

        # ➕ Linha específica somando FGTS + Multa 40%
        fgts_multa_mask = resultado['Verba Consolidada'].isin(['FGTS', 'MULTA FGTS'])
        if fgts_multa_mask.any():
            subtotal_fgts_multa = resultado.loc[fgts_multa_mask, ['Valor Corrigido', 'Juros']].sum()

            # remove as linhas individuais FGTS e MULTA FGTS
            resultado = resultado[~fgts_multa_mask]

            # adiciona apenas a linha consolidada
            linha_fgts_multa = pd.DataFrame([[
                "FGTS + MULTA 40%",
                subtotal_fgts_multa['Valor Corrigido'],
                subtotal_fgts_multa['Juros']
            ]], columns=['Verba Consolidada', 'Valor Corrigido', 'Juros'])

            resultado = pd.concat([resultado, linha_fgts_multa], ignore_index=True)

        st.success("✅ Processamento concluído!")

        st.subheader("📊 Resultado Consolidado (sem coluna Total):")

        # ➕ Adiciona linha de total geral
        linha_total = pd.DataFrame([[
            "TOTAL GERAL",
            resultado['Valor Corrigido'].sum(),
            resultado['Juros'].sum()
        ]], columns=['Verba Consolidada', 'Valor Corrigido', 'Juros'])

        resultado_com_total = pd.concat([resultado, linha_total], ignore_index=True)

        # 🔧 Formatação brasileira
        resultado_exibicao = resultado_com_total.copy()
        for col in ['Valor Corrigido', 'Juros']:
            resultado_exibicao[col] = resultado_exibicao[col].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        st.dataframe(resultado_exibicao)
