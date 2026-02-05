#!/usr/bin/env python3
"""
UK Ministerial Gifts & Hospitality Tracker

A Streamlit app to search and explore UK ministerial gift and hospitality declarations.
Data sourced from GOV.UK "Register of Ministers' Gifts and Hospitality" publications.

Run with: streamlit run gifts_app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from uk_gifts_search import (
    search_gifts,
    search_hospitality,
    get_all_ministers,
    get_all_departments,
    get_index_stats,
    load_index
)

# Page config
st.set_page_config(
    page_title="UK Ministerial Gifts & Hospitality Tracker",
    page_icon="🎁",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🎁 UK Ministerial Gifts & Hospitality Tracker")
    
    # Load index stats
    stats = get_index_stats()
    
    if "error" in stats:
        st.error("Could not load index. Please ensure uk_gifts_index.json exists.")
        return
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Gifts", f"{stats['gift_count']:,}")
    with col2:
        st.metric("Total Hospitality", f"{stats['hospitality_count']:,}")
    with col3:
        st.metric("Ministers", stats['ministers'])
    with col4:
        st.metric("Coverage", stats['metadata'].get('coverage', 'N/A'))
    
    st.markdown("---")
    
    # Search interface
    st.subheader("🔍 Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input(
            "Search gifts and hospitality",
            placeholder="e.g., BBC, UAE, Financial Times, France...",
            help="Supports Boolean operators: AND, OR, NOT, quotes, parentheses"
        )
    
    with col2:
        search_type = st.radio(
            "Search in",
            ["Both", "Gifts only", "Hospitality only"],
            horizontal=True
        )
    
    # Filters
    with st.expander("Advanced Filters"):
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            ministers = ["All"] + get_all_ministers()
            selected_minister = st.selectbox("Minister", ministers)
        
        with filter_col2:
            departments = ["All"] + get_all_departments()
            selected_dept = st.selectbox("Department", departments)
        
        with filter_col3:
            date_range = st.date_input(
                "Date range",
                value=(datetime(2024, 7, 1), datetime.now()),
                min_value=datetime(2024, 1, 1),
                max_value=datetime.now()
            )
    
    # Process filters
    minister_filter = None if selected_minister == "All" else selected_minister
    dept_filter = None if selected_dept == "All" else selected_dept
    date_from = date_range[0].strftime("%Y-%m-%d") if len(date_range) == 2 else None
    date_to = date_range[1].strftime("%Y-%m-%d") if len(date_range) == 2 else None
    
    # Tabs for results
    tab1, tab2, tab3 = st.tabs(["📊 Results", "🎁 Gifts", "🍽️ Hospitality"])
    
    if search_term:
        # Search
        gift_results = None
        hosp_results = None
        
        if search_type in ["Both", "Gifts only"]:
            gift_results = search_gifts(
                search_term,
                minister=minister_filter,
                department=dept_filter,
                date_from=date_from,
                date_to=date_to
            )
        
        if search_type in ["Both", "Hospitality only"]:
            hosp_results = search_hospitality(
                search_term,
                minister=minister_filter,
                department=dept_filter,
                date_from=date_from,
                date_to=date_to
            )
        
        with tab1:
            st.subheader(f"Results for '{search_term}'")
            
            res_col1, res_col2 = st.columns(2)
            
            with res_col1:
                if gift_results:
                    st.metric("Gifts Found", gift_results["match_count"])
                    
                    if gift_results["by_minister"]:
                        st.write("**By Minister:**")
                        for minister, count in sorted(gift_results["by_minister"].items(), 
                                                       key=lambda x: x[1], reverse=True)[:5]:
                            st.write(f"- {minister}: {count}")
            
            with res_col2:
                if hosp_results:
                    st.metric("Hospitality Found", hosp_results["match_count"])
                    
                    if hosp_results["by_provider"]:
                        st.write("**Top Providers:**")
                        for provider, count in sorted(hosp_results["by_provider"].items(),
                                                       key=lambda x: x[1], reverse=True)[:5]:
                            st.write(f"- {provider}: {count}")
        
        with tab2:
            if gift_results and gift_results["matches"]:
                st.subheader(f"🎁 Gifts ({gift_results['match_count']} matches)")
                
                # Convert to DataFrame
                df = pd.DataFrame(gift_results["matches"])
                
                # Select and rename columns
                display_cols = ["date", "minister", "department", "gift", 
                              "donor_recipient", "given_or_received", "value", "outcome"]
                display_cols = [c for c in display_cols if c in df.columns]
                
                df_display = df[display_cols].copy()
                df_display.columns = ["Date", "Minister", "Department", "Gift",
                                     "From/To", "Given/Received", "Value", "Outcome"][:len(display_cols)]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Download button
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"gifts_{search_term.replace(' ', '_')}.csv",
                    "text/csv"
                )
            elif gift_results:
                st.info("No gift matches found")
        
        with tab3:
            if hosp_results and hosp_results["matches"]:
                st.subheader(f"🍽️ Hospitality ({hosp_results['match_count']} matches)")
                
                # Convert to DataFrame
                df = pd.DataFrame(hosp_results["matches"])
                
                # Select and rename columns
                display_cols = ["date", "minister", "department", "provider",
                              "hospitality_type", "value", "accompanied"]
                display_cols = [c for c in display_cols if c in df.columns]
                
                df_display = df[display_cols].copy()
                df_display.columns = ["Date", "Minister", "Department", "Provider",
                                     "Type", "Value", "Accompanied"][:len(display_cols)]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Download button
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"hospitality_{search_term.replace(' ', '_')}.csv",
                    "text/csv"
                )
            elif hosp_results:
                st.info("No hospitality matches found")
    
    else:
        # No search - show overview
        with tab1:
            st.info("Enter a search term above to find gifts and hospitality declarations")
            
            st.subheader("📈 Overview")
            
            # Load full data for overview
            index = load_index()
            if index:
                # Recent gifts
                st.write("**Recent Gifts (last 10):**")
                recent_gifts = sorted(index["gifts"], 
                                     key=lambda x: x.get("date", ""), 
                                     reverse=True)[:10]
                for g in recent_gifts:
                    st.write(f"- {g.get('date', 'N/A')} | **{g.get('minister', 'N/A')}**: "
                            f"{g.get('gift', 'N/A')} from {g.get('donor_recipient', 'N/A')}")
                
                st.write("")
                st.write("**Recent Hospitality (last 10):**")
                recent_hosp = sorted(index["hospitality"],
                                    key=lambda x: x.get("date", ""),
                                    reverse=True)[:10]
                for h in recent_hosp:
                    st.write(f"- {h.get('date', 'N/A')} | **{h.get('minister', 'N/A')}**: "
                            f"{h.get('hospitality_type', 'N/A')} from {h.get('provider', 'N/A')}")
    
    # Footer
    st.markdown("---")
    st.caption(
        "Data source: [GOV.UK Register of Ministers' Gifts and Hospitality]"
        "(https://www.gov.uk/government/collections/register-of-ministers-gifts-and-hospitality) | "
        f"Last updated: {stats['metadata'].get('created', 'Unknown')[:10]}"
    )
    st.caption(
        "Gifts over £140 and hospitality above de minimis levels must be declared. "
        "Search supports Boolean operators: AND, OR, NOT, quotes, and parentheses."
    )


if __name__ == "__main__":
    main()
