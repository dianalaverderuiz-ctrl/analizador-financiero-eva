import streamlit as st
import pandas as pd
import io
import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Consultor Financiero IA", layout="wide")
st.title("📊 Consultor Financiero Integrado: EVA, Ratios y Agente IA")

# 2. CARGA DE DATOS (BARRA LATERAL)
st.sidebar.header("📁 Ingesta de Información")
archivo = st.sidebar.file_uploader("Suba su archivo Excel (.xlsx)", type=["xlsx"])
ke_usuario = st.sidebar.slider("Costo de Oportunidad (Ke) %", 5.0, 25.0, 14.0, step=0.5) / 100

# FUNCIÓN DE EXTRACCIÓN SEGURA
def get_val(df, cuenta):
    try:
        val = df.loc[cuenta, 'Valor']
        if isinstance(val, pd.Series):
            return float(val.iloc[0])
        return float(val)
    except KeyError:
        return None

if archivo:
    try:
        xls = pd.ExcelFile(archivo)
        p_bal = [s for s in xls.sheet_names if 'balan' in s.lower() or 'situac' in s.lower()][0]
        p_res = [s for s in xls.sheet_names if 'result' in s.lower() or 'perd' in s.lower() or 'pérd' in s.lower()][0]
        
        df_balance = pd.read_excel(archivo, sheet_name=p_bal)
        df_resultados = pd.read_excel(archivo, sheet_name=p_res)
        
        df_balance['Cuenta'] = df_balance['Cuenta'].astype(str).str.strip()
        df_resultados['Cuenta'] = df_resultados['Cuenta'].astype(str).str.strip()
        df_b = df_balance.set_index('Cuenta')
        df_r = df_resultados.set_index('Cuenta')

        # --- EXTRACCIÓN DE VARIABLES ---
        at = get_val(df_b, 'Total Activos')
        ac = get_val(df_b, 'Activo Corriente')
        pc = get_val(df_b, 'Pasivo Corriente')
        pt = get_val(df_b, 'Total Pasivos')
        pat = get_val(df_b, 'Patrimonio Neto')
        inv = get_val(df_b, 'Inventarios')
        cxc = get_val(df_b, 'Cuentas por Cobrar')
        df_fin = get_val(df_b, 'Deuda Financiera (Corto y Largo Plazo)')
        pc_sc = get_val(df_b, 'Pasivo Corriente (Sin Costo Financiero)')

        uaii = get_val(df_r, 'Utilidad Operativa (UAII)')
        ventas = get_val(df_r, 'Ingresos Totales')
        int_pag = get_val(df_r, 'Gastos Financieros (Intereses)')
        imp = get_val(df_r, 'Impuestos de Renta')
        uai = get_val(df_r, 'Utilidad Antes de Impuestos')

        if None in [at, ac, pc, pt, pat, uaii, ventas]:
            st.error("❌ Faltan cuentas críticas. Verifique su Excel.")
            st.stop()

        # --- CÁLCULOS ---
        tax_rate = imp / uai if (uai and uai > 0) else 0.33
        kd = int_pag / df_fin if (df_fin and df_fin > 0) else 0
        v_est = (df_fin if df_fin else 0) + pat
        wacc = (((df_fin if df_fin else 0)/v_est)*kd*(1-tax_rate)) + ((pat/v_est)*ke_usuario) if v_est > 0 else 0
        uodi = uaii * (1 - tax_rate)
        cap_inv = at - (pc_sc if pc_sc else 0)
        eva = uodi - (cap_inv * wacc)
        roic = uodi / cap_inv if cap_inv > 0 else 0
        
        razon_corriente = ac / pc if pc > 0 else 0
        endeudamiento_total = (pt / at) * 100 if at > 0 else 0
        rotacion_activos = ventas / at if at > 0 else 0
        dias_cobro = ((cxc if cxc else 0) * 360) / ventas if ventas > 0 else 0

        # --- INTERFAZ ---
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 EVA", "🔮 Escenarios", "📊 Ratios", "🤖 Agente de Consultoría"])

        with tab1:
            st.subheader("Generación de Valor")
            c1, c2, c3 = st.columns(3)
            c1.metric("EVA", f"${eva:,.2f}", delta="Creación" if eva > 0 else "Destrucción")
            c2.metric("WACC", f"{wacc*100:.2f}%")
            c3.metric("ROIC", f"{roic*100:.2f}%")
            st.bar_chart(pd.DataFrame({'Monto': [uodi, cap_inv * wacc]}, index=['Utilidad (UODI)', 'Costo Capital']))

        with tab2:
            st.subheader("Simulación")
            esc_data = {"Escenario": ["Optimista", "Base", "Pesimista"],
                        "EVA": [(uodi * 1.1) - (cap_inv * wacc), eva, uodi - (cap_inv * (wacc + 0.02))]}
            st.table(pd.DataFrame(esc_data).style.format({"EVA": "${:,.2f}"}))

        with tab3:
            st.subheader("Ratios de Salud")
            r1, r2, r3 = st.columns(3)
            r1.metric("Liquidez Corriente", f"{razon_corriente:.2f}")
            r2.metric("Endeudamiento", f"{endeudamiento_total:.1f}%")
            r3.metric("Rotación Activos", f"{rotacion_activos:.2f}x")

        with tab4:
            st.header("🤖 Informe Estratégico del Agente IA")
            st.info(f"Fecha de análisis: {datetime.date.today()}")
            
            col_diag, col_plan = st.columns(2)
            
            with col_diag:
                st.subheader("🔍 Diagnóstico de Situación")
                if eva > 0:
                    st.success("✅ **FORTALEZA:** La empresa supera su costo de oportunidad. Hay excedente para reinversión o dividendos.")
                else:
                    st.error("❌ **DEBILIDAD:** Destrucción de valor. El retorno operativo no compensa el riesgo del capital invertido.")
                
                if razon_corriente < 1.2:
                    st.warning("⚠️ **ALERTA DE CAJA:** La liquidez es frágil. Podría haber dificultades para cubrir pasivos inmediatos.")
                
                if endeudamiento_total > 60:
                    st.warning("🚩 **ALERTA DE SOLVENCIA:** La estructura de capital depende excesivamente de terceros.")

            with col_plan:
                st.subheader("🚀 Plan de Acción Sugerido")
                acciones = []
                if eva < 0:
                    acciones.append("1. **Reingeniería de Costos:** El ROIC está bajo; identifique procesos que consumen recursos sin generar margen.")
                if razon_corriente < 1.2:
                    acciones.append("2. **Optimización de COI:** Acelere el recaudo de cartera (actualmente en " + f"{int(dias_cobro)}" + " días).")
                if endeudamiento_total > 60:
                    acciones.append("3. **Capitalización:** Evalúe la retención de utilidades o aporte de socios para bajar la presión financiera.")
                
                if not acciones:
                    st.write("Excelente desempeño. Priorice la expansión de mercado.")
                else:
                    for acc in acciones:
                        st.write(acc)

            st.write("---")
            st.markdown("### 📈 Resumen Cognitivo")
            st.write(f"El sistema detecta que por cada dólar invertido, la operación rinde {roic*100:.2f}%, mientras que financiar ese dólar cuesta {wacc*100:.2f}%.")

    except Exception as e:
        st.error(f"Error inesperado: {e}")
