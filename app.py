import streamlit as st
import pandas as pd
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Consultor Financiero IA", layout="wide")
st.title("📊 Consultor Financiero Integrado: EVA, Ratios y Diagnóstico")

# 2. CARGA DE DATOS (BARRA LATERAL)
st.sidebar.header("📁 Ingesta de Información")
archivo = st.sidebar.file_uploader("Suba su archivo Excel (.xlsx)", type=["xlsx"])
ke_usuario = st.sidebar.slider("Costo de Oportunidad (Ke) %", 5.0, 25.0, 14.0, step=0.5) / 100

# FUNCIÓN DE EXTRACCIÓN SEGURA (Evita errores de Series/Float)
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
        # Identificación inteligente de pestañas
        p_bal = [s for s in xls.sheet_names if 'balan' in s.lower() or 'situac' in s.lower()][0]
        p_res = [s for s in xls.sheet_names if 'result' in s.lower() or 'perd' in s.lower() or 'pérd' in s.lower()][0]
        
        df_balance = pd.read_excel(archivo, sheet_name=p_bal)
        df_resultados = pd.read_excel(archivo, sheet_name=p_res)
        
        # Limpieza de nombres
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

        # Verificación de datos mínimos
        if None in [at, ac, pc, pt, pat, uaii, ventas]:
            st.error("❌ Faltan cuentas críticas en el Excel. Revise los nombres de la columna 'Cuenta'.")
            st.stop()

        # --- CÁLCULOS CORE (EVA Y WACC) ---
        tax_rate = imp / uai if (uai and uai > 0) else 0.33
        kd = int_pag / df_fin if (df_fin and df_fin > 0) else 0
        v_est = (df_fin if df_fin else 0) + pat
        wacc = (((df_fin if df_fin else 0)/v_est)*kd*(1-tax_rate)) + ((pat/v_est)*ke_usuario) if v_est > 0 else 0
        uodi = uaii * (1 - tax_rate)
        cap_inv = at - (pc_sc if pc_sc else 0)
        eva = uodi - (cap_inv * wacc)
        roic = uodi / cap_inv if cap_inv > 0 else 0

        # --- CÁLCULOS ADICIONALES (RATIOS) ---
        razon_corriente = ac / pc if pc > 0 else 0
        prueba_acida = (ac - (inv if inv else 0)) / pc if pc > 0 else 0
        endeudamiento_total = (pt / at) * 100 if at > 0 else 0
        autonomia_financiera = pat / pt if (pt and pt > 0) else 0 
        rotacion_activos = ventas / at if at > 0 else 0
        dias_cobro = ((cxc if cxc else 0) * 360) / ventas if ventas > 0 else 0

        # --- INTERFAZ ---
        tab1, tab2, tab3 = st.tabs(["🎯 Diagnóstico EVA", "🔮 Escenarios", "📊 Ratios Financieros"])

        with tab1:
            st.subheader("Análisis de Generación de Valor")
            c1, c2, c3 = st.columns(3)
            c1.metric("EVA", f"${eva:,.2f}", delta="Creación" if eva > 0 else "Destrucción")
            c2.metric("WACC", f"{wacc*100:.2f}%")
            c3.metric("ROIC", f"{roic*100:.2f}%")
            
            st.markdown("### 🧠 Diagnóstico IA")
            if eva > 0 and razon_corriente < 1.0:
                st.warning("⚠️ **Alerta de Seguridad:** La empresa crea valor, pero tiene riesgo de iliquidez.")
            elif eva < 0:
                st.error(f"❌ **Alerta de Valor:** Se destruye valor económico.")
            else:
                st.success("✅ **Situación Ideal:** La empresa genera valor y es solvente.")

        with tab2:
            st.subheader("Simulación de Escenarios")
            esc_data = {
                "Escenario": ["Optimista (+10% UODI)", "Base", "Pesimista (+2% WACC)"],
                "EVA Estimado": [
                    (uodi * 1.1) - (cap_inv * wacc),
                    eva,
                    uodi - (cap_inv * (wacc + 0.02))
                ]
            }
            st.table(pd.DataFrame(esc_data).style.format({"EVA Estimado": "${:,.2f}"}))

        with tab3:
            st.subheader("Análisis de Ratios Financieros")
            col_liq, col_sol, col_act = st.columns(3)
            
            with col_liq:
                st.markdown("#### Liquidez")
                st.metric("Razón Corriente", f"{razon_corriente:.2f}")
                st.metric("Prueba Ácida", f"{prueba_acida:.2f}")

            with col_sol:
                st.markdown("#### Solvencia")
                st.metric("Endeudamiento", f"{endeudamiento_total:.1f}%")
                st.metric("Autonomía", f"{autonomia_financiera:.2f}")

            with col_act:
                st.markdown("#### Actividad")
                st.metric("Rotación Activos", f"{rotacion_activos:.2f}x")
                st.metric("Días de Cobro", f"{int(dias_cobro)} días")

            st.write("---")
            st.subheader("Estructura de Capital")
            st.bar_chart(pd.DataFrame({'Monto': [pt, pat]}, index=['Pasivos', 'Patrimonio']))

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
else:
    st.info("👋 Por favor, cargue un archivo Excel para iniciar el análisis.")
