import streamlit as st
import pandas as pd
import io

# 1. Configuración de página
st.set_page_config(page_title="Analizador Financiero", layout="wide")
st.title("📊 Consultor Financiero IA: EVA y Ratios")

# 2. Carga de archivos en la barra lateral
st.sidebar.header("Configuración")
archivo = st.sidebar.file_uploader("Cargar Excel", type=["xlsx"])
ke_usuario = st.sidebar.slider("Costo Patrimonio (Ke) %", 5.0, 25.0, 14.0) / 100

if archivo:
    try:
        # Leer todas las pestañas
        xls = pd.ExcelFile(archivo)
        
        # Identificar pestañas (Busca por palabras clave)
        p_bal = [s for s in xls.sheet_names if 'balan' in s.lower() or 'situac' in s.lower()][0]
        p_res = [s for s in xls.sheet_names if 'result' in s.lower() or 'pérdid' in s.lower()][0]
        
        # Cargar DataFrames
        df_balance = pd.read_excel(archivo, sheet_name=p_bal)
        df_resultados = pd.read_excel(archivo_archivo, sheet_name=p_res) if 'archivo_archivo' not in locals() else pd.read_excel(archivo, sheet_name=p_res)
        
        # Limpieza de datos inmediata
        df_balance['Cuenta'] = df_balance['Cuenta'].str.strip()
        df_resultados['Cuenta'] = df_resultados['Cuenta'].str.strip()
        df_balance = df_balance.set_index('Cuenta')
        df_resultados = df_resultados.set_index('Cuenta')

        # --- EXTRACCIÓN DE VALORES ---
        # Balance
        at = df_balance.loc['Total Activos', 'Valor']
        ac = df_balance.loc['Activo Corriente', 'Valor']
        pc = df_balance.loc['Pasivo Corriente', 'Valor']
        pt = df_balance.loc['Total Pasivos', 'Valor']
        pat = df_balance.loc['Patrimonio Neto', 'Valor']
        inv = df_balance.loc['Inventarios', 'Valor']
        cxc = df_balance.loc['Cuentas por Cobrar', 'Valor']
        df_fin = df_balance.loc['Deuda Financiera (Corto y Largo Plazo)', 'Valor']
        pc_sc = df_balance.loc['Pasivo Corriente (Sin Costo Financiero)', 'Valor']

        # Resultados
        uaii = df_resultados.loc['Utilidad Operativa (UAII)', 'Valor']
        ventas = df_resultados.loc['Ingresos Totales', 'Valor']
        int_pagados = df_resultados.loc['Gastos Financieros (Intereses)', 'Valor']
        imp = df_resultados.loc['Impuestos de Renta', 'Valor']
        uai = df_resultados.loc['Utilidad Antes de Impuestos', 'Valor']

        # --- CÁLCULOS FINANCIEROS ---
        tax_rate = imp / uai if uai > 0 else 0.33
        kd = int_pagados / df_fin if df_fin > 0 else 0
        v_total = df_fin + pat
        wacc = ((df_fin/v_total)*kd*(1-tax_rate)) + ((pat/v_total)*ke_usuario)
        
        uodi = uaii * (1 - tax_rate)
        capital_inv = at - pc_sc
        eva = uodi - (capital_inv * wacc)
        roic = uodi / capital_inv if capital_inv > 0 else 0

        # Ratios
        liq_corr = ac / pc
        end_tot = (pt / at) * 100
        rot_act = ventas / at

        # --- INTERFAZ DE USUARIO ---
        t1, t2, t3 = st.tabs(["🎯 EVA", "🔮 Escenarios", "📋 Informe e IA"])

        with t1:
            c1, c2, c3 = st.columns(3)
            c1.metric("EVA", f"${eva:,.2f}", delta="Generando Valor" if eva > 0 else "Destruyendo Valor")
            c2.metric("WACC", f"{wacc*100:.2f}%")
            c3.metric("ROIC", f"{roic*100:.2f}%")
            st.bar_chart(pd.DataFrame({'Monto': [uodi, capital_inv * wacc]}, index=['Utilidad (UODI)', 'Costo Capital']))

        with t3:
            st.subheader("Análisis de Salud y Recomendaciones")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Liquidez:** {liq_corr:.2f}")
                st.write(f"**Endeudamiento:** {end_tot:.1f}%")
            with col_b:
                st.info("💡 **Recomendación IA:**")
                if eva < 0: st.write("- Su costo de capital supera la rentabilidad. Revise márgenes operativos.")
                if liq_corr < 1.2: st.write("- Alerta de liquidez: Considere factoring para sus cuentas por cobrar.")
                if end_tot > 65: st.write("- Endeudamiento alto. Priorice desapalancamiento antes de nuevas inversiones.")

    except Exception as e:
        st.error(f"Error de lectura: Asegúrese de que los nombres de las cuentas en el Excel coinciden. Detalle: {e}")
else:
    st.info("👋 Bienvenido. Cargue un archivo Excel para iniciar el diagnóstico.")
