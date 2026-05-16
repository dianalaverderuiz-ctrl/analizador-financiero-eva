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
            # --- 1. EXTRACCIÓN DE DATOS ---
            # Asegúrate de que estos nombres existan en tu columna 'Cuenta' del Excel
            df_balance.index = df_balance.index.str.strip()
            df_resultados.index = df_resultados.index.str.strip()
            total_activos = df_balance.loc['Total Activos', 'Valor']
            total_activos_corrientes = df_balance.loc['Activo Corriente', 'Valor']
            pasivo_corriente = df_balance.loc['Pasivo Corriente', 'Valor']
            total_pasivos = df_balance.loc['Total Pasivos', 'Valor']
            patrimonio = df_balance.loc['Patrimonio Neto', 'Valor']
            inventarios = df_balance.loc['Inventarios', 'Valor']
            cuentas_por_cobrar = df_balance.loc['Cuentas por Cobrar', 'Valor']
            
            uaii = df_resultados.loc['Utilidad Operativa (UAII)', 'Valor']
            ventas = df_resultados.loc['Ingresos Totales', 'Valor']
            gastos_financieros = df_resultados.loc['Gastos Financieros (Intereses)', 'Valor']
            impuestos = df_resultados.loc['Impuestos de Renta', 'Valor']
            utilidad_antes_impuestos = df_resultados.loc['Utilidad Antes de Impuestos', 'Valor']

            # --- 2. CÁLCULOS ---
            T = impuestos / utilidad_antes_impuestos
            Kd = gastos_financieros / deuda_financiera if deuda_financiera > 0 else 0
            V = deuda_financiera + patrimonio
            Wd = deuda_financiera / V if V > 0 else 0
            We = patrimonio / V if V > 0 else 0
            
            wacc = (Wd * Kd * (1 - T)) + (We * ke_usuario)
            uodi = uaii * (1 - T)
            capital_invertido = total_activos - pasivo_corriente_sin_costo
            cargo_capital = capital_invertido * wacc
            eva = uodi - cargo_capital
            roic = uodi / capital_invertido if capital_invertido > 0 else 0

            # Ratios adicionales
            razon_corriente = total_activos_corrientes / pasivo_corriente
            endeudamiento_total = (total_pasivos / total_activos) * 100
            rotacion_activos = ventas / total_activos

            # --- 3. INTERFAZ ---
            st.success("Análisis completado con éxito")
            col1, col2, col3 = st.columns(3)
            col1.metric("EVA", f"${eva:,.2f}")
            col2.metric("WACC", f"{wacc*100:.2f}%")
            col3.metric("Razón Corriente", f"{razon_corriente:.2f}")
            
            # Aquí puedes añadir el resto de pestañas y el informe...
