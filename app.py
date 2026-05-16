import streamlit as st
import pandas as pd
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consultor Financiero IA", layout="wide")
st.title("📊 Analizador Financiero Inteligente")

# 2. CARGA
st.sidebar.header("📁 Configuración")
archivo = st.sidebar.file_uploader("Cargar Excel (.xlsx)", type=["xlsx"])
ke_usuario = st.sidebar.slider("Costo Ke %", 5.0, 25.0, 14.0) / 100

if archivo:
    try:
        xls = pd.ExcelFile(archivo)
        p_bal = [s for s in xls.sheet_names if 'balan' in s.lower() or 'situac' in s.lower()][0]
        p_res = [s for s in xls.sheet_names if 'result' in s.lower() or 'perd' in s.lower() or 'pérd' in s.lower()][0]
        
        df_balance = pd.read_excel(archivo, sheet_name=p_bal)
        df_resultados = pd.read_excel(archivo, sheet_name=p_res)
        
        # Limpieza radical de datos
        df_balance.columns = df_balance.columns.str.strip()
        df_resultados.columns = df_resultados.columns.str.strip()
        df_balance['Cuenta'] = df_balance['Cuenta'].astype(str).str.strip()
        df_resultados['Cuenta'] = df_resultados['Cuenta'].astype(str).str.strip()
        
        # Filtrar solo las columnas necesarias y eliminar duplicados de cuenta
        df_b = df_balance[['Cuenta', 'Valor']].drop_duplicates('Cuenta').set_index('Cuenta')
        df_r = df_resultados[['Cuenta', 'Valor']].drop_duplicates('Cuenta').set_index('Cuenta')

        # FUNCIÓN DE EXTRACCIÓN SEGURA (Aquí está la clave)
        def get_val(df, cuenta):
            try:
                # .item() transforma una celda de Pandas directamente en un número de Python
                return float(df.loc[cuenta, 'Valor'])
            except:
                # Si falla, intentamos convertir a serie y tomar el primer elemento
                val = df.loc[cuenta, 'Valor']
                if isinstance(val, pd.Series):
                    return float(val.iloc[0])
                return float(val)

        # EXTRACCIÓN
        try:
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
        except KeyError as e:
            st.error(f"❌ Error: No se encuentra la cuenta **{e}** en tu Excel.")
            st.stop()

        # 3. CÁLCULOS
        tax_rate = imp / uai if uai > 0 else 0.33
        kd = int_pag / df_fin if df_fin > 0 else 0
        v_est = df_fin + pat
        wacc = ((df_fin/v_est)*kd*(1-tax_rate)) + ((pat/v_est)*ke_usuario) if v_est > 0 else 0
        uodi = uaii * (1 - tax_rate)
        cap_inv = at - pc_sc
        eva = uodi - (cap_inv * wacc)
        roic = uodi / cap_inv if cap_inv > 0 else 0
        
        liq_corr = ac / pc if pc > 0 else 0
        end_tot = (pt / at) * 100 if at > 0 else 0
        
        # --- CÁLCULOS ADICIONALES (RATIOS) ---
            
        # 1. Ratios de Liquidez
        razon_corriente = total_activos_corrientes / pasivo_corriente  # Necesitas definir estas variables del Excel
        prueba_acida = (total_activos_corrientes - inventarios) / pasivo_corriente
            
        # 2. Ratios de Solvencia y Endeudamiento
        endeudamiento_total = (total_pasivos / total_activos) * 100
        autonomia_financiera = (patrimonio / total_pasivos)
            
        # 3. Ratios de Actividad (Eficiencia)
        # Nota: Ventas viene del Estado de Resultados
        rotacion_activos = ventas / total_activos
        dias_cobro = (cuentas_por_cobrar * 360) / ventas
        
        # 4. INTERFAZ
        t1, t2 = st.tabs(["🎯 Resultados", "📋 Informe"])
        with t1:
            c1, c2, c3 = st.columns(3)
            c1.metric("EVA", f"${eva:,.2f}")
            c2.metric("WACC", f"{wacc*100:.2f}%")
            c3.metric("ROIC", f"{roic*100:.2f}%")
            st.bar_chart(pd.DataFrame({'Valor': [uodi, cap_inv*wacc]}, index=['Utilidad', 'Costo Cap']))

        with t2:
            st.subheader("Informe de Consultoría")
            st.write(f"**Liquidez:** {liq_corr:.2f} | **Endeudamiento:** {end_tot:.1f}%")
            if eva < 0: st.error("Destrucción de valor detectada. Revise costos financieros.")
            else: st.success("La empresa genera valor económico real.")

    except Exception as e:
        st.error(f"Error inesperado: {e}")
else:
    st.info("Suba un archivo para analizar.")
