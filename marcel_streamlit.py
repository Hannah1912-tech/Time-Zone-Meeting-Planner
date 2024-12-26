import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import asyncio

# Ensure proper async context
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy') and isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Set page configuration
st.set_page_config(
    page_title="Time Zone Meeting Planner",
    page_icon="🌍",
    layout="wide"
)

# Load the countries data
@st.cache_data
def load_country_data():
    try:
        file_path = 'countries_data.csv'
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading countries data: {str(e)}")
        return pd.DataFrame()

countries_data = load_country_data()

def get_timezone(country_name):
    """
    Retrieve the timezone of a given country from the dataset.
    """
    country_data = countries_data[countries_data['name'].str.contains(country_name, case=False, na=False)]
    if country_data.empty:
        raise ValueError(f"Country '{country_name}' not found in the dataset.")
    
    # Extract the first timezone for the country
    timezone = eval(country_data.iloc[0]['timezones'])[0]
    
    # Comprehensive UTC to IANA timezone mapping
    utc_to_iana = {
        'UTC+00:00': 'UTC',
        'UTC+01:00': 'Europe/Paris',
        'UTC+02:00': 'Europe/Kiev',
        'UTC+03:00': 'Europe/Moscow',
        'UTC+04:00': 'Asia/Dubai',
        'UTC+05:00': 'Asia/Karachi',
        'UTC+05:30': 'Asia/Kolkata',
        'UTC+06:00': 'Asia/Dhaka',
        'UTC+07:00': 'Asia/Bangkok',
        'UTC+08:00': 'Asia/Shanghai',
        'UTC+09:00': 'Asia/Tokyo',
        'UTC+09:30': 'Australia/Darwin',
        'UTC+10:00': 'Australia/Sydney',
        'UTC+11:00': 'Pacific/Noumea',
        'UTC+12:00': 'Pacific/Auckland',
        'UTC-01:00': 'Atlantic/Azores',
        'UTC-02:00': 'America/Noronha',
        'UTC-03:00': 'America/Sao_Paulo',
        'UTC-04:00': 'America/New_York',
        'UTC-05:00': 'America/Chicago',
        'UTC-06:00': 'America/Denver',
        'UTC-07:00': 'America/Phoenix',
        'UTC-08:00': 'America/Los_Angeles',
        'UTC-09:00': 'America/Anchorage',
        'UTC-10:00': 'Pacific/Honolulu',
        'UTC-11:00': 'Pacific/Midway',
        'UTC-12:00': 'Pacific/Wake'
    }
    
    for utc_offset, iana_zone in utc_to_iana.items():
        if timezone.startswith(utc_offset):
            return iana_zone
    
    return timezone

def find_best_talk_time(country1, country2, wake_hours1, sleep_hours1, wake_hours2, sleep_hours2):
    """
    Find the best time to talk between two people in different countries.
    """
    timezone1 = pytz.timezone(get_timezone(country1))
    timezone2 = pytz.timezone(get_timezone(country2))
    
    # Define awake periods for both people
    now = datetime.now()
    
    # Person 1's wake time
    wake_start1 = timezone1.localize(now.replace(hour=wake_hours1[0], minute=0, second=0, microsecond=0))
    wake_end1 = timezone1.localize(now.replace(hour=wake_hours1[1], minute=0, second=0, microsecond=0))
    
    # Person 2's wake time
    wake_start2 = timezone2.localize(now.replace(hour=wake_hours2[0], minute=0, second=0, microsecond=0))
    wake_end2 = timezone2.localize(now.replace(hour=wake_hours2[1], minute=0, second=0, microsecond=0))
    
    # Convert all times to UTC for comparison
    wake_start1_utc = wake_start1.astimezone(pytz.UTC)
    wake_end1_utc = wake_end1.astimezone(pytz.UTC)
    wake_start2_utc = wake_start2.astimezone(pytz.UTC)
    wake_end2_utc = wake_end2.astimezone(pytz.UTC)
    
    # Calculate overlap in awake times
    overlap_start = max(wake_start1_utc, wake_start2_utc)
    overlap_end = min(wake_end1_utc, wake_end2_utc)
    
    if overlap_start < overlap_end:
        # Convert overlap times back to each person's local time
        overlap_start_local1 = overlap_start.astimezone(timezone1)
        overlap_end_local1 = overlap_end.astimezone(timezone1)
        overlap_start_local2 = overlap_start.astimezone(timezone2)
        overlap_end_local2 = overlap_end.astimezone(timezone2)
        
        return {
            'status': 'success',
            'country1_time': f"{overlap_start_local1.strftime('%H:%M')} to {overlap_end_local1.strftime('%H:%M')}",
            'country2_time': f"{overlap_start_local2.strftime('%H:%M')} to {overlap_end_local2.strftime('%H:%M')}",
            'utc_time': f"{overlap_start.strftime('%H:%M')} to {overlap_end.strftime('%H:%M')}"
        }
    else:
        return {
            'status': 'error',
            'message': "There's no common awake time today. Consider adjusting schedules."
        }

def main():
    st.title("🌍 Time Zone Meeting Planner")
    st.write("Find the best time to talk with someone in a different time zone!")

    # Get list of countries
    country_list = sorted(countries_data['name'].tolist())

    # Create two columns for the form
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Person 1")
        country1 = st.selectbox("Select your country", country_list, key="country1")
        wake_hour1 = st.number_input("Wake hour (0-23)", 0, 23, 7, key="wake1")
        sleep_hour1 = st.number_input("Sleep hour (0-23)", 0, 23, 23, key="sleep1")

    with col2:
        st.subheader("Person 2")
        country2 = st.selectbox("Select your country", country_list, key="country2")
        wake_hour2 = st.number_input("Wake hour (0-23)", 0, 23, 7, key="wake2")
        sleep_hour2 = st.number_input("Sleep hour (0-23)", 0, 23, 23, key="sleep2")

    if st.button("Find Best Time"):
        try:
            result = find_best_talk_time(
                country1=country1, 
                country2=country2,
                wake_hours1=(wake_hour1, sleep_hour1),
                sleep_hours1=(wake_hour1, sleep_hour1),
                wake_hours2=(wake_hour2, sleep_hour2),
                sleep_hours2=(wake_hour2, sleep_hour2)
            )
            
            if result['status'] == 'success':
                st.success("Found overlapping time!")
                
                # Create three columns for the results
                res_col1, res_col2, res_col3 = st.columns(3)
                
                with res_col1:
                    st.metric(f"Time in {country1}", result['country1_time'])
                
                with res_col2:
                    st.metric(f"Time in {country2}", result['country2_time'])
                
                with res_col3:
                    st.metric("Time in UTC", result['utc_time'])
                    
            else:
                st.error(result['message'])
                
        except ValueError as e:
            st.error(f"Error: {str(e)}")

    # Add footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit")

if __name__ == "__main__":
    main() 