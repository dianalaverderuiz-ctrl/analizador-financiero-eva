import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime

# Configuración inicial de la página web
st.set_page_config(page_title="EcoStock AI - Analizador Financiero", layout="wide")

st.title("📊 Sistema Cognitivo de Análisis Financiero y Valor Económico (EVA)")
st.markdown("Cargue los estados financieros de su empresa para proyectar escenarios y evaluar la creación de valor real.")

# --- BARRA LATERAL ---
st.sidebar.header("📁 Ingesta de Información")
archivo_cargado = st.sidebar.file_uploader("Suba el archivo de Excel (.xlsx)", type=["xlsx"])

st.sidebar.header("⚙️ Parámetros de Mercado")
ke_usuario = st.sidebar.slider("Costo de Oportunidad del Patrimonio (Ke)", min_value=5.0, max_value=25.0, value=14.0, step=0.5) / 100

# --- LÓGICA DE PROCESAMIENTO ---
if archivo_cargado is not None:
    try:
        archivo_excel = pd.ExcelFile(archivo_cargado)
        nombres_pestanas = archivo_excel.sheet_names
        
        pestana_balance = None
        pestana_resultados = None
        
        for nombre in nombres_pestanas:
            nombre_min = nombre.lower().strip()
            if 'balance' in nombre_min or 'situacion' in nombre_min or 'situación' in nombre_min:
                pestana_balance = nombre
            elif 'resultado' in nombre_min or 'perdidas' in nombre_min or 'pérdidas' in nombre_min:
                pestana_resultados = nombre

        if not pestana_balance or not pestana_resultados:
            st.error(f"No se identificaron las pestañas. Pestañas detectadas: {nombres_pestanas}")
        else:
            df_balance = pd.read_excel(archivo_cargado, sheet_name=pestana_balance).set_index('Cuenta')
            df_resultados = pd.read_excel(archivo_cargado, sheet_name=pestana_resultados).set_index('Cuenta')
            
            # Limpiar índices
            df_balance.index = df_balance.index.str.strip()
            df_resultados.index = df_resultados.index.str.strip()

            total_activos = df_balance.loc['Total Activos', 'Valor']
            pasivo_corriente_sin_costo = df_balance.loc['Pasivo Corriente (Sin Costo Financiero)', 'Valor']
            deuda_financiera = df_balance.loc['Deuda Financiera (Corto y Largo Plazo)', 'Valor']
            patrimonio = df_balance.loc['Patrimonio Neto', 'Valor']

            uaii = df_resultados.loc['Utilidad Operativa (UAII)', 'Valor']
            gastos_financieros = df_resultados.loc['Gastos Financieros (Intereses)', 'Valor']
            impuestos = df_resultados.loc['Impuestos de Renta', 'Valor']
            utilidad_antes_impuestos = df_resultados.loc['Utilidad Antes de Impuestos', 'Valor']

            # --- CÁLCULOS CORE ---
            T = impuestos / utilidad_antes_impuestos
            Kd = gastos_financieros / deuda_financiera
            V = deuda_financiera + patrimonio
            Wd = deuda_financiera / V
            We = patrimonio / V
            
            wacc = (Wd * Kd * (1 - T)) + (We * ke_usuario)
            uodi = uaii * (1 - T)
            capital_invertido = total_activos - pasivo_corriente_sin_costo
            cargo_capital = capital_invertido * wacc
            eva = uodi - cargo_capital
            roic = uodi / capital_invertido

            # --- INTERFAZ ---
            tab1, tab2 = st.tabs(["🎯 Diagnóstico Actual", "🔮 Proyección de Escenarios"])
            
            with tab1:
                st.subheader("Indicadores de Desempeño Financiero")
                col1, col2, col3 = st.columns(3)
                col1.metric(label="WACC", value=f"{wacc*100:.2f}%")
                col2.metric(label="ROIC", value=f"{roic*100:.2f}%")
                col3.metric(label="EVA", value=f"${eva:,.2f}")

                st.subheader("Visualización Operativa")
                chart_data = pd.DataFrame({
                    'Métrica': ['UODI', 'Cargo Capital'],
                    'Valor': [uodi, cargo_capital]
                })
                st.bar_chart(data=chart_data, x='Métrica', y='Valor')

            with tab2:
                st.subheader("Análisis de Escenarios")
                datos_escenarios = {
                    "Escenario": ["Optimista", "Base", "Pesimista"],
                    "UODI": [uodi * 1.10, uodi, uodi * 0.85],
                    "EVA": [(uodi * 1.10) - (capital_invertido * (wacc - 0.01)), eva, (uodi * 0.85) - (capital_invertido * (wacc + 0.02))]
                }
                st.table(pd.DataFrame(datos_escenarios))

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Cargue su archivo Excel para comenzar.")
# --- 1. EXTRACCIÓN DE NUEVAS VARIABLES DEL EXCEL ---
            # Asegúrate de que estas cuentas existan en tu archivo Excel
            total_activos_corrientes = df_balance.loc['Activo Corriente', 'Valor']
            pasivo_corriente = df_balance.loc['Pasivo Corriente', 'Valor']
            total_pasivos = df_balance.loc['Total Pasivos', 'Valor']
            inventarios = df_balance.loc['Inventarios', 'Valor']
            ventas = df_resultados.loc['Ingresos Totales', 'Valor']
            cuentas_por_cobrar = df_balance.loc['Cuentas por Cobrar', 'Valor']

            # --- 2. CÁLCULOS DE RATIOS (CORREGIDOS) ---
            # Liquidez
            razon_corriente = total_activos_corrientes / pasivo_corriente
            prueba_acida = (total_activos_corrientes - inventarios) / pasivo_corriente
            
            # Endeudamiento
            endeudamiento_total = (total_pasivos / total_activos) * 100
            apalancamiento = (total_pasivos / patrimonio)
            
            # Actividad
            rotacion_activos = ventas / total_activos
            dias_cobro = (cuentas_por_cobrar * 360) / ventas

            # --- 3. MOTOR DE RECOMENDACIONES COGNITIVAS ---
            def generar_diagnostico(eva, liq, end, roic, wacc):
                alertas = []
                recomendaciones = []
                
                if eva > 0:
                    alertas.append("✅ **VALOR:** La empresa crea valor económico.")
                else:
                    alertas.append("❌ **VALOR:** Destrucción de valor detectada.")
                    recomendaciones.append("- Revisar eficiencia operativa para subir el ROIC.")

                if liq < 1.2:
                    alertas.append("⚠️ **LIQUIDEZ:** Capacidad de pago limitada a corto plazo.")
                    recomendaciones.append("- Evaluar factoraje para convertir cuentas por cobrar en efectivo rápido.")

                if end > 60:
                    alertas.append("🚩 **SOLVENCIA:** El nivel de deuda es elevado (>60%).")
                    recomendaciones.append("- Evitar adquirir nuevos créditos financieros este periodo.")
                
                return alertas, recomendaciones

            # --- 4. INTERFAZ DE RESULTADOS ---
            tab1, tab2, tab3 = st.tabs(["🎯 EVA", "🔮 Escenarios", "📊 Ratios e Informe"])

            with tab3:
                st.subheader("Análisis de Salud Financiera")
                c1, c2, c3 = st.columns(3)
                c1.metric("Razón Corriente", f"{razon_corriente:.2f}")
                c2.metric("Endeudamiento", f"{endeudamiento_total:.1f}%")
                c3.metric("Rotación Activos", f"{rotacion_activos:.2f}x")

                st.markdown("---")
                st.subheader("📋 Informe de Recomendaciones IA")
                alertas_ia, recs_ia = generar_diagnostico(eva, razon_corriente, endeudamiento_total, roic, wacc)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Diagnósticos:**")
                    for a in alertas_ia: st.write(a)
                with col_b:
                    st.write("**Acciones Sugeridas:**")
                    for r in recs_ia: st.write(r)
