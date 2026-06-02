import streamlit as st
import os
import json
import sys
import pandas as pd

# Ensure the root directory is accessible for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.main import run_orchestrator

st.set_page_config(page_title="B2B Spec Normalization Orchestrator", layout="wide")

st.title("🎛️ Master Correction Agent for Seller Specs")
st.markdown("Precision **B2B Spec Normalization** using a proprietary LangGraph Pipeline.")

# Custom CSS for a clean, technical professional look
st.markdown("""
<style>
    .thought-container {
        background-color: #1a1c24;
        border-radius: 8px;
        padding: 20px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 20px;
        font-family: 'Consolas', 'Monaco', monospace;
    }
    .thought-line {
        color: #d1d5db;
        font-size: 1.05em;
        line-height: 1.5;
        margin-bottom: 8px;
        padding: 6px 0;
        border-bottom: 1px solid #2e323d;
    }
    .tag-thinking { color: #9B51E0; font-weight: bold; }
    .tag-thought { color: #F2C94C; font-weight: bold; }
    .tag-result { color: #27AE60; font-weight: bold; }
    .tag-anomaly { color: #EB5757; font-weight: bold; }
    .tag-skip { color: #828282; font-style: italic; }
    .tag-decision { color: #2D9CDB; font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("LLM Gateway API Key", type="password", value="sk-1V_j4KY8sPIELOSTD23UbQ")
    
    st.divider()
    
    st.header("Test Parameters")
    mcat_id_input = st.text_input("MCAT ID", value="")
    cat_name_input = st.text_input("Category Name", value="")
    
    run_btn = st.button("🚀 Run Analysis", type="primary")

# Main execution area
if run_btn:
    if not api_key_input:
        st.error("Please provide an API Key to run the orchestrator.")
    elif not mcat_id_input or not cat_name_input:
        st.error("Please provide both MCAT ID and Category Name.")
    else:
        # Inject API key into environment
        os.environ["LLM_GATEWAY_API_KEY"] = api_key_input
        
        st.info(f"Analyzing MCAT: **{mcat_id_input}** ({cat_name_input}). Please wait...")
        
        with st.spinner("Processing deep audit..."):
            try:
                # Execute the main orchestrator pipeline
                final_state = run_orchestrator(mcat_id_input, cat_name_input)
                final_output = final_state.get("final_output", {})
                
                st.success("Analysis Completed!")
                
                # Display Results in Tabs (Restoring original structure as requested)
                tabs = st.tabs([
                    "📊 Summary", 
                    "📂 Data Map", 
                    "📞 DS-1: Buyer Calls",
                    "🛠️ DS-2: Custom Specs",
                    "🔍 DS-3: Search Insights",
                    "📈 DS-4: Fill Rate",
                    "🎯 Missing Specs", 
                    "🔝 Sequencing", 
                    "💡 Options (Audited)", 
                    "🧠 Thought Stream",
                    "📝 Comparison"
                ])
                
                tab1, tab2, tab1_ds1, tab1_ds2, tab1_ds3, tab1_ds4, tab7, tab8, tab9, tab10, tab_comp = tabs
                
                with tab1:
                    st.write("### Analysis Summary")
                    st.info(final_output.get("Summary", "No summary provided."))
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Master Confidence", final_output.get("Master_Decision", {}).get("confidence", "N/A"))
                    with col_b:
                        anom_count = len(final_output.get("Master_Decision", {}).get("anomalies", []))
                        st.metric("Anomalies Detected", anom_count, delta=None if anom_count == 0 else -anom_count, delta_color="inverse")
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### Availability Map")
                        st.json(final_output.get("Data_Availability", {}))
                    with col2:
                        st.write("### Data Source Richness Status")
                        ds_status = final_output.get("Data_Availability", {})
                        st.markdown(f"- **DS-1 (Buyer Calls)**: `{ds_status.get('DS-1 Buyer-Seller Call Data', 'EMPTY')}`")
                        st.markdown(f"- **DS-2 (Custom Specs)**: `{ds_status.get('DS-2 Custom Specs Data', 'EMPTY')}`")
                        st.markdown(f"- **DS-3 (Buyer Search)**: `{ds_status.get('DS-3 Buyer Search Data', 'EMPTY')}`")
                        st.markdown(f"- **DS-4 (Fill Rate)**: `{ds_status.get('DS-4 Product Fill Rate', 'EMPTY')}`")

                with tab1_ds1:
                    st.write("### 📞 DS-1 Agent: Buyer-Seller Call Analysis")
                    st.subheader("🤖 AI Agent Insights")
                    st.json(final_output.get("DS1_Agent", {}))
                    st.subheader("📄 Raw Source Data")
                    st.json(final_output.get("DS1_Data", []))

                with tab1_ds2:
                    st.write("### 🛠️ DS-2 Agent: Custom Specification Analysis")
                    st.subheader("🤖 AI Agent Insights")
                    st.json(final_output.get("DS2_Agent", {}))
                    st.subheader("📄 Raw Source Data")
                    st.json(final_output.get("DS2_Data", []))

                with tab1_ds3:
                    st.write("### 🔍 DS-3 Agent: Buyer Search Intent")
                    st.subheader("🤖 AI Agent Insights")
                    st.json(final_output.get("DS3_Agent", {}))
                    st.subheader("📄 Raw Source Data")
                    st.json(final_output.get("DS3_Data", []))

                with tab1_ds4:
                    st.write("### 📈 DS-4: Product Fill Rate Stats")
                    st.json(final_output.get("DS4_Data", []))

                with tab7: 
                    st.write("### 🎯 Missing Specs Agent Output")
                    st.json(final_output.get("Missing_Specs", {}))
                    
                with tab8: 
                    st.write("### 🔝 Sequencing Agent Output")
                    st.json(final_output.get("Sequence", {}))

                with tab9:
                    st.write("### 💎 Option Mapping & Importance Audit")
                    audit = final_output.get("Final_Option_Audit", [])
                    if audit:
                        st.markdown("---")
                        # Group by spec for better organization
                        df_audit = pd.DataFrame(audit)
                        for spec, group in df_audit.groupby("spec_name"):
                            st.write(f"**Attribute: `{spec}`**")
                            for idx, (_, row) in enumerate(group.iterrows()):
                                imp = str(row.get("importance", "")).upper()
                                dec = str(row.get("decision", "")).upper()
                                val = row.get("option_value", "")
                                reason = row.get("reason", "")
                                
                                if "HIGH" in imp:
                                    status = "KEEP" if "KEEP" in dec else "MERGE"
                                    st.markdown(f"🔴 **{val}** ({status}) - {reason}")
                                else:
                                    st.markdown(f"☠️ *{val}* (REJECT) - {reason}")
                            st.markdown("---")
                    else:
                        st.info("No option audit data available currently.")

                with tab10:
                    st.write("### 🧠 Master Agent — Native Reasoning Stream")
                    st.caption("This is the exact, unmodified `reasoning_content` extracted directly from the LLM API response of the Master Orchestrator.")
                    
                    full_reasoning = final_output.get("Master_Reasoning", "").strip()

                    if full_reasoning:
                        # Displaying as plain text for a terminal-like experience as requested
                        st.text(full_reasoning)
                    else:
                        st.info("_No native reasoning captured._")

                with tab_comp:
                    st.write("### 📝 Side-by-Side Comparison")
                    comp = final_output.get("Comparison_View", {})
                    if comp:
                        col_pre, col_post = st.columns(2)
                        with col_pre:
                            st.subheader("🚩 Pre-Platform (DS-0)")
                            st.json(comp.get("pre_platform_specs", []))
                        with col_post:
                            st.subheader("✅ Final Corrected Output")
                            st.json(comp.get("final_corrected_specs", []))



                st.divider()
                st.subheader("Master Output Inspection")
                with st.expander("Click to View Complete System Execution JSON (Raw State)"):
                    st.json(final_output)

            except Exception as e:
                st.error(f"An error occurred during execution: {str(e)}")
else:
    st.info("Enter configuration in the sidebar and click **Run Orchestrator** to start.")
