import streamlit as st
import pandas as pd
import io
import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Consultor Financiero IA", layout="wide")
st.title("📊 Sistema Integral de Valor y Salud Financiera")

# 2. CARGA DE ARCHIVOS
st.sidebar.header("📁 Carga de Datos")
archivo = st.sidebar.file_uploader("Suba su archivo Excel (.xlsx)", type=["xlsx"])
ke_usuario = st.sidebar.slider("Costo de Oportunidad (Ke) %", 5.0, 25.0, 14.0) / 100

if archivo:
    try:
        # Leer archivo y buscar pestañas
        xls = pd.ExcelFile(archivo)
        p_bal = [s for s in xls.sheet_names if 'balan' in s.lower() or 'situac' in s.lower()][0]
        p_res = [s for s in xls.sheet_names if 'result' in s.lower() or 'perd' in s.lower() or 'pérd' in s.lower()][0]
        
        df_balance = pd.read_excel(archivo, sheet_name=p_bal)
        df_resultados = pd.read_excel(archivo, sheet_name=p_res)
        
        # Limpieza de nombres de cuenta y normalización
        df_balance['Cuenta'] = df_balance['Cuenta'].astype(str).str.strip()
        df_resultados['Cuenta'] = df_resultados['Cuenta'].astype(str).str.strip()
        df_balance = df_balance.set_index('Cuenta')
        df_resultados = df_resultados.set_index('Cuenta')

        # EXTRACCIÓN DE VALORES (Usando .item() para asegurar que sean números y no Series)
        try:
            # Balance
            at = float(df_balance.loc['Total Activos', 'Valor'])
            ac = float(df_balance.loc['Activo Corriente', 'Valor'])
            pc = float(df_balance.loc['Pasivo Corriente', 'Valor'])
            pt = float(df_balance.loc['Total Pasivos', 'Valor'])
            pat = float(df_balance.loc['Patrimonio Neto', 'Valor'])
            inv = float(df_balance.loc['Inventarios', 'Valor'])
            cxc = float(df_balance.loc['Cuentas por Cobrar', 'Valor'])
            df_fin = float(df_balance.loc['Deuda Financiera (Corto y Largo Plazo)', 'Valor'])
            pc_sc = float(df_balance.loc['Pasivo Corriente (Sin Costo Financiero)', 'Valor'])

            # Resultados
            uaii = float(df_resultados.loc['Utilidad Operativa (UAII)', 'Valor'])
            ventas = float(df_resultados.loc['Ingresos Totales', 'Valor'])
            int_pag = float(df_resultados.loc['Gastos Financieros (Intereses)', 'Valor'])
            imp = float(df_resultados.loc['Impuestos de Renta', 'Valor'])
            uai = float(df_resultados.loc['Utilidad Antes de Impuestos', 'Valor'])
        except KeyError as e:
            st.error(f"❌ No se encontró la cuenta: {e}. Verifique que el nombre en el Excel sea idéntico.")
            st.stop()

        # 3. CÁLCULOS CORE
        tax_rate = imp / uai if uai > 0 else 0.33
        kd = int_pag / df_fin if df_fin > 0 else 0
        v_estrucc = df_fin + pat
        wacc = ((df_fin/v_estrucc)*kd*(1-tax_rate)) + ((pat/v_estrucc)*ke_usuario) if v_estrucc > 0 else 0
        
        uodi = uaii * (1 - tax_rate)
        capital_inv = at - pc_sc
        eva = uodi - (capital_inv * wacc)
        roic = uodi / capital_inv if capital_inv > 0 else 0

        # Ratios
        liq_corr = ac / pc if pc > 0 else 0
        prueba_acida = (ac - inv) / pc if pc > 0 else 0
        end_tot = (pt / at) * 100 if at > 0 else 0
        rot_act = ventas / at if at > 0 else 0

        # 4. INTERFAZ DE USUARIO
        tab1, tab2, tab3 = st.tabs(["🎯 Diagnóstico EVA", "📊 Ratios Financieros", "📋 Informe e IA"])

        with tab1:
            st.subheader("Generación de Valor Económico")
            c1, c2, c3 = st.columns(3)
            # Formateamos manualmente a string para evitar el error de Series.format
            c1.metric("EVA", f"${eva:,.2f}", delta="Creación" if eva > 0 else "Destrucción")
            c2.metric("WACC (Costo)", f"{wacc*100:.2f}%")
            c3.metric("ROIC (Retorno)", f"{roic*100:.2f}%")
            
            st.write("---")
            st.subheader("UODI vs Cargo de Capital")
            st.bar_chart(pd.DataFrame({'Monto': [uodi, capital_inv * wacc]}, index=['Utilidad Real (UODI)', 'Costo de Capital']))

        with tab2:
            st.subheader("Indicadores de Salud")
            r1, r2, r3 = st.columns(3)
            r1.metric("Razón Corriente", f"{liq_corr:.2f}x")
            r2.metric("Endeudamiento", f"{end_tot:.1f}%")
            r3.metric("Prueba Ácida", f"{prueba_acida:.2f}x")
            
            st.write("---")
            st.subheader("Eficiencia")
            st.metric("Rotación de Activos", f"{rot_act:.2f} veces al año")

        with tab3:
            st.subheader("🤖 Recomendaciones del Consultor IA")
            
            # Lógica de recomendaciones
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### Diagnósticos")
                if eva > 0: st.success("✅ La operación genera riqueza excedente.")
                else: st.error("❌ La operación no cubre su costo de oportunidad.")
                
                if liq_corr < 1.2: st.warning("⚠️ Riesgo de liquidez a corto plazo.")
                if end_tot > 65: st.warning("🚩 Nivel de deuda riesgoso.")

            with col_b:
                st.markdown("### Acciones Sugeridas")
                if eva < 0: st.write("- **Optimizar márgenes:** Reducir costos operativos para elevar el ROIC.")
                if liq_corr < 1.2: st.write("- **Gestión de Caja:** Evaluar líneas de crédito revolventes o factoring.")
                if end_tot > 65: st.write("- **Desapalancamiento:** No adquirir nueva deuda; reinvertir utilidades.")
                if rot_act < 1: st.write("- **Uso de Activos:** Identificar activos improductivos y liquidarlos.")

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
else:
    st.info("👋 Por favor, cargue un archivo Excel para iniciar el análisis.")
