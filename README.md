# Dashboard de ventas Walmart

Dashboard interactivo desarrollado con Streamlit, Pandas y Plotly para explorar
ventas semanales, tiendas, semanas festivas y factores externos.

## Requisitos

- Python 3.9 o posterior
- Los paquetes de `requirements.txt`
- `Walmart_Sales.csv` o `Walmart_Sales.xlsx` junto a `app.py`

La aplicación prioriza `Walmart_Sales.csv`. Si no está disponible, carga
automáticamente `Walmart_Sales.xlsx`. El Excel incluido en este espacio de trabajo
se puede utilizar directamente.

## Instalación y ejecución

```bash
python -m venv .venv
```

En Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instala las dependencias e inicia Streamlit:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Funcionalidades

- Filtros por rango de fechas, una o varias tiendas y tipo de semana.
- Indicadores de ventas totales, promedio semanal, tienda líder e impacto
  porcentual de las semanas festivas.
- Tendencia temporal, Top 10 de tiendas, dispersión de ventas frente a factores
  externos y boxplot por tipo de semana.
- Caché de datos para acelerar la carga y validación de columnas y registros.

El promedio semanal se calcula por registro tienda-semana. El impacto festivo
compara la venta media festiva con la media no festiva en el periodo y las tiendas
seleccionadas, incluso si los gráficos están filtrados a un solo tipo de semana.
