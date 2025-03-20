# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd
from requests.utils import quote

# Streamlit App Title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your smoothie will be:', name_on_order)

# Snowflake Connection
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch available fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).to_pandas()

# Ensure columns exist
if 'FRUIT_NAME' in my_dataframe.columns and 'SEARCH_ON' in my_dataframe.columns:
    fruit_options = my_dataframe['FRUIT_NAME'].tolist()
else:
    fruit_options = []

# Multi-select for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ', '.join(ingredients_list)  # Safe formatting

    for fruit_chosen in ingredients_list:
        # Get the corresponding "SEARCH_ON" value
        search_on_values = my_dataframe.loc[my_dataframe['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].values
        search_on = search_on_values[0] if len(search_on_values) > 0 else fruit_chosen  # Default if not found

        st.subheader(fruit_chosen + ' Nutrition Information')

        # Encode `search_on` for API request
        encoded_search_on = quote(search_on)

        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{encoded_search_on}")
            if fruityvice_response.status_code == 200:
                st.dataframe(data=fruityvice_response.json(), use_container_width=True)
            else:
                st.warning(f"No data found for {fruit_chosen}.")
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")

    # Button to Submit Order
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        try:
            session.sql("INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)", 
                        [ingredients_string, name_on_order]).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Error placing order: {e}")
