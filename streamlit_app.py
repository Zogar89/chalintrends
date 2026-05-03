from __future__ import annotations

from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from chalintrends.analytics import (
    average_delivery_pct_over_salon,
    category_daily_prices,
    latest_offers,
    salon_delivery_comparison,
)
from chalintrends.categories import category_sort_key, is_top_seller, sort_category_names
from chalintrends.live_search import live_search_input
from chalintrends.mock_data import generate_mock_history
from chalintrends.search import filter_products, product_matches
from chalintrends.storage import load_prices

DATA_PATH = Path("data/prices.csv")
PRICE_LIST_LABELS = {"salon": "Salon", "delivery": "Delivery"}
NAV_OPTIONS = ["Listado", "Ofertas", "Categorias", "Comparar cortes", "Salon vs Delivery"]
PAGE_SLUGS = {
    "Listado": "listado",
    "Ofertas": "ofertas",
    "Categorias": "categorias",
    "Comparar cortes": "comparar-cortes",
    "Salon vs Delivery": "salon-vs-delivery",
}
SLUG_PAGES = {slug: page for page, slug in PAGE_SLUGS.items()}
NAV_ICONS = {
    "Listado": ":material/view_list:",
    "Ofertas": ":material/local_offer:",
    "Categorias": ":material/bar_chart:",
    "Comparar cortes": ":material/monitoring:",
    "Salon vs Delivery": ":material/compare_arrows:",
}
SECTION_ICONS = {
    "Listado": "view_list",
    "Ofertas primero": "local_offer",
    "Bajaron vs hace 30 dias": "trending_down",
    "Tendencia por categoria": "bar_chart",
    "Comparar cortes": "monitoring",
    "Salon vs Delivery": "compare_arrows",
}
CATEGORY_ICONS = {
    "Achuras": "restaurant",
    "Vacuno premium": "workspace_premium",
    "Vacuno medio": "outdoor_grill",
    "Vacuno economico": "soup_kitchen",
    "Cerdo": "lunch_dining",
    "Pollo": "egg_alt",
    "Chacinados": "set_meal",
    "Elaborados": "room_service",
    "Otros": "category",
    "Sin categorizar": "help",
}
CATEGORY_CHART_COLORS = {
    "Vacuno premium": "#172033",
    "Vacuno medio": "#a82d25",
    "Vacuno economico": "#c0892e",
    "Pollo": "#2f9e68",
    "Cerdo": "#d66b36",
    "Achuras": "#1f78d1",
    "Chacinados": "#8a5fbf",
    "Elaborados": "#e08aa0",
    "Otros": "#2aa7a0",
    "Sin categorizar": "#687180",
}
COMPARISON_CHART_COLORS = [
    "#a82d25",
    "#172033",
    "#c0892e",
    "#0b7a48",
    "#1f78d1",
    "#8a5fbf",
    "#d66b36",
    "#2aa7a0",
]


def format_price(value: float | int | None) -> str:
    if pd.isna(value):
        return "-"
    return f"${int(value):,}".replace(",", ".")


def format_percent(value: float | None, *, decimals: int = 1) -> str:
    if pd.isna(value):
        return "base"
    if decimals == 0:
        rounded = int(value + 0.5) if value >= 0 else int(value - 0.5)
        return f"{rounded}%"
    return f"{value:.{decimals}f}%"


def format_trend_percent(value: float | None) -> str:
    if pd.isna(value):
        return "base"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%".replace(".", ",")


def money_delta(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin historial"
    sign = "+" if value > 0 else ""
    return f"{sign}{format_price(value)}"


def trend_badge_html(change: float | int | None, change_pct: float | None) -> str:
    if pd.isna(change_pct):
        return '<span class="trend-badge trend-flat">base</span>'

    numeric_change = change_pct if pd.isna(change) else change
    if numeric_change == 0:
        trend_class = "trend-flat"
    elif numeric_change < 0:
        trend_class = "trend-good"
    else:
        trend_class = "trend-bad"
    badge_text = format_trend_percent(change_pct)
    return f'<span class="trend-badge {trend_class}">{escape(badge_text)}</span>'


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink: #172033;
          --muted: #687180;
          --paper: #f6f1e8;
          --panel: #fffaf1;
          --line: #e0d5c5;
          --red: #a82d25;
          --green: #0b7a48;
          --gold: #c0892e;
        }

        .stApp {
          background:
            linear-gradient(180deg, rgba(168,45,37,.08), rgba(168,45,37,0) 220px),
            var(--paper);
          color: var(--ink);
        }

        [data-testid="stHeader"] {
          background: transparent;
        }

        div[data-testid="collapsedControl"],
        div[data-testid="stSidebarCollapsedControl"] {
          left: 14px;
          position: fixed;
          top: 14px;
          z-index: 100002;
        }

        div[data-testid="collapsedControl"] button,
        div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"],
        div[data-testid="stSidebarCollapsedControl"] button,
        div[data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"],
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] {
          align-items: center;
          background: #172033 !important;
          border: 1px solid rgba(255,250,241,.45) !important;
          border-radius: 999px !important;
          box-shadow: 0 12px 28px rgba(23,32,51,.24);
          color: #fffaf1 !important;
          display: inline-flex;
          height: 48px !important;
          justify-content: center;
          min-height: 48px !important;
          min-width: 48px !important;
          padding: 0 !important;
          width: 48px !important;
        }

        div[data-testid="collapsedControl"] button:hover,
        div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"]:hover,
        div[data-testid="stSidebarCollapsedControl"] button:hover,
        div[data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"]:hover,
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"]:hover {
          background: #22304a !important;
          border-color: rgba(226,193,125,.85) !important;
          color: #fffaf1 !important;
        }

        div[data-testid="collapsedControl"] svg,
        div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"] svg,
        div[data-testid="stSidebarCollapsedControl"] svg,
        div[data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"] svg,
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg {
          color: #fffaf1 !important;
          height: 26px !important;
          stroke-width: 2.4;
          width: 26px !important;
        }

        section[data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(255,250,241,.98), rgba(246,241,232,.98)),
            var(--panel);
          border-right: 1px solid var(--line);
        }

        section[data-testid="stSidebar"] > div {
          padding-top: 1.35rem;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
          color: var(--muted);
        }

        .sidebar-brand {
          border-bottom: 1px solid rgba(224,213,197,.75);
          margin: 0 0 14px;
          padding: 0 0 14px;
        }

        .sidebar-brand-title {
          align-items: center;
          color: var(--ink);
          display: flex;
          font-size: 1rem;
          font-weight: 800;
          gap: 8px;
          line-height: 1.2;
          margin: 0;
        }

        .sidebar-brand-title .material-symbols-rounded {
          background: #172033;
          border-radius: 8px;
          color: #fffaf1;
          font-size: 17px;
          height: 28px;
          justify-content: center;
          width: 28px;
        }

        .sidebar-kicker {
          color: var(--muted);
          font-size: .72rem;
          font-weight: 700;
          letter-spacing: .08em;
          margin: 10px 0 0;
          text-transform: uppercase;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] {
          margin-bottom: 6px;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
          background: transparent;
          border: 1px solid transparent;
          color: var(--ink);
          justify-content: flex-start;
          border-radius: 8px;
          min-height: 36px;
          padding: 7px 10px;
          font-size: .91rem;
          font-weight: 700;
          box-shadow: none;
          transition: background-color .15s ease, border-color .15s ease, color .15s ease;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
          background: rgba(23,32,51,.06);
          border-color: rgba(23,32,51,.12);
          color: var(--ink);
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="baseButton-primary"] {
          background: rgba(23,32,51,.08);
          border-color: rgba(23,32,51,.18);
          border-left-color: var(--gold);
          border-left-width: 4px;
          color: var(--ink);
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"]:hover,
        section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover {
          background: rgba(23,32,51,.11);
          border-color: rgba(23,32,51,.22);
          border-left-color: var(--gold);
          color: var(--ink);
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
          color: inherit;
          line-height: 1.15;
        }

        section[data-testid="stSidebar"] div[data-testid="stButton"] button .material-symbols-rounded {
          color: var(--gold);
          font-size: 18px;
        }

        .block-container {
          max-width: 760px;
          padding: 1.1rem 1rem 4rem;
        }

        h1, h2, h3, p {
          letter-spacing: 0;
        }

        .material-symbols-rounded {
          font-family: "Material Symbols Rounded";
          font-weight: normal;
          font-style: normal;
          line-height: 1;
          letter-spacing: normal;
          text-transform: none;
          display: inline-flex;
          white-space: nowrap;
          word-wrap: normal;
          direction: ltr;
          -webkit-font-feature-settings: "liga";
          -webkit-font-smoothing: antialiased;
          font-feature-settings: "liga";
        }

        .inline-icon {
          color: var(--gold);
          font-size: 17px;
          margin-right: 6px;
          vertical-align: -3px;
        }

        .hero {
          border: 1px solid #2a3548;
          background:
            linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,0) 38%),
            #172033;
          border-radius: 8px;
          padding: 12px 16px;
          color: white;
          box-shadow: 0 12px 30px rgba(23,32,51,.13);
          margin-bottom: 10px;
        }

        .eyebrow {
          color: #e2c17d;
          font-size: 10px;
          text-transform: uppercase;
          font-weight: 800;
          margin-bottom: 4px;
        }

        .hero-title {
          font-size: 24px;
          line-height: 1;
          font-weight: 900;
          margin-bottom: 6px;
        }

        .hero-copy {
          color: #d7dde8;
          font-size: 12px;
          line-height: 1.28;
          max-width: 30rem;
        }

        .summary-card-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          grid-template-areas:
            "trend up"
            "trend down";
          gap: 8px;
          margin: 12px 0 14px;
          align-items: stretch;
        }

        .trend-summary-panel {
          position: relative;
          margin: 0;
          border: 1px solid var(--line);
          background: rgba(255,253,248,.96);
          border-radius: 8px;
          padding: 12px 13px;
          overflow: hidden;
          box-shadow: 0 8px 18px rgba(23,32,51,.04);
        }

        .trend-panel-head {
          color: var(--ink);
          font-size: 12px;
          font-weight: 900;
          line-height: 1.15;
          margin-bottom: 9px;
          display: flex;
          align-items: center;
          gap: 6px;
          min-height: 20px;
        }

        .trend-summary-icon {
          position: absolute;
          top: 10px;
          right: 12px;
          width: 32px;
          height: 32px;
          border: 1px solid currentColor;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 19px;
          background: rgba(255,255,255,.55);
        }

        .trend-up {
          color: var(--red);
        }

        .trend-down {
          color: var(--green);
        }

        .trend-steady {
          color: var(--gold);
        }

        .trend-category-breakdown {
          display: grid;
          grid-template-columns: 1fr;
          gap: 0;
        }

        .trend-category-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: 8px;
          min-height: 32px;
          color: var(--ink);
          font-size: 11px;
          font-weight: 850;
          padding: 4px 0;
          border-bottom: 1px solid rgba(224,213,197,.68);
        }

        .trend-category-row:last-child {
          border-bottom: 0;
        }

        .trend-category-name {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .trend-category-icon {
          color: var(--gold);
          flex: 0 0 auto;
          font-size: 14px;
          line-height: 1;
        }

        .trend-category-value {
          flex: 0 0 auto;
          font-weight: 950;
        }

        .trend-category-row.trend-up .trend-category-value {
          color: var(--red);
        }

        .trend-category-row.trend-down .trend-category-value {
          color: var(--green);
        }

        .trend-category-row.trend-steady .trend-category-value {
          color: var(--gold);
        }

        .top-movers-card {
          min-height: 138px;
          padding-right: 52px;
        }

        .top-movers-card.trend-up {
          grid-area: up;
        }

        .top-movers-card.trend-down {
          grid-area: down;
        }

        .top-movers-card.trend-up {
          border-color: rgba(168,45,37,.45);
        }

        .top-movers-card.trend-down {
          border-color: rgba(11,122,72,.45);
        }

        .top-mover-list {
          display: grid;
          gap: 0;
          margin-top: 1px;
        }

        .top-mover-row {
          display: grid;
          grid-template-columns: 18px minmax(0, 1fr) auto;
          gap: 7px;
          align-items: center;
          color: var(--ink);
          font-size: 11px;
          font-weight: 800;
          padding: 6px 0;
          border-bottom: 1px solid rgba(224,213,197,.68);
        }

        .top-mover-row:last-child {
          border-bottom: 0;
        }

        .top-mover-rank {
          color: var(--ink);
          font-weight: 900;
        }

        .top-mover-name {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .top-mover-value {
          font-weight: 950;
        }

        .top-movers-card.trend-up .top-mover-value {
          color: var(--red);
        }

        .top-movers-card.trend-down .top-mover-value {
          color: var(--green);
        }

        .top-mover-caption {
          color: var(--muted);
          font-size: 10px;
          font-weight: 700;
          margin-top: 8px;
        }

        .category-trend-card {
          grid-area: trend;
        }

        .section-card {
          border: 1px solid var(--line);
          background: rgba(255,250,241,.92);
          border-radius: 8px;
          padding: 14px;
          margin: 12px 0;
        }

        .section-head {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 12px;
          margin-bottom: 10px;
        }

        .section-title {
          font-size: 18px;
          font-weight: 900;
          color: var(--ink);
          display: inline-flex;
          align-items: center;
        }

        .section-note {
          color: var(--muted);
          font-size: 12px;
          text-align: right;
        }

        .chart-title {
          color: var(--ink);
          font-size: 14px;
          font-weight: 950;
          margin: 12px 0 2px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        .chart-caption {
          color: var(--muted);
          font-size: 10px;
          font-weight: 720;
          line-height: 1.25;
          margin-bottom: 6px;
          max-width: 42rem;
        }

        .compare-picker-head {
          color: var(--ink);
          font-size: 14px;
          font-weight: 950;
          margin: 10px 0 4px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        div[data-testid="stVegaLiteChart"] {
          background: rgba(255,253,248,.96);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-sizing: border-box;
          width: 100%;
          padding: 14px 18px 10px;
          overflow: hidden;
          box-shadow: 0 8px 18px rgba(23,32,51,.04);
          margin-bottom: 14px;
        }

        div[data-testid="stVegaLiteChart"] > div,
        div[data-testid="stVegaLiteChart"] canvas,
        div[data-testid="stVegaLiteChart"] svg {
          max-width: 100% !important;
        }

        .price-list {
          display: grid;
          gap: 8px;
        }

        .price-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 10px;
          align-items: center;
          padding: 11px 12px;
          border: 1px solid #eadfce;
          background: #fffdf8;
          border-radius: 8px;
        }

        .category-section {
          margin: 16px 0 20px;
        }

        .category-head {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 12px;
          margin-bottom: 8px;
        }

        .category-title {
          color: var(--ink);
          font-size: 19px;
          font-weight: 900;
          display: inline-flex;
          align-items: center;
        }

        .category-count {
          color: var(--muted);
          font-size: 12px;
          font-weight: 750;
        }

        .category-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
          gap: 8px;
        }

        .category-grid-compact .category-card {
          min-height: 58px;
        }

        .category-grid-compact .category-sparkline {
          display: flex;
        }

        .category-card {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto 46px 70px;
          grid-template-areas: "info price change trend";
          align-items: center;
          gap: 9px;
          min-height: 54px;
          padding: 8px 9px;
          border: 1px solid #eadfce;
          background: #fffdf8;
          border-radius: 8px;
        }

        .category-card-main {
          grid-area: info;
          min-width: 0;
        }

        .category-card .price-side {
          grid-area: price;
        }

        .category-sparkline {
          grid-area: trend;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 5px;
          min-width: 0;
          margin-top: 0;
          color: var(--muted);
        }

        .sparkline-svg {
          width: 70px;
          height: 18px;
          overflow: visible;
          flex: 0 0 70px;
        }

        .product-name {
          color: var(--ink);
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
          line-height: 1.1;
          font-weight: 900;
          min-width: 0;
        }

        .product-name-text {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .top-seller-star {
          color: #f2b600;
          flex: 0 0 auto;
          font-size: 20px;
          font-weight: 900;
          line-height: 1;
        }

        .product-meta {
          color: var(--muted);
          font-size: 11px;
          margin-top: 2px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .price-side {
          text-align: right;
          white-space: nowrap;
        }

        .price {
          color: var(--ink);
          font-size: 15px;
          font-weight: 900;
          line-height: 1;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          margin-top: 5px;
          border-radius: 999px;
          padding: 3px 7px;
          font-size: 11px;
          font-weight: 850;
          border: 1px solid transparent;
        }

        .badge-good {
          color: var(--green);
          background: #e6f3ec;
          border-color: #bddfcf;
        }

        .badge-base {
          color: #7a5a1b;
          background: #f7ebcf;
          border-color: #ead49a;
        }

        .trend-badge {
          grid-area: change;
          display: block;
          margin-top: 0;
          font-size: 11px;
          line-height: 1;
          font-weight: 900;
          letter-spacing: 0;
          text-align: right;
          white-space: nowrap;
        }

        .trend-good {
          color: var(--green);
        }

        .trend-bad {
          color: var(--red);
        }

        .trend-flat {
          color: var(--muted);
        }

        .search-title {
          color: var(--ink);
          font-size: 13px;
          font-weight: 850;
          margin: 4px 0 6px;
          display: inline-flex;
          align-items: center;
        }

        .comparison-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
          gap: 8px;
        }

        .delivery-surcharge-card {
          align-items: center;
          background: #fffdf8;
          border: 1px solid #eadfce;
          border-radius: 8px;
          box-shadow: 0 8px 18px rgba(23,32,51,.04);
          display: grid;
          gap: 10px;
          grid-template-columns: minmax(0, 1fr) auto;
          margin: 0 0 10px;
          padding: 13px 14px;
        }

        .delivery-surcharge-label {
          color: var(--muted);
          font-size: 11px;
          font-weight: 850;
          letter-spacing: .06em;
          text-transform: uppercase;
        }

        .delivery-surcharge-value {
          color: var(--red);
          font-size: 30px;
          font-weight: 950;
          line-height: 1;
          margin-top: 3px;
        }

        .delivery-surcharge-value.trend-down {
          color: var(--green);
        }

        .delivery-surcharge-value.trend-flat {
          color: var(--gold);
        }

        .delivery-surcharge-caption {
          color: var(--muted);
          font-size: 12px;
          font-weight: 720;
          line-height: 1.25;
          margin-top: 5px;
        }

        .delivery-surcharge-icon {
          align-items: center;
          background: rgba(168,45,37,.08);
          border: 1px solid rgba(168,45,37,.24);
          border-radius: 999px;
          color: var(--red);
          display: inline-flex;
          font-size: 26px;
          height: 48px;
          justify-content: center;
          width: 48px;
        }

        .delivery-surcharge-icon.trend-down {
          background: rgba(11,122,72,.08);
          border-color: rgba(11,122,72,.24);
          color: var(--green);
        }

        .delivery-surcharge-icon.trend-flat {
          background: rgba(192,137,46,.1);
          border-color: rgba(192,137,46,.28);
          color: var(--gold);
        }

        .compare-card {
          border: 1px solid #eadfce;
          background: #fffdf8;
          border-radius: 8px;
          padding: 11px;
        }

        .compare-name {
          font-weight: 900;
          margin-bottom: 8px;
        }

        .compare-line {
          display: flex;
          justify-content: space-between;
          color: var(--muted);
          font-size: 13px;
          margin-top: 3px;
        }

        .compare-line strong {
          color: var(--ink);
        }

        .diff-pill,
        .same-price {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          padding: 3px 7px;
          font-size: 11px;
          font-weight: 850;
          white-space: nowrap;
        }

        .diff-pill {
          color: #6b4218;
          background: #f6e6d2;
          border: 1px solid #e7c49c;
        }

        .same-price {
          color: var(--green);
          background: #e6f3ec;
          border: 1px solid #bddfcf;
        }

        div[data-testid="stTextInput"] > label,
        div[data-testid="stMultiSelect"] > label,
        div[data-testid="stSelectbox"] > label {
          color: var(--ink);
          font-weight: 850;
        }

        div[data-testid="stMultiSelect"] {
          background: rgba(255,253,248,.96);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-sizing: border-box;
          padding: 10px 12px 12px;
          box-shadow: 0 8px 18px rgba(23,32,51,.04);
          margin: 0 0 14px;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) {
          margin: 0 0 12px;
          width: 100%;
          max-width: none;
          padding: 0;
          border: 0;
          border-radius: 0;
          background: transparent;
          box-shadow: none;
          backdrop-filter: none;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) > div,
        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [data-testid="stWidgetLabel"] {
          background: transparent !important;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) p {
          color: var(--muted);
          font-size: 12px;
          font-weight: 900;
          letter-spacing: 0;
          margin: 0 0 5px 2px;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [data-baseweb="button-group"],
        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [role="radiogroup"] {
          display: grid !important;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
          width: 100% !important;
          max-width: none !important;
          border-radius: 8px;
          background: #efe6d8;
          padding: 5px;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind^="segmented_control"] {
          min-height: 46px;
          width: 100% !important;
          justify-content: center;
          border: 1px solid transparent;
          border-radius: 8px;
          background: transparent;
          color: #687180;
          box-shadow: none;
          transition: transform .12s ease, border-color .12s ease, background-color .12s ease, box-shadow .12s ease;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind^="segmented_control"]:hover {
          transform: none;
          color: var(--ink);
          background: rgba(255,255,255,.36);
          box-shadow: none;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind^="segmented_control"] p {
          margin: 0;
          color: inherit;
          font-size: 16px;
          font-weight: 950;
          line-height: 1;
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind="segmented_controlActive"] {
          background: #fffdf8;
          color: var(--red);
          border-color: rgba(168,45,37,.34);
          box-shadow:
            inset 0 0 0 1px rgba(168,45,37,.12),
            0 6px 16px rgba(168,45,37,.16);
        }

        div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind="segmented_controlActive"] p {
          color: var(--red) !important;
        }

        div[data-testid="stTextInput"] input {
          background: #ffffff;
          border: 1px solid var(--line);
          border-radius: 8px;
          min-height: 52px;
          font-size: 18px;
          padding-left: 14px;
        }

        div[data-testid="stTextInput"] input:focus {
          border-color: var(--red);
          box-shadow: 0 0 0 2px rgba(168,45,37,.12);
        }

        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
          border-radius: 8px;
          border-color: var(--line);
          background: #fffdf8;
          min-height: 46px;
          box-shadow: inset 0 0 0 1px rgba(224,213,197,.28);
        }

        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
          background: rgba(168,45,37,.08);
          border: 1px solid rgba(168,45,37,.18);
          border-radius: 999px;
          color: var(--red);
          font-weight: 850;
        }

        div[data-testid="stTabs"] [role="tablist"] {
          gap: 4px;
          border-bottom: 1px solid var(--line);
        }

        div[data-testid="stTabs"] [role="tab"] {
          color: var(--muted);
          font-weight: 850;
          padding-left: 6px;
          padding-right: 6px;
        }

        div[data-testid="stTabs"] [aria-selected="true"] {
          color: var(--ink);
        }

        div[role="radiogroup"] label:has(input[type="radio"]) {
          border-radius: 8px;
          padding: 6px 8px;
        }

        @media (max-width: 760px) {
          div[data-testid="collapsedControl"],
          div[data-testid="stSidebarCollapsedControl"] {
            left: 12px;
            top: 12px;
          }

          div[data-testid="collapsedControl"] button,
          div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"],
          div[data-testid="stSidebarCollapsedControl"] button,
          div[data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"],
          section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] {
            height: 54px !important;
            min-height: 54px !important;
            min-width: 54px !important;
            width: 54px !important;
          }

          div[data-testid="collapsedControl"] svg,
          div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"] svg,
          div[data-testid="stSidebarCollapsedControl"] svg,
          div[data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"] svg,
          section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg {
            height: 30px !important;
            width: 30px !important;
          }

          .block-container {
            padding-left: .75rem;
            padding-right: .75rem;
          }

          .hero-title {
            font-size: 22px;
          }

          .hero {
            padding: 12px 14px;
          }

          .hero-copy {
            max-width: 100%;
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) {
            margin: 0 0 12px 0;
            width: 100% !important;
            max-width: none !important;
            box-sizing: border-box;
            padding: 0;
            background: transparent !important;
            border: 0;
            box-shadow: none;
            backdrop-filter: none;
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) p {
            color: var(--muted);
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [data-baseweb="button-group"],
          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            width: 100% !important;
            max-width: none !important;
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [data-baseweb="button-group"] > *,
          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) [role="radiogroup"] > * {
            flex: 1 1 0 !important;
            min-width: 0 !important;
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind^="segmented_control"] {
            flex: 1 1 0 !important;
            justify-content: center;
            max-width: none !important;
            min-width: 0 !important;
            width: 100% !important;
          }

          div[data-testid="stElementContainer"]:has(button[kind^="segmented_control"]) button[kind^="segmented_control"] p {
            overflow: visible;
            text-overflow: clip;
            white-space: nowrap;
          }

          .price-list,
          .price-row {
            width: 100%;
            box-sizing: border-box;
          }

          .trend-summary-panel {
            max-width: none;
          }

          .summary-card-grid {
            grid-template-columns: 1fr;
            grid-template-rows: none;
            grid-template-areas:
              "trend"
              "up"
              "down";
          }
        }

        @media (max-width: 560px) {
          .trend-category-breakdown {
            grid-template-columns: 1fr;
            max-width: none;
          }

          .section-head {
            display: block;
          }

          .section-note {
            text-align: left;
            margin-top: 3px;
          }

          .category-grid {
            grid-template-columns: 1fr;
          }

        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def category_trend_card_html(offers: pd.DataFrame) -> str:
    breakdown_rows = []
    for category in sort_category_names(offers["category"].dropna().unique()):
        group = offers[offers["category"] == category]
        category_change = pd.to_numeric(group["change_pct"], errors="coerce").mean()
        row_class = "trend-steady"
        if pd.notna(category_change) and category_change > 0.2:
            row_class = "trend-up"
        elif pd.notna(category_change) and category_change < -0.2:
            row_class = "trend-down"
        category_value = format_trend_percent(category_change) if pd.notna(category_change) else "base"
        category_name = "Carne" if str(category) == "Carnes" else str(category)
        category_icon = CATEGORY_ICONS.get(str(category), "category")
        breakdown_rows.append(
            f'<div class="trend-category-row {row_class}">'
            f'<span class="trend-category-name">'
            f'<span class="material-symbols-rounded trend-category-icon">{category_icon}</span>'
            f'{escape(category_name)}</span>'
            f'<span class="trend-category-value">{escape(category_value)}</span>'
            '</div>'
        )

    return (
        '<section class="trend-summary-panel category-trend-card">'
        '<div class="trend-panel-head"><span class="material-symbols-rounded inline-icon">monitoring</span>'
        'Tendencia General 30d</div>'
        f'<div class="trend-category-breakdown">{"".join(breakdown_rows)}</div>'
        '</section>'
    )


def top_movers_card_html(offers: pd.DataFrame, *, direction: str) -> str:
    is_up = direction == "up"
    clean = offers.dropna(subset=["change_pct"]).copy()
    if clean.empty:
        rows_html = '<div class="top-mover-caption">Sin historial suficiente</div>'
    else:
        ranked = clean.sort_values("change_pct", ascending=not is_up).head(3)
        rows = []
        for index, (_, row) in enumerate(ranked.iterrows(), start=1):
            rows.append(
                '<div class="top-mover-row">'
                f'<span class="top-mover-rank">{index}</span>'
                f'<span class="top-mover-name">{escape(str(row["product_name"]))}</span>'
                f'<span class="top-mover-value">{escape(format_trend_percent(row.get("change_pct")))}</span>'
                '</div>'
            )
        rows_html = "".join(rows)

    card_class = "trend-up" if is_up else "trend-down"
    title = "Top 3 que mas subieron" if is_up else "Top 3 que mas bajaron"
    icon = "trending_up" if is_up else "trending_down"
    return (
        f'<section class="trend-summary-panel top-movers-card {card_class}">'
        f'<div class="trend-panel-head">{escape(title)}</div>'
        f'<span class="material-symbols-rounded trend-summary-icon">{icon}</span>'
        f'<div class="top-mover-list">{rows_html}</div>'
        '<div class="top-mover-caption">Comparado con hace 30 dias</div>'
        '</section>'
    )


def render_summary_cards(offers: pd.DataFrame) -> None:
    if offers.empty:
        st.markdown(
            '<div class="section-card"><div class="product-meta">No hay datos para calcular tendencias.</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="summary-card-grid">'
        f'{category_trend_card_html(offers)}'
        f'{top_movers_card_html(offers, direction="up")}'
        f'{top_movers_card_html(offers, direction="down")}'
        '</div>',
        unsafe_allow_html=True,
    )


def product_name_html(product_name: object) -> str:
    name = str(product_name)
    star_html = (
        '<span class="top-seller-star" aria-label="Producto destacado">&#9733;</span>'
        if is_top_seller(name)
        else ""
    )
    return f'<div class="product-name">{star_html}<span class="product-name-text">{escape(name)}</span></div>'


def render_price_rows(
    df: pd.DataFrame,
    *,
    max_rows: int,
    empty_text: str,
    base_mode: bool = False,
    comparison_label: str = "hace 30 dias",
    waiting_label: str = "30 dias de historial",
) -> None:
    if df.empty:
        st.markdown(
            f'<div class="section-card"><div class="product-meta">{escape(empty_text)}</div></div>',
            unsafe_allow_html=True,
        )
        return

    rows_html = []
    for _, row in df.head(max_rows).iterrows():
        change_text = format_percent(row.get("change_pct"))
        delta_text = money_delta(row.get("change"))
        if base_mode or pd.isna(row.get("change_pct")):
            badge_class = "badge-base"
            badge_text = "linea base"
            meta = f"{row['category']} · esperando {waiting_label}"
        else:
            badge_class = "badge-good" if row.get("change", 0) <= 0 else "badge-base"
            badge_text = change_text
            meta = f"{row['category']} · {delta_text} vs {comparison_label}"

        rows_html.append(
            '<div class="price-row">'
            '<div>'
            f'{product_name_html(row["product_name"])}'
            f'<div class="product-meta">{escape(meta)}</div>'
            '</div>'
            '<div class="price-side">'
            f'<div class="price">{format_price(row["price"])}</div>'
            f'<span class="badge {badge_class}">{escape(badge_text)}</span>'
            '</div>'
            '</div>'
        )

    st.markdown(f'<div class="price-list">{"".join(rows_html)}</div>', unsafe_allow_html=True)


def sparkline_svg(values: list[float]) -> str:
    clean_values = [float(value) for value in values if pd.notna(value)]
    if not clean_values:
        return '<div class="category-sparkline"></div>'
    if len(clean_values) == 1:
        clean_values = [clean_values[0], clean_values[0]]

    width = 90
    height = 20
    pad = 3
    min_value = min(clean_values)
    max_value = max(clean_values)
    spread = max_value - min_value
    usable_height = height - pad * 2
    point_count = len(clean_values)
    points = []
    for index, value in enumerate(clean_values):
        x = 0 if point_count == 1 else (index / (point_count - 1)) * width
        y = height / 2 if spread == 0 else pad + ((max_value - value) / spread) * usable_height
        points.append(f"{x:.1f},{y:.1f}")

    stroke = "#0b7a48" if clean_values[-1] <= clean_values[0] else "#a82d25"
    last_x, last_y = points[-1].split(",")
    return (
        '<div class="category-sparkline">'
        f'<svg class="sparkline-svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{" ".join(points)}" fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.1" fill="{stroke}" />'
        '</svg>'
        '</div>'
    )


def build_sparkline_lookup(prices: pd.DataFrame, *, price_list: str, days: int = 30) -> dict[str, str]:
    history = prices[prices["price_list"] == price_list].copy()
    if history.empty:
        return {}

    history["date"] = pd.to_datetime(history["date"])
    latest = history["date"].max()
    start = latest - pd.Timedelta(days=days - 1)
    history = history[history["date"] >= start].sort_values("date")

    sparklines = {}
    for product_name, group in history.groupby("product_name", sort=False):
        daily_prices = group.groupby("date")["price"].last().dropna()
        sparklines[str(product_name)] = sparkline_svg(daily_prices.tolist())
    return sparklines


def render_grouped_listing(
    df: pd.DataFrame,
    *,
    empty_text: str,
    sparklines: dict[str, str],
    compact: bool = False,
) -> None:
    if df.empty:
        st.markdown(
            f'<div class="section-card"><div class="product-meta">{escape(empty_text)}</div></div>',
            unsafe_allow_html=True,
        )
        return

    sections_html = []
    sorted_df = df.copy()
    sorted_df["_category_rank"] = sorted_df["category"].map(lambda value: category_sort_key(str(value))[0])
    sorted_df = sorted_df.sort_values(["_category_rank", "category", "product_name"])
    for category, group in sorted_df.groupby("category", sort=False):
        cards_html = []
        for _, row in group.iterrows():
            change_meta = (
                "esperando 30 dias de historial"
                if pd.isna(row.get("change"))
                else f"{money_delta(row.get('change'))} vs 30 dias"
            )
            badge_html = trend_badge_html(row.get("change"), row.get("change_pct"))

            cards_html.append(
                '<div class="category-card">'
                '<div class="category-card-main">'
                f'{product_name_html(row["product_name"])}'
                f'<div class="product-meta">{escape(change_meta)}</div>'
                '</div>'
                '<div class="price-side">'
                f'<div class="price">{format_price(row["price"])}</div>'
                '</div>'
                f'{badge_html}'
                f'{sparklines.get(str(row["product_name"]), sparkline_svg([]))}'
                '</div>'
            )

        product_label = "producto" if len(group) == 1 else "productos"
        category_icon = CATEGORY_ICONS.get(str(category), "category")
        grid_class = "category-grid category-grid-compact" if compact else "category-grid"
        sections_html.append(
            '<section class="category-section">'
            '<div class="category-head">'
            f'<div class="category-title"><span class="material-symbols-rounded inline-icon">{category_icon}</span>{escape(str(category))}</div>'
            f'<div class="category-count">{len(group)} {product_label}</div>'
            '</div>'
            f'<div class="{grid_class}">{"".join(cards_html)}</div>'
            '</section>'
        )

    st.markdown("".join(sections_html), unsafe_allow_html=True)


def render_section(title: str, note: str) -> None:
    icon = SECTION_ICONS.get(title, "analytics")
    st.markdown(
        f"""
        <div class="section-head">
          <div class="section-title"><span class="material-symbols-rounded inline-icon">{icon}</span>{escape(title)}</div>
          <div class="section-note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_category_charts(category_prices: pd.DataFrame) -> None:
    data = category_prices.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["median_price"] = pd.to_numeric(data["median_price"], errors="coerce")
    data = data.dropna(subset=["median_price"]).sort_values(["category", "date"])
    if data.empty:
        st.write("No hay datos de categorias.")
        return

    category_order = sort_category_names(data["category"].dropna().unique().tolist())
    color_range = [CATEGORY_CHART_COLORS.get(category, "#687180") for category in category_order]

    baseline = (
        data.groupby("category", as_index=False)
        .first()[["category", "date", "median_price"]]
        .rename(columns={"date": "baseline_date", "median_price": "baseline_price"})
    )
    chart_data = data.merge(baseline, on="category", how="left")
    chart_data["index_value"] = (chart_data["median_price"] / chart_data["baseline_price"]) * 100
    chart_data["change_pct"] = ((chart_data["median_price"] - chart_data["baseline_price"]) / chart_data["baseline_price"]) * 100
    chart_data["price_label"] = chart_data["median_price"].map(format_price)
    chart_data["change_label"] = chart_data["change_pct"].map(format_trend_percent)

    st.markdown(
        '<div class="chart-title"><span class="material-symbols-rounded inline-icon">show_chart</span>Movimiento relativo</div>'
        '<div class="chart-caption">Base 100 por categoria para comparar evolucion sin que los precios altos dominen el grafico.</div>',
        unsafe_allow_html=True,
    )
    relative_base = alt.Chart(chart_data)
    relative_chart = (
        alt.Chart(pd.DataFrame({"index_value": [100]}))
        .mark_rule(color="#d8ccb9", strokeDash=[5, 5], strokeWidth=1)
        .encode(y="index_value:Q")
        + relative_base.mark_line(strokeWidth=2.4, interpolate="monotone", opacity=.92, clip=True).encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%d %b", labelColor="#687180", tickSize=0, labelPadding=8),
            ),
            y=alt.Y(
                "index_value:Q",
                title=None,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(labelColor="#687180", tickSize=0, labelPadding=8),
            ),
            color=alt.Color(
                "category:N",
                title=None,
                scale=alt.Scale(domain=category_order, range=color_range),
                legend=alt.Legend(
                    orient="bottom",
                    columns=3,
                    labelColor="#687180",
                    symbolStrokeWidth=3,
                    symbolSize=90,
                    labelFontSize=11,
                ),
            ),
            tooltip=[
                alt.Tooltip("category:N", title="Categoria"),
                alt.Tooltip("date:T", title="Fecha", format="%d/%m/%Y"),
                alt.Tooltip("price_label:N", title="Mediana"),
                alt.Tooltip("change_label:N", title="Cambio"),
            ],
        )
    ).properties(height=250, padding={"left": 6, "right": 18, "top": 8, "bottom": 6}, background="transparent")
    st.altair_chart(
        relative_chart.configure_view(strokeWidth=0).configure_axis(
            gridColor="#eadfce",
            gridOpacity=.68,
            domain=False,
            labelFontSize=11,
        ),
        use_container_width=True,
    )

    latest = chart_data.groupby("category", as_index=False).tail(1).copy()
    latest["category"] = pd.Categorical(latest["category"], categories=category_order, ordered=True)
    latest = latest.sort_values("median_price", ascending=True)
    max_median_price = float(latest["median_price"].max()) if not latest.empty else 0

    st.markdown(
        '<div class="chart-title"><span class="material-symbols-rounded inline-icon">format_align_left</span>Precio mediano actual</div>'
        '<div class="chart-caption">Ranking de niveles actuales, separado de la evolucion para leerlo rapido.</div>',
        unsafe_allow_html=True,
    )
    bars = alt.Chart(latest).mark_bar(cornerRadiusEnd=5, size=14).encode(
        y=alt.Y(
            "category:N",
            sort="-x",
            title=None,
            axis=alt.Axis(labelColor="#172033", labelFontWeight=800, tickSize=0, labelPadding=8),
        ),
        x=alt.X(
            "median_price:Q",
            title=None,
            scale=alt.Scale(domain=[0, max_median_price * 1.18]),
            axis=alt.Axis(format="$,.0f", labelColor="#687180", tickSize=0, labelPadding=8),
        ),
        color=alt.Color(
            "category:N",
            legend=None,
            scale=alt.Scale(domain=category_order, range=color_range),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="Categoria"),
            alt.Tooltip("price_label:N", title="Mediana actual"),
            alt.Tooltip("change_label:N", title="Cambio"),
        ],
    )
    labels = alt.Chart(latest).mark_text(align="left", baseline="middle", dx=7, color="#172033", fontWeight="bold", fontSize=11).encode(
        y=alt.Y("category:N", sort="-x"),
        x="median_price:Q",
        text="price_label:N",
    )
    st.altair_chart(
        (bars + labels)
        .properties(
            height=max(210, len(latest) * 30),
            padding={"left": 6, "right": 22, "top": 8, "bottom": 6},
            background="transparent",
        )
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False, domain=False, labelFontSize=11),
        use_container_width=True,
    )


def render_product_comparison_chart(product_history: pd.DataFrame, selected_products: list[str]) -> None:
    data = product_history.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["price"] = pd.to_numeric(data["price"], errors="coerce")
    data = data.dropna(subset=["price"]).sort_values(["product_name", "date"])
    if data.empty:
        st.write("No hay historial para los cortes seleccionados.")
        return

    product_order = [product for product in selected_products if product in set(data["product_name"])]
    color_range = [COMPARISON_CHART_COLORS[index % len(COMPARISON_CHART_COLORS)] for index in range(len(product_order))]
    data["price_label"] = data["price"].map(format_price)

    latest = data.groupby("product_name", as_index=False).tail(1).copy()
    latest["endpoint_label"] = latest.apply(
        lambda row: f'{row["product_name"]} · {format_price(row["price"])}',
        axis=1,
    )

    min_price = float(data["price"].min())
    max_price = float(data["price"].max())
    price_padding = max((max_price - min_price) * 0.16, 1200)
    min_date = data["date"].min()
    max_date = data["date"].max()
    x_domain = [min_date, max_date + pd.Timedelta(days=16)]

    st.markdown(
        '<div class="chart-title"><span class="material-symbols-rounded inline-icon">timeline</span>Evolucion de precios</div>'
        '<div class="chart-caption">Comparacion historica de los cortes seleccionados para la lista activa.</div>',
        unsafe_allow_html=True,
    )
    base = alt.Chart(data)
    line = base.mark_line(strokeWidth=2.8, interpolate="monotone", opacity=.92, clip=True).encode(
        x=alt.X(
            "date:T",
            title=None,
            scale=alt.Scale(domain=x_domain),
            axis=alt.Axis(format="%d %b", labelColor="#687180", tickSize=0, labelPadding=8),
        ),
        y=alt.Y(
            "price:Q",
            title=None,
            scale=alt.Scale(domain=[max(0, min_price - price_padding), max_price + price_padding]),
            axis=alt.Axis(format="$,.0f", labelColor="#687180", tickSize=0, labelPadding=8),
        ),
        color=alt.Color(
            "product_name:N",
            title=None,
            scale=alt.Scale(domain=product_order, range=color_range),
            legend=alt.Legend(
                orient="bottom",
                columns=3,
                labelColor="#687180",
                labelFontSize=11,
                symbolSize=90,
                symbolStrokeWidth=3,
            ),
        ),
        tooltip=[
            alt.Tooltip("product_name:N", title="Corte"),
            alt.Tooltip("date:T", title="Fecha", format="%d/%m/%Y"),
            alt.Tooltip("price_label:N", title="Precio"),
        ],
    )
    endpoint_labels = alt.Chart(latest).mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#172033",
        fontSize=10,
        fontWeight="bold",
        clip=True,
    ).encode(
        x=alt.X("date:T", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("price:Q", scale=alt.Scale(domain=[max(0, min_price - price_padding), max_price + price_padding])),
        text="endpoint_label:N",
        color=alt.Color("product_name:N", scale=alt.Scale(domain=product_order, range=color_range), legend=None),
    )

    chart = (line + endpoint_labels).properties(
        height=300,
        padding={"left": 6, "right": 48, "top": 10, "bottom": 6},
        background="transparent",
    )
    st.altair_chart(
        chart.configure_view(strokeWidth=0).configure_axis(
            gridColor="#eadfce",
            gridOpacity=.62,
            domain=False,
            labelFontSize=11,
        ),
        use_container_width=True,
    )


def render_comparison(comparison: pd.DataFrame, max_rows: int | None = None) -> None:
    if comparison.empty:
        st.write("No hay datos para comparar.")
        return

    rows_html = []
    visible_rows = comparison if max_rows is None else comparison.head(max_rows)
    for _, row in visible_rows.iterrows():
        diff = row.get("delivery_minus_salon")
        pct = row.get("delivery_pct_over_salon")
        same_price = pd.notna(diff) and abs(float(diff)) < 0.5
        if same_price:
            diff_html = '<span class="same-price">Mismo precio que delivery</span>'
        elif pd.notna(pct):
            diff_html = f'<span class="diff-pill">{escape(money_delta(diff))} ({pct:+.1f}%)</span>'
        else:
            diff_html = f"<strong>{escape(money_delta(diff))}</strong>"

        rows_html.append(
            '<div class="compare-card">'
            f'<div class="compare-name">{escape(str(row["product_name"]))}</div>'
            f'<div class="compare-line"><span>Salon</span><strong>{format_price(row.get("salon"))}</strong></div>'
            f'<div class="compare-line"><span>Delivery</span><strong>{format_price(row.get("delivery"))}</strong></div>'
            f'<div class="compare-line"><span>Diferencia</span>{diff_html}</div>'
            '</div>'
        )

    st.markdown(f'<div class="comparison-grid">{"".join(rows_html)}</div>', unsafe_allow_html=True)


def render_delivery_surcharge_card(comparison: pd.DataFrame) -> None:
    average_pct = average_delivery_pct_over_salon(comparison)
    required_columns = {"salon", "delivery", "delivery_pct_over_salon"}
    if required_columns.issubset(comparison.columns):
        salon = pd.to_numeric(comparison["salon"], errors="coerce")
        delivery = pd.to_numeric(comparison["delivery"], errors="coerce")
        pct = pd.to_numeric(comparison["delivery_pct_over_salon"], errors="coerce")
        compared_items = int((salon.notna() & delivery.notna() & (salon != 0) & pct.notna()).sum())
    else:
        compared_items = 0

    if average_pct is None:
        value = "Sin datos"
        tone_class = "trend-flat"
        icon = "remove"
        caption = "Faltan items con precio en Salon y Delivery."
    else:
        value = format_trend_percent(average_pct)
        if average_pct > 0:
            tone_class = "trend-up"
            icon = "trending_up"
        elif average_pct < 0:
            tone_class = "trend-down"
            icon = "trending_down"
        else:
            tone_class = "trend-flat"
            icon = "remove"
        item_label = "item" if compared_items == 1 else "items"
        caption = f"Promedio simple de {compared_items} {item_label} con precio en ambas listas."

    st.markdown(
        '<div class="delivery-surcharge-card">'
        '<div>'
        '<div class="delivery-surcharge-label">Recargo promedio Delivery</div>'
        f'<div class="delivery-surcharge-value {tone_class}">{escape(value)}</div>'
        f'<div class="delivery-surcharge-caption">{escape(caption)}</div>'
        '</div>'
        f'<span class="material-symbols-rounded delivery-surcharge-icon {tone_class}">{icon}</span>'
        '</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="ChalinTrends",
    page_icon=":material/monitoring:",
    layout="centered",
    initial_sidebar_state="auto",
)
inject_styles()

prices = load_prices(DATA_PATH)
if prices.empty:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Tracker personal</div>
          <div class="hero-title">ChalinTrends</div>
          <div class="hero-copy">Todavia no hay datos. Ejecuta <code>python scripts/update_prices.py</code> para cargar el primer snapshot.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

real_history_days = prices["date"].nunique()
st.session_state.setdefault("demo_mode", real_history_days < 2)
demo_mode = bool(st.session_state["demo_mode"])
if demo_mode:
    prices = generate_mock_history(prices)

history_days = prices["date"].nunique()
history_label = "historial demo sintetico" if demo_mode else "historial real"

st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">Precios de carne · seguimiento diario</div>
      <div class="hero-title">ChalinTrends</div>
      <div class="hero-copy">
        Ofertas primero, buscador siempre a mano y comparacion entre Salon y Delivery.
        {history_days} dia(s) de {history_label}.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

demo_mode = st.toggle(
    "Usar historial demo (3 meses)",
    key="demo_mode",
    help="Genera datos sinteticos desde el snapshot actual. No modifica data/prices.csv.",
)

requested_slug = st.query_params.get("page")
if isinstance(requested_slug, list):
    requested_slug = requested_slug[0] if requested_slug else None
requested_page = SLUG_PAGES.get(str(requested_slug), NAV_OPTIONS[0])
if requested_page not in NAV_OPTIONS:
    requested_page = NAV_OPTIONS[0]

st.session_state.setdefault("price_list", "salon")
if requested_page != "Salon vs Delivery":
    price_list = st.segmented_control(
        "Lista",
        options=["salon", "delivery"],
        key="price_list",
        format_func=lambda value: PRICE_LIST_LABELS[value],
    )
    if price_list is None:
        price_list = "salon"
else:
    price_list = st.session_state.get("price_list", "salon")

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-brand-title">
            <span class="material-symbols-rounded">monitoring</span>
            <span>ChalinTrends</span>
          </div>
          <div class="sidebar-kicker">Navegacion</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    visible_nav_options = NAV_OPTIONS
    if requested_slug and str(requested_slug) not in SLUG_PAGES:
        st.query_params["page"] = PAGE_SLUGS[requested_page]
    if "page" not in st.session_state:
        st.session_state["page"] = requested_page
    elif requested_slug and st.session_state["page"] != requested_page:
        st.session_state["page"] = requested_page
    if st.session_state["page"] not in visible_nav_options:
        st.session_state["page"] = visible_nav_options[0]

    for option in visible_nav_options:
        button_type = "primary" if st.session_state["page"] == option else "secondary"
        if st.button(
            option,
            icon=NAV_ICONS[option],
            type=button_type,
            use_container_width=True,
            key=f"nav_{option}",
        ):
            st.session_state["page"] = option
            st.query_params["page"] = PAGE_SLUGS[option]
            st.rerun()

page = st.session_state["page"]

offers = latest_offers(prices, price_list=price_list, window_days=30)
weekly_offers = latest_offers(prices, price_list=price_list, window_days=7)

if page == "Listado":
    render_summary_cards(offers)

query = ""
if page not in {"Categorias", "Comparar cortes"}:
    st.markdown(
        '<div class="search-title"><span class="material-symbols-rounded inline-icon">search</span>Buscar corte o producto</div>',
        unsafe_allow_html=True,
    )
    query = live_search_input(
        "Buscar corte o producto",
        placeholder="Asado, vacio, lomo...",
        key="global_search",
    )

if query:
    if not offers.empty:
        offers = filter_products(offers, query)
    if not weekly_offers.empty:
        weekly_offers = filter_products(weekly_offers, query)

if page == "Listado":
    render_section("Listado", f"Todos los productos de {PRICE_LIST_LABELS[price_list]}")
    sparklines = build_sparkline_lookup(prices, price_list=price_list, days=30)
    render_grouped_listing(
        offers,
        empty_text="No hay productos para esta busqueda.",
        sparklines=sparklines,
        compact=bool(query),
    )

elif page == "Ofertas":
    render_section(
        "Ofertas primero",
        "Bajas reales ordenadas por mayor porcentaje.",
    )
    if history_days < 2:
        baseline = offers.sort_values("price", ascending=False) if not offers.empty else offers
        st.markdown(
            '<div class="product-meta" style="margin-bottom: 8px;">Primer snapshot: esto es la linea base. Con mas historial aparecen bajas semanales y de 30 dias.</div>',
            unsafe_allow_html=True,
        )
        render_price_rows(
            baseline,
            max_rows=10,
            empty_text="No hay productos para esta busqueda.",
            base_mode=True,
        )
    else:
        weekly_drops = weekly_offers[weekly_offers["dropped_since_comparison"]] if not weekly_offers.empty else weekly_offers
        render_section("Bajaron esta semana", "Comparado contra el registro de hace 7 dias.")
        render_price_rows(
            weekly_drops.sort_values("change_pct", ascending=True, na_position="last")
            if not weekly_drops.empty
            else weekly_drops,
            max_rows=10,
            empty_text="Todavia no hay bajas registradas esta semana.",
            comparison_label="hace 7 dias",
            waiting_label="7 dias de historial",
        )

        render_section("Bajaron en 30 dias", "Comparado contra el registro de hace 30 dias.")
        drops = offers[offers["dropped_since_comparison"]] if not offers.empty else offers
        render_price_rows(
            drops.sort_values("change_pct", ascending=True, na_position="last") if not drops.empty else drops,
            max_rows=10,
            empty_text="Todavia no hay bajas registradas en 30 dias.",
            comparison_label="hace 30 dias",
            waiting_label="30 dias de historial",
        )

elif page == "Categorias":
    render_section("Tendencia por categoria", f"Evolucion y precios actuales de {PRICE_LIST_LABELS[price_list]}")
    category_prices = category_daily_prices(prices, price_list=price_list)
    if category_prices.empty:
        st.write("No hay datos de categorias.")
    else:
        render_category_charts(category_prices)

elif page == "Comparar cortes":
    render_section("Comparar cortes", f"Evolucion historica de {PRICE_LIST_LABELS[price_list]}")
    product_options = sorted(prices["product_name"].dropna().unique())
    if query:
        product_options = [product for product in product_options if product_matches(product, query)]
    default_candidates = ["Asado", "Vacío", "Vacio", "Lomo"]
    default_products = []
    for product in default_candidates:
        if product in product_options and product not in default_products:
            default_products.append(product)
    if not default_products:
        default_products = product_options[:3]
    st.markdown(
        '<div class="compare-picker-head"><span class="material-symbols-rounded inline-icon">add_chart</span>Cortes a comparar</div>'
        '<div class="chart-caption">Elegí uno o varios cortes para verlos en el mismo grafico.</div>',
        unsafe_allow_html=True,
    )
    selected_products = st.multiselect(
        "Productos",
        product_options,
        default=default_products,
        placeholder="Asado, vacio, lomo...",
        label_visibility="collapsed",
    )
    if selected_products:
        product_history = prices[
            (prices["price_list"] == price_list) & (prices["product_name"].isin(selected_products))
        ].copy()
        render_product_comparison_chart(product_history, selected_products)
    else:
        st.write("Elegí al menos un corte para comparar.")

elif page == "Salon vs Delivery":
    render_section("Salon vs Delivery", "Diferencia actual por producto")
    latest_prices = prices[prices["date"] == prices["date"].max()]
    overall_comparison = salon_delivery_comparison(latest_prices)
    if query:
        latest_prices = filter_products(latest_prices, query)
    comparison = salon_delivery_comparison(latest_prices)
    render_delivery_surcharge_card(overall_comparison)
    render_comparison(comparison)
