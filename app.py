 from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent
REQUIRED_COLUMNS = {
    "Store",
    "Date",
    "Weekly_Sales",
    "Holiday_Flag",
    "Temperature",
    "Fuel_Price",
    "CPI",
    "Unemployment",
}
FACTOR_LABELS = {
    "Temperature": "Temperatura",
    "Fuel_Price": "Precio del combustible",
    "CPI": "Índice de precios al consumidor",
    "Unemployment": "Desempleo",
}
COLORS = {
    "primary": "#4f46e5",
    "holiday": "#f97316",
    "regular": "#4f46e5",
    "background": "#ffffff",
}


st.set_page_config(
    page_title="Walmart | Análisis de ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Cargando y preparando los datos...")
def load_sales_data(file_path: str, modified_at: int) -> pd.DataFrame:
    """Load the available source file and normalize the analysis columns."""
    path = Path(file_path)
    if path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
    elif path.suffix.lower() == ".xlsx":
        data = pd.read_excel(path)
    else:
        raise ValueError(f"Formato de archivo no compatible: {path.suffix}")

    data.columns = data.columns.astype(str).str.strip()
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Faltan columnas obligatorias en el archivo: {missing}")

    data = data[list(REQUIRED_COLUMNS)].copy()
    data["Date"] = pd.to_datetime(data["Date"], dayfirst=True, errors="coerce")

    numeric_columns = [
        "Store",
        "Weekly_Sales",
        "Holiday_Flag",
        "Temperature",
        "Fuel_Price",
        "CPI",
        "Unemployment",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    invalid_required = (
        data[["Store", "Date", "Weekly_Sales", "Holiday_Flag"]].isna().any(axis=1)
        | ~data["Holiday_Flag"].isin([0, 1])
        | (data["Store"] % 1 != 0)
    )
    if invalid_required.any():
        raise ValueError(
            f"Se encontraron {int(invalid_required.sum())} registros con fecha, "
            "tienda, ventas o Holiday_Flag no válidos. Corrige esos registros "
            "y vuelve a ejecutar la aplicación."
        )
    data = data.copy()
    data["Store"] = data["Store"].astype(int)
    data["Holiday_Flag"] = data["Holiday_Flag"].astype(int)
    if data.empty:
        raise ValueError("El archivo no contiene registros válidos para analizar.")

    return data.sort_values("Date")


def find_data_file() -> Path:
    """Prefer the requested CSV, falling back to the workbook in this workspace."""
    for filename in ("Walmart_Sales.csv", "Walmart_Sales.xlsx"):
        path = DATA_DIR / filename
        if path.is_file():
            return path
    raise FileNotFoundError(
        "No se encontró Walmart_Sales.csv ni un archivo Excel "
        "(Walmart_Sales.xlsx) junto a app.py."
    )


def format_currency(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f} mil M"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f} M"
    return f"${value:,.0f}"


def render_scatter(data: pd.DataFrame, column: str, label: str) -> None:
    chart_data = data.copy()
    chart_data["Tipo de semana"] = chart_data["Holiday_Flag"].map(
        {0: "Normal", 1: "Festiva"}
    )
    chart = px.scatter(
        chart_data,
        x=column,
        y="Weekly_Sales",
        color="Tipo de semana",
        color_discrete_map={
            "Normal": COLORS["regular"],
            "Festiva": COLORS["holiday"],
        },
        opacity=0.65,
        hover_data={"Store": True, "Date": "|%d-%m-%Y", "Tipo de semana": False},
        labels={
            column: label,
            "Weekly_Sales": "Ventas semanales",
        },
    )
    chart.update_traces(marker={"size": 7})
    chart.update_layout(
        height=340,
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        legend={
            "title": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        xaxis={"gridcolor": "#eef0f5"},
        yaxis={"gridcolor": "#eef0f5", "tickprefix": "$", "tickformat": ",.0f"},
        plot_bgcolor=COLORS["background"],
    )
    st.plotly_chart(chart, use_container_width=True)


st.markdown(
    """
    <style>
    .stApp { background: #f6f7fb; }
    [data-testid="stHeader"] { background: rgba(246, 247, 251, 0.92); }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e9ebf2;
        padding: 18px 20px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(20, 25, 50, 0.04);
    }
    [data-testid="stMetricLabel"] { color: #687086; }
    [data-testid="stMetricValue"] { color: #20243a; }
    h1, h2, h3 { color: #20243a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Walmart | Análisis de ventas")
st.caption("Explora el rendimiento semanal, las tiendas y los factores externos.")

try:
    source_file = find_data_file()
    sales = load_sales_data(str(source_file), source_file.stat().st_mtime_ns)
except (FileNotFoundError, ImportError, OSError, ValueError) as error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()

st.sidebar.header("Filtros")
st.sidebar.caption(f"Fuente de datos: `{source_file.name}`")

minimum_date = sales["Date"].min().date()
maximum_date = sales["Date"].max().date()
selected_dates = st.sidebar.date_input(
    "Rango de fechas",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date,
    format="DD/MM/YYYY",
)

stores = sorted(sales["Store"].unique().tolist())
selected_stores = st.sidebar.multiselect(
    "Tiendas",
    options=stores,
    default=stores,
    format_func=lambda store: f"Tienda {store}",
)
holiday_selection = st.sidebar.selectbox(
    "Tipo de semana",
    options=["Todas", "Festivas", "No festivas"],
    help="Filtra los gráficos y métricas principales por tipo de semana.",
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    start_date = start_date or minimum_date
    end_date = end_date or start_date
else:
    start_date = end_date = selected_dates

period_data = sales.loc[
    sales["Date"].dt.date.between(start_date, end_date)
    & sales["Store"].isin(selected_stores)
].copy()

if holiday_selection == "Festivas":
    filtered_data = period_data.loc[period_data["Holiday_Flag"] == 1].copy()
elif holiday_selection == "No festivas":
    filtered_data = period_data.loc[period_data["Holiday_Flag"] == 0].copy()
else:
    filtered_data = period_data

total_sales = filtered_data["Weekly_Sales"].sum()
average_sales = filtered_data["Weekly_Sales"].mean()
if filtered_data.empty:
    top_store = "—"
else:
    top_store_id = filtered_data.groupby("Store")["Weekly_Sales"].sum().idxmax()
    top_store = f"Tienda {top_store_id}"

holiday_average = period_data.loc[
    period_data["Holiday_Flag"] == 1, "Weekly_Sales"
].mean()
regular_average = period_data.loc[
    period_data["Holiday_Flag"] == 0, "Weekly_Sales"
].mean()
if pd.notna(holiday_average) and pd.notna(regular_average) and regular_average != 0:
    holiday_impact = (holiday_average / regular_average - 1) * 100
    impact_value = f"{holiday_impact:+.1f}%"
else:
    impact_value = "N/D"

st.subheader("Indicadores del periodo")
kpi_columns = st.columns(4)
kpi_columns[0].metric("Ventas totales", format_currency(total_sales))
kpi_columns[1].metric(
    "Promedio por registro semanal",
    format_currency(average_sales) if pd.notna(average_sales) else "—",
)
kpi_columns[2].metric("Tienda líder", top_store)
kpi_columns[3].metric(
    "Impacto promedio festivo",
    impact_value,
    help="Cambio porcentual de la venta media festiva frente a la media no festiva. "
    "Se calcula con todas las semanas del periodo y tiendas seleccionadas.",
)
st.caption(
    f"El impacto festivo compara semanas festivas y normales dentro del periodo "
    f"y las tiendas elegidas, independientemente del filtro de tipo de semana."
)

st.divider()
st.subheader("Tendencia y rendimiento por tienda")
trend_column, store_column = st.columns((1.5, 1))

with trend_column:
    st.markdown("##### Ventas semanales a lo largo del tiempo")
    if filtered_data.empty:
        st.info("No hay datos para los filtros seleccionados.")
    else:
        weekly_sales = (
            filtered_data.groupby("Date", as_index=False)["Weekly_Sales"]
            .sum()
            .sort_values("Date")
        )
        trend_chart = px.line(
            weekly_sales,
            x="Date",
            y="Weekly_Sales",
            markers=True,
            labels={"Date": "Fecha", "Weekly_Sales": "Ventas semanales"},
            color_discrete_sequence=[COLORS["primary"]],
        )
        trend_chart.update_traces(line={"width": 2.5}, marker={"size": 5})
        trend_chart.update_layout(
            height=390,
            margin={"l": 8, "r": 8, "t": 16, "b": 8},
            xaxis={"gridcolor": "#eef0f5"},
            yaxis={
                "gridcolor": "#eef0f5",
                "tickprefix": "$",
                "tickformat": ",.0f",
            },
            plot_bgcolor=COLORS["background"],
        )
        st.plotly_chart(trend_chart, use_container_width=True)

with store_column:
    st.markdown("##### Top 10 tiendas por facturación")
    if filtered_data.empty:
        st.info("No hay datos para mostrar.")
    else:
        top_stores = (
            filtered_data.groupby("Store", as_index=False)["Weekly_Sales"]
            .sum()
            .nlargest(10, "Weekly_Sales")
            .sort_values("Weekly_Sales", ascending=True)
        )
        top_stores["Store"] = top_stores["Store"].astype(str)
        store_chart = px.bar(
            top_stores,
            x="Weekly_Sales",
            y="Store",
            orientation="h",
            text="Weekly_Sales",
            labels={"Weekly_Sales": "Ventas totales", "Store": "Tienda"},
            color_discrete_sequence=[COLORS["primary"]],
        )
        store_chart.update_traces(
            texttemplate="$%{x:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        store_chart.update_layout(
            height=390,
            margin={"l": 8, "r": 56, "t": 16, "b": 8},
            xaxis={
                "gridcolor": "#eef0f5",
                "tickprefix": "$",
                "tickformat": ",.0f",
            },
            yaxis={"title": "", "type": "category"},
            plot_bgcolor=COLORS["background"],
            showlegend=False,
        )
        st.plotly_chart(store_chart, use_container_width=True)

st.divider()
st.subheader("Factores externos y ventas")
if filtered_data.empty:
    st.info("Selecciona filtros con datos para explorar los factores externos.")
else:
    factor_columns = st.columns(2)
    for index, (column, label) in enumerate(FACTOR_LABELS.items()):
        with factor_columns[index % 2]:
            st.markdown(f"##### {label}")
            factor_data = filtered_data.dropna(subset=[column])
            if factor_data.empty:
                st.info(f"No hay valores de {label.lower()} para los filtros elegidos.")
            else:
                render_scatter(factor_data, column, label)

st.divider()
st.subheader("Comparación de semanas festivas y normales")
if period_data.empty:
    st.info("No hay datos para comparar en el periodo y tiendas seleccionados.")
else:
    holiday_data = period_data.copy()
    holiday_data["Tipo de semana"] = holiday_data["Holiday_Flag"].map(
        {0: "Normal", 1: "Festiva"}
    )
    holiday_chart = px.box(
        holiday_data,
        x="Tipo de semana",
        y="Weekly_Sales",
        color="Tipo de semana",
        category_orders={"Tipo de semana": ["Normal", "Festiva"]},
        color_discrete_map={
            "Normal": COLORS["regular"],
            "Festiva": COLORS["holiday"],
        },
        points="outliers",
        labels={"Weekly_Sales": "Ventas semanales"},
    )
    holiday_chart.update_layout(
        height=400,
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        yaxis={"gridcolor": "#eef0f5", "tickprefix": "$", "tickformat": ",.0f"},
        xaxis={"title": ""},
        plot_bgcolor=COLORS["background"],
        showlegend=False,
    )
    st.plotly_chart(holiday_chart, use_container_width=True)
