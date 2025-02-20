import pandas as pd
import os
from io import BytesIO
import streamlit as st
import zipfile
import time

# Set up the app
st.set_page_config(page_title="Data Sweeper", layout="wide", page_icon="./umair.png")

st.markdown("""
    <style>
        .st-emotion-cache-1104ytp egexzqm0 {
            padding: 0px !important;
            margin-bottom: 0px !important;
        }
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center; /* Aligns items vertically */
            width: 100%;
            margin-bottom: 0px;
        }
        .buttons-container {
            display: flex;
            gap: 10px;
        }
        .buttons-container a {
            text-decoration: none;
        }
        .buttons-container button {
            padding: 8px 16px;
            font-size: 14px;
            border-radius: 8px;
            border: 1px solid #ccc;
            background-color: white;
            cursor: pointer;
            transition: 0.3s;
        }
        .buttons-container button:hover {
            background-color: #f0f0f0;
        }
        .hr-tagg {
            margin-top: -30px;
        }

        @media (max-width: 1024px) {
            .buttons-container button {
                padding: 6px 10px;
                font-size: 14px;
            }
            .title-container h1 {
                font-size: 40px;
            }
            .title-container p {
                font-size: 14px;
            }
        }

        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                align-items: center; /* Centers everything */
                text-align: center;
            }
            .buttons-container {
                justify-content: center;
                width: 100%;
                margin-top: 10px; /* Adds spacing for clarity */
            }

            .buttons-container button {
                width: 100%; /* Full width buttons for mobile */
            }
            .hr-tagg {
                margin-top: -20px;
            }
        }

        @media (max-width: 640px) {
            .title-container h1 {
                font-size: 32px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# HTML for title & buttons
st.markdown("""
    <div class="header-container">
        <div class="title-container">
            <h1>📊 Data Sweeper</h1>
            <p>Transform your files between CSV and Excel formats with built-in data cleaning and visualization!</p>
        </div>
        <div class="buttons-container">
            <a href="https://umair-portfolio-web.vercel.app/" target="_blank">
                <button>🌍 Portfolio</button>
            </a>
            <a href="https://www.linkedin.com/in/umairnawaz7228/" target="_blank">
                <button>🔗 LinkedIn</button>
            </a>
            <a href="https://github.com/umair7228" target="_blank">
                <button>🐙 GitHub</button>
            </a>
        </div>
    </div>
    <div class="hr-tagg"><hr></div>
""", unsafe_allow_html=True)

# Initialize session state
if "processed_files" not in st.session_state:
    st.session_state.processed_files = {}
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "download_file_name" not in st.session_state:
    st.session_state.download_file_name = None

def update_dataframe(file_name, new_df):
    """Update the processed files with the transformed dataframe"""
    st.session_state.processed_files[file_name] = new_df

def create_zip_buffer():
    """Create ZIP buffer with all processed files"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for file_name, df in st.session_state.processed_files.items():
            buffer = BytesIO()
            if file_name.endswith('.xlsx'):
                df.to_excel(buffer, index=False)
                new_name = file_name.replace('.xlsx', '_processed.xlsx')
            else:
                df.to_csv(buffer, index=False)
                new_name = file_name.replace('.csv', '_processed.csv')
            zf.writestr(new_name, buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# File uploader
uploaded_files = st.file_uploader(
    "📂 Upload your files here (CSV or Excel)",
    type=["csv", "xlsx"],
    accept_multiple_files=True,
    key="file_uploader"
)

if uploaded_files:
    for file in uploaded_files:
        file_name = file.name
        file_ext = os.path.splitext(file_name)[-1].lower()

        # Initialize dataframe in session state
        if file_name not in st.session_state.processed_files:
            try:
                if file_ext == ".csv":
                    df = pd.read_csv(file, encoding='utf-8')
                else:
                    df = pd.read_excel(file)
                st.session_state.processed_files[file_name] = df
            except UnicodeDecodeError:
                df = pd.read_csv(file, encoding="ISO-8859-1")
                st.session_state.processed_files[file_name] = df

        df = st.session_state.processed_files[file_name]

        # Display file info
        st.write(f"📄 **File Name:** {file_name}")
        st.write(f"📏 **File Size:** {round(file.size / 1024, 2)} KB")

        # Preview the data
        with st.expander(f"🔍 Preview Data Head: {file_name}", expanded=False):
            if st.checkbox("Show Data Head"):
                st.dataframe(df.head())
            elif st.checkbox("Show 100 Records"):
                st.dataframe(df.head(100))
            elif st.checkbox("Show Full Data"):
                st.dataframe(df)


        # Data Cleaning Options
        with st.expander(f"🧹 Data Cleaning Options: {file_name}", expanded=False):
            clean_data = st.checkbox(f"Enable Data Cleaning for: {file_name}", key=f"clean_{file_name}")

            if clean_data:
                col1, col2 = st.columns(2)

                with col1:
                    # Remove duplicates from specific columns
                    st.subheader("Remove Duplicates")
                    duplicate_columns = st.multiselect(
                        f"Select columns to remove duplicates from {file_name}", 
                        df.columns, 
                        key=f"duplicate_cols_{file_name}"
                    )

                    # Let the user choose the behavior
                    duplicate_behavior = st.radio(
                        f"Choose how to handle duplicates in {file_name}",
                        ["Replace duplicates with NaN", "Remove entire row"],
                        key=f"duplicate_behavior_{file_name}"
                    )

                    if st.button(f"Handle Duplicates for {file_name}"):
                        if duplicate_columns:
                            if duplicate_behavior == "Replace duplicates with NaN":
                                # Replace duplicates with NaN
                                mask = df.duplicated(subset=duplicate_columns, keep='first')
                                df.loc[mask, duplicate_columns] = None
                                st.success(f"Duplicates in {', '.join(duplicate_columns)} replaced with NaN!")
                            else:
                                # Remove entire row
                                df.drop_duplicates(subset=duplicate_columns, inplace=True, keep='first')
                                st.success(f"Duplicates in {', '.join(duplicate_columns)} removed (entire row deleted)!")
                            
                            # Update the DataFrame in session state
                            update_dataframe(file_name, df)
                        else:
                            st.warning("Please select at least one column.")

                    # Drop columns with missing values
                    st.subheader("Drop Columns with Missing Values")
                    missing_threshold = st.slider(
                        f"Drop columns with >% missing values", 
                        0, 100, 90, 
                        key=f"missing_{file_name}"
                    )
                    if st.button(f"Drop Empty Columns for {file_name}"):
                        cols_to_drop = df.columns[df.isnull().mean() > (missing_threshold / 100)]
                        df.drop(columns=cols_to_drop, inplace=True)
                        update_dataframe(file_name, df)
                        st.success(f"Dropped {len(cols_to_drop)} columns: {', '.join(cols_to_drop)}")

                with col2:
                    # Fill missing values for specific columns
                    st.subheader("Fill Missing Values")
                    fill_columns = st.multiselect(
                        f"Select columns to fill missing values for {file_name}", 
                        df.columns, 
                        key=f"fill_cols_{file_name}"
                    )
                    if fill_columns:
                        fill_method = st.selectbox(
                            f"Fill method for selected columns", 
                            ["Mean", "Median", "Mode", "Custom Value"], 
                            key=f"fill_method_{file_name}"
                        )
                        if fill_method == "Custom Value":
                            custom_value = st.text_input(
                                f"Enter custom value for selected columns", 
                                key=f"custom_value_{file_name}"
                            )
                        else:
                            custom_value = None

                        if st.button(f"Fill Missing Values for Selected Columns in {file_name}"):
                            for col in fill_columns:
                                if fill_method == "Mean":
                                    df[col].fillna(df[col].mean(), inplace=True)
                                elif fill_method == "Median":
                                    df[col].fillna(df[col].median(), inplace=True)
                                elif fill_method == "Mode":
                                    df[col].fillna(df[col].mode().iloc[0], inplace=True)
                                elif fill_method == "Custom Value":
                                    if custom_value:
                                        df[col].fillna(custom_value, inplace=True)
                                    else:
                                        st.warning("Please enter a custom value.")
                            update_dataframe(file_name, df)
                            st.success(f"Missing values filled for {', '.join(fill_columns)}!")
                    else:
                        st.warning("Please select at least one column to fill missing values.")

        # Select Columns to Keep
        with st.expander(f"🔧 Select Columns to Convert: {file_name}", expanded=False):
            columns = st.multiselect(f"Select columns for {file_name}", df.columns, default=df.columns, key=f"cols_{file_name}")
            df = df[columns]
            update_dataframe(file_name, df)

        # Data Visualization
        with st.expander(f"📈 Data Visualization: {file_name}", expanded=False):
            data_viz = st.checkbox(f"Visualize data for: {file_name}", key=f"viz_{file_name}")

            if data_viz:
                # Filter numeric columns for visualization
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

                if not numeric_columns:
                    st.warning("No numeric columns found for visualization. Please ensure your dataset contains numeric data.")
                else:
                    # Let the user select columns for visualization
                    viz_cols = st.multiselect(
                        f"Select columns to visualize", 
                        numeric_columns,
                        key=f"viz_cols_{file_name}"
                    )

                    if viz_cols:
                        chart_type = st.selectbox("Select chart type", ["Bar", "Line", "Scatter"], key=f"chart_{file_name}")

                        try:
                            if chart_type == "Bar":
                                st.bar_chart(df[viz_cols])
                            elif chart_type == "Line":
                                st.line_chart(df[viz_cols])
                            elif chart_type == "Scatter":
                                st.write("Select two numerical columns")
                                x_axis = st.selectbox("X-axis", numeric_columns, key=f"x_{file_name}")
                                y_axis = st.selectbox("Y-axis", numeric_columns, key=f"y_{file_name}")
                                st.scatter_chart(df[[x_axis, y_axis]])
                        except Exception as e:
                            st.error(f"Couldn't create chart: {str(e)}")
                    else:
                        st.warning("Please select at least one column to visualize.")

        # Conversion Options for Individual Files
        with st.expander(f"🔄 Conversion Options: {file_name}", expanded=False):
            conversion_type = st.radio(f"Convert {file_name} to:", ["CSV", "Excel"], key=f"convert_type_{file_name}")

            if st.button(f"Convert {file_name}"):
                buffer = BytesIO()

                if conversion_type == "CSV":
                    st.session_state.processed_files[file_name].to_csv(buffer, index=False)
                    file_name_download = file_name.replace(file_ext, "_processed.csv")
                    mime_type = "text/csv"
                elif conversion_type == "Excel":
                    st.session_state.processed_files[file_name].to_excel(buffer, index=False)
                    file_name_download = file_name.replace(file_ext, "_processed.xlsx")
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                buffer.seek(0)
                st.session_state.zip_buffer = buffer.getvalue()
                st.session_state.download_file_name = file_name_download

    # Batch Processing & ZIP Download
    if st.button("📦 Process All Files"):
        st.session_state.zip_buffer = create_zip_buffer()
        st.session_state.download_file_name = "processed_files.zip"

# Download handling
if st.session_state.get('zip_buffer'):
    st.download_button(
        label="⬇️ Download Processed Files",
        data=st.session_state.zip_buffer,
        file_name=st.session_state.download_file_name,
        mime="application/zip" if st.session_state.download_file_name.endswith('.zip') 
             else "text/csv" if st.session_state.download_file_name.endswith('.csv') 
             else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_{time.time()}"  # Unique key for each download
    )

# Final message
st.success("🎉 All files processed! Thank you for using Data Sweeper!")