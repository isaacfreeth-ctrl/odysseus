#!/usr/bin/env python3
"""
UK Ministerial Gifts & Hospitality Tracker

A Streamlit app for searching UK ministerial gift and hospitality declarations.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import io

# Try to import boolean search
try:
    from boolean_search import boolean_match, is_boolean_query
    BOOLEAN_AVAILABLE = True
except ImportError:
    BOOLEAN_AVAILABLE = False
    def is_boolean_query(q): return False
    def boolean_match(q, t): return q.lower() in t.lower()


# Page config
st.set_page_config(
    page_title="UK Ministerial Gifts & Hospitality Tracker",
    page_icon="🎁",
    layout="wide"
)

# Load index
@st.cache_data
def load_index():
    """Load the gifts index."""
    local_path = Path(__file__).parent / "uk_gifts_index.json"
    if local_path.exists():
        with open(local_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def search_gifts(index, search_term, minister_filter=None):
    """Search gift declarations."""
    if not search_term:
        results = index["gifts"]
    else:
        use_boolean = BOOLEAN_AVAILABLE and is_boolean_query(search_term)
        search_lower = search_term.lower()
        
        results = []
        for gift in index["gifts"]:
            searchable = f"{gift.get('donor_recipient', '')} {gift.get('gift', '')}".lower()
            
            if use_boolean:
                if boolean_match(search_term, searchable):
                    results.append(gift)
            else:
                if search_lower in searchable:
                    results.append(gift)
    
    # Apply minister filter
    if minister_filter and minister_filter != "All":
        results = [g for g in results if g.get("minister") == minister_filter]
    
    return results


def search_hospitality(index, search_term, minister_filter=None):
    """Search hospitality declarations."""
    if not search_term:
        results = index["hospitality"]
    else:
        use_boolean = BOOLEAN_AVAILABLE and is_boolean_query(search_term)
        search_lower = search_term.lower()
        
        results = []
        for hosp in index["hospitality"]:
            searchable = f"{hosp.get('provider', '')} {hosp.get('hospitality_type', '')}".lower()
            
            if use_boolean:
                if boolean_match(search_term, searchable):
                    results.append(hosp)
            else:
                if search_lower in searchable:
                    results.append(hosp)
    
    # Apply minister filter
    if minister_filter and minister_filter != "All":
        results = [h for h in results if h.get("minister") == minister_filter]
    
    return results


def create_excel_download(gifts, hospitality, search_term):
    """Create Excel file with search results."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if gifts:
            df_gifts = pd.DataFrame(gifts)
            cols = ['minister', 'department', 'date', 'gift', 'donor_recipient', 
                    'given_or_received', 'value', 'outcome']
            cols = [c for c in cols if c in df_gifts.columns]
            df_gifts[cols].to_excel(writer, sheet_name='Gifts', index=False)
        
        if hospitality:
            df_hosp = pd.DataFrame(hospitality)
            cols = ['minister', 'department', 'date', 'provider', 'hospitality_type',
                    'value', 'accompanied']
            cols = [c for c in cols if c in df_hosp.columns]
            df_hosp[cols].to_excel(writer, sheet_name='Hospitality', index=False)
    
    output.seek(0)
    return output


# Main app
def main():
    st.title("🎁 UK Ministerial Gifts & Hospitality Tracker")
    
    # Load data
    index = load_index()
    
    if not index:
        st.error("Could not load gifts index. Please ensure uk_gifts_index.json exists.")
        return
    
    # Sidebar
    st.sidebar.header("About")
    st.sidebar.markdown(f"""
    **Coverage:** {index['metadata'].get('coverage', 'Unknown')}
    
    **Total Records:**
    - 🎁 {index['metadata']['gift_count']} gifts
    - 🍽️ {index['metadata']['hospitality_count']} hospitality
    
    **Last Updated:**  
    {index['metadata'].get('created', 'Unknown')[:10]}
    
    ---
    
    **Data Source:**  
    [GOV.UK Register of Ministers' Gifts and Hospitality](https://www.gov.uk/government/collections/register-of-ministers-gifts-and-hospitality)
    
    ---
    
    **Search Tips:**
    - Simple search: `UAE`
    - Boolean AND: `France AND wine`
    - Boolean OR: `BBC OR Sky`
    - Exact phrase: `"Financial Times"`
    """)
    
    # Get unique ministers for filter
    all_ministers = sorted(set(
        [g.get("minister", "") for g in index["gifts"]] +
        [h.get("minister", "") for h in index["hospitality"]]
    ))
    all_ministers = ["All"] + [m for m in all_ministers if m]
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Search donors, providers, or gift descriptions",
            placeholder="e.g., UAE, Financial Times, football tickets..."
        )
    
    with col2:
        minister_filter = st.selectbox("Filter by Minister", all_ministers)
    
    # Tabs for gifts vs hospitality
    tab1, tab2, tab3 = st.tabs(["🎁 Gifts", "🍽️ Hospitality", "📊 Summary"])
    
    # Search
    gifts = search_gifts(index, search_term, minister_filter if minister_filter != "All" else None)
    hospitality = search_hospitality(index, search_term, minister_filter if minister_filter != "All" else None)
    
    with tab1:
        st.subheader(f"Gifts ({len(gifts)} results)")
        
        if gifts:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            ministers = defaultdict(int)
            for g in gifts:
                ministers[g.get("minister", "Unknown")] += 1
            
            with col1:
                st.metric("Total Gifts", len(gifts))
            with col2:
                st.metric("Ministers", len(ministers))
            with col3:
                top_minister = max(ministers.items(), key=lambda x: x[1]) if ministers else ("N/A", 0)
                st.metric("Top Recipient", f"{top_minister[0][:20]}..." if len(top_minister[0]) > 20 else top_minister[0])
            
            # Table
            df = pd.DataFrame(gifts)
            display_cols = ['minister', 'date', 'gift', 'donor_recipient', 'value', 'outcome']
            display_cols = [c for c in display_cols if c in df.columns]
            
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "minister": "Minister",
                    "date": "Date",
                    "gift": "Gift",
                    "donor_recipient": "From/To",
                    "value": "Value",
                    "outcome": "Outcome"
                }
            )
        else:
            st.info("No gifts found matching your search.")
    
    with tab2:
        st.subheader(f"Hospitality ({len(hospitality)} results)")
        
        if hospitality:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            providers = defaultdict(int)
            for h in hospitality:
                providers[h.get("provider", "Unknown")] += 1
            
            with col1:
                st.metric("Total Records", len(hospitality))
            with col2:
                st.metric("Unique Providers", len(providers))
            with col3:
                top_provider = max(providers.items(), key=lambda x: x[1]) if providers else ("N/A", 0)
                st.metric("Top Provider", f"{top_provider[0][:20]}..." if len(top_provider[0]) > 20 else top_provider[0])
            
            # Table
            df = pd.DataFrame(hospitality)
            display_cols = ['minister', 'date', 'provider', 'hospitality_type', 'value']
            display_cols = [c for c in display_cols if c in df.columns]
            
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "minister": "Minister",
                    "date": "Date",
                    "provider": "Provider",
                    "hospitality_type": "Type",
                    "value": "Value"
                }
            )
        else:
            st.info("No hospitality found matching your search.")
    
    with tab3:
        st.subheader("Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Gift Recipients**")
            gift_by_minister = defaultdict(int)
            for g in index["gifts"]:
                gift_by_minister[g.get("minister", "Unknown")] += 1
            
            top_gift = sorted(gift_by_minister.items(), key=lambda x: -x[1])[:10]
            df_gift = pd.DataFrame(top_gift, columns=["Minister", "Gifts"])
            st.dataframe(df_gift, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Top Hospitality Recipients**")
            hosp_by_minister = defaultdict(int)
            for h in index["hospitality"]:
                hosp_by_minister[h.get("minister", "Unknown")] += 1
            
            top_hosp = sorted(hosp_by_minister.items(), key=lambda x: -x[1])[:10]
            df_hosp = pd.DataFrame(top_hosp, columns=["Minister", "Hospitality"])
            st.dataframe(df_hosp, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("**Top Hospitality Providers**")
        provider_counts = defaultdict(int)
        for h in index["hospitality"]:
            provider = h.get("provider", "")
            if provider and provider.lower() != "nil return":
                provider_counts[provider] += 1
        
        top_providers = sorted(provider_counts.items(), key=lambda x: -x[1])[:15]
        df_providers = pd.DataFrame(top_providers, columns=["Provider", "Count"])
        st.dataframe(df_providers, use_container_width=True, hide_index=True)
    
    # Download button
    if gifts or hospitality:
        st.markdown("---")
        excel_data = create_excel_download(gifts, hospitality, search_term or "all")
        
        filename = f"uk_gifts_{'_'.join(search_term.split()[:3]) if search_term else 'all'}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        st.download_button(
            label="📥 Download Results as Excel",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == "__main__":
    main()
