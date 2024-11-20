import numpy as np
import pandas as pd
import zipfile
import plotly.express as px
import matplotlib.pyplot as plt
import requests
from io import BytesIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pydeck as pdk


df = pd.read_csv("housing_with_coordinates.csv")

st.set_page_config(layout="wide", page_title="Orange County Housing App", page_icon="🏡")
st.markdown(
    """
    <h1 style='text-align: center; color: #2E8B57;'>🏡 Orange County Housing Analysis 🏡</h1>
    <p style='text-align: center; color: gray;'>Explore housing prices, trends, and insights.</p>
    """,
    unsafe_allow_html=True,
)

#CREATE FILTERS IN SIDEBAR
st.sidebar.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        background-color: #f7f9fc;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filters")
st.sidebar.markdown("Use the options below to explore the data.")

# Price Range Slider
price_range = st.sidebar.slider("Price Range", 
                                 min_value=int(df["Price"].min()), 
                                 max_value=int(df["Price"].max()), 
                                 value=(int(df["Price"].min()), int(df["Price"].max())))

# City Dropdown
cities = st.sidebar.multiselect( "Select Cities", options=df["City"].unique(), default=["Huntington Beach"])

# Bedrooms and Bathrooms
min_beds, max_beds = st.sidebar.slider(
    "Number of Bedrooms", 
    int(df["Beds"].min()), 
    int(df["Beds"].max()), 
    (int(df["Beds"].min()), int(df["Beds"].max()))
)

min_baths, max_baths = st.sidebar.slider(
    "Number of Bathrooms", 
    int(df["Baths"].min()), 
    int(df["Baths"].max()), 
    (int(df["Baths"].min()), int(df["Baths"].max()))
)

# Square Footage
sqft_range = st.sidebar.slider("Square Footage", 
                                min_value=int(df["Square Feet"].min()), 
                                max_value=int(df["Square Feet"].max()), 
                                value=(int(df["Square Feet"].min()), int(df["Square Feet"].max())))


#FILTER DATA
filtered_data = df[
    (df["Price"] >= price_range[0]) & 
    (df["Price"] <= price_range[1]) &
    (df["City"].isin(cities)) &
    (df["Beds"] >= min_beds) & 
    (df["Beds"] <= max_beds) &
    (df["Baths"] >= min_baths) & 
    (df["Baths"] <= max_baths) &
    (df["Square Feet"] >= sqft_range[0]) & 
    (df["Square Feet"] <= sqft_range[1])
]


#TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Visualizations", "Table View", "Maps", "City Comparisons"])

def format_city_names(cities):
    if not cities:
        return "All Cities"
    elif len(cities) == 1:
        return cities[0]
    elif len(cities) == 2:
        return f"{cities[0]} & {cities[1]}"
    else:
        return f"{', '.join(cities[:-1])} & {cities[-1]}"

# Generate dynamic city names
city_names = format_city_names(cities)

# Tab 1: Summary Statistics
with tab1:
    st.subheader(f"Summary Statistics for {city_names}:")
    
    if filtered_data.empty:
        st.write("No data available for the selected filters.")
    else:
        st.write(f"Average Price: ${filtered_data['Price'].mean():,.2f}")
        st.write(f"Average Square Footage: {filtered_data['Square Feet'].mean():,.0f}")
        st.write(f"Average Bedrooms: {filtered_data['Beds'].mean():.1f}")
        st.write(f"Average Bathrooms: {filtered_data['Baths'].mean():.1f}")

# Tab 2: Visualizations
with tab2:
    st.subheader(f"Visualizations for {city_names}:")

    if filtered_data.empty:
        st.write("No data available for the selected filters.")
    else:
        # Price Distribution (Histogram with Hover)
        st.write("### Price Distribution")
        fig = px.histogram(
            filtered_data,
            x="Price",
            nbins=20,
            title="Price Distribution",
            labels={"Price": "Price"},
            color_discrete_sequence=["skyblue"],
        )
        fig.update_traces(hovertemplate="Price: %{x}<br>Frequency: %{y}")
        st.plotly_chart(fig)

        st.markdown("---")

        # Scatter Plot (Interactive Hover)
        st.write("### Price vs Square Feet")
        fig = px.scatter(
            filtered_data,
            x="Square Feet",
            y="Price",
            title="Price vs Square Feet",
            labels={"Square Feet": "Square Feet", "Price": "Price"},
            hover_data=["Address", "Beds", "Baths"],  # Add extra hover information
        )
        st.plotly_chart(fig)

# Tab 3: Filtered Data
with tab3:
    st.subheader(f"Filtered Data for {city_names}:")
    
    if filtered_data.empty:
        st.write("No data available for the selected filters.")
    else:
        st.dataframe(filtered_data)
        st.download_button(
            label="Download Filtered Data",
            data=filtered_data.to_csv(index=False),
            file_name="filtered_housing_data.csv",
            mime="text/csv",
        )

with tab4:
    if "Latitude" in df.columns and "Longitude" in df.columns:
        st.write("### Properties on Map")

        # Add a column to indicate whether the property is in the selected city
        df["Selected"] = df["City"].isin(cities)  # Mark True if the property is in the selected city

        # Define color based on selection
        def get_color(selected):
            return [0, 255, 0, 160] if selected else [200, 30, 0, 160]  # Green for selected, Red for others

        df["Color"] = df["Selected"].apply(get_color)

        # Map layer with bigger dots
        map_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["Longitude", "Latitude"],
            get_radius=200,  # Increased radius for larger dots
            get_color="Color",  # Use the computed color
            pickable=True,
        )

        # View state centered around the data
        view_state = pdk.ViewState(
            latitude=df["Latitude"].mean(),
            longitude=df["Longitude"].mean(),
            zoom=10,
            pitch=0,  # Set pitch to 0 for a top-down view
        )

        # Custom legend as part of Pydeck
        legend_html = """
        <div style="position: absolute; z-index: 1; bottom: 20px; left: 20px; 
                    background-color: white; padding: 10px; border-radius: 5px; 
                    box-shadow: 0px 2px 4px rgba(0,0,0,0.3);">
            <h4 style="margin: 0; font-size: 14px;">Legend</h4>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 15px; height: 15px; background-color: rgb(0, 255, 0); margin-right: 5px;"></div>
                <span style="font-size: 12px;">Selected City</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 15px; height: 15px; background-color: rgb(200, 30, 0); margin-right: 5px;"></div>
                <span style="font-size: 12px;">Other Cities</span>
            </div>
        </div>
        """

        # Render the map
        r = pdk.Deck(
            layers=[map_layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>Price:</b> {Price}<br><b>Beds:</b> {Beds}<br><b>Baths:</b> {Baths}", "style": {"color": "white"}},
            map_style="mapbox://styles/mapbox/light-v10",
        )

        # Display the map and legend
        st.pydeck_chart(r)
        st.markdown(legend_html, unsafe_allow_html=True)    


    st.write("### Pricing Heatmap (All Cities)")
    fig = px.density_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        z="Price",
        radius=50,  # Adjust for density smoothing
        center=dict(lat=df["Latitude"].mean(), lon=df["Longitude"].mean()),
        zoom=10,
        mapbox_style="carto-positron",
    )

    # Display the Plotly map
    st.plotly_chart(fig)

with tab5:
    city_avg_price = df.groupby("City")["Price"].mean().sort_values(ascending=False).reset_index()

    # Create bar chart
    fig = px.bar(
        city_avg_price,
        x="City",
        y="Price",
        title="Average Home Price by City",
        labels={"Price": "Average Price ($)", "City": "City"},
        color="Price",  # Color by price for visual emphasis
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig)

    st.markdown("---")

    fig = px.scatter(
    df,
    x="Square Feet",
    y="Price",
    color="City",
    title="Price vs. Square Feet by City",
    labels={"Square Feet": "Square Feet", "Price": "Price ($)", "City": "City"},
    hover_data=["Address", "Beds", "Baths"],  # Add extra details on hover
    )
    st.plotly_chart(fig)

    st.markdown("---")

    filtered_df = df[(df["Square Feet"] < 8000) & (df["Price"] < 10000000)]

    # Create the scatter plot
    fig = px.scatter(
        filtered_df,
        x="Square Feet",
        y="Price",
        title="Price vs. Square Feet (No Outliers)",
        labels={"Square Feet": "Square Feet", "Price": "Price ($)", "City": "City"},
        hover_data=["Address", "Beds", "Baths"],
        trendline="ols"
    )

    # Customize the points to be light green
    fig.update_traces(marker=dict(color="lightblue"))
    for trace in fig.data:
        if trace.mode == "lines":  # Identify the trendline trace
            trace.line.color = "darkblue"

    # Display the plot in Streamlit
    st.plotly_chart(fig)

    st.markdown(" --- ")

    city_listings = df["City"].value_counts(normalize=True) * 100  # Calculate percentages
    city_listings = city_listings.reset_index()
    city_listings.columns = ["City", "Percentage"]

    # Aggregate cities under 3% as "Other"
    threshold = 2
    city_listings["City"] = city_listings["City"].where(city_listings["Percentage"] >= threshold, "Other")

    # Recalculate percentages after aggregation
    city_listings = city_listings.groupby("City", as_index=False).sum()

    # Create the pie chart
    fig = px.pie(
        city_listings,
        values="Percentage",
        names="City",
        title="Market Share of Listings by City",
        color="City",
        color_discrete_sequence=px.colors.qualitative.Set3,  # Vibrant color palette
        hole=0.4,  # Optional: Make it a donut chart
    )

    # Add hover data for better interactivity
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Percentage: %{value:.2f}%<extra></extra>",
        textinfo="label+percent",
    )

    # Display the chart
    st.plotly_chart(fig)

    



