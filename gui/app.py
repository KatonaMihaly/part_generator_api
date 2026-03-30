import os

import requests
import streamlit as st
from dotenv import load_dotenv

from part_generator_api.models.requests import ISO_4762_DIAMETERS

load_dotenv()

API_URL = os.getenv("API_URL")


def generate(endpoint, payload, filename, key):
    """
    Handles API request and session state.
    """
    with st.spinner("Generating..."):
        try:
            response = requests.post(f"{API_URL}{endpoint}", json=payload)
            if response.status_code == 200:
                st.session_state[f"{key}_data"] = response.content
                st.session_state[f"{key}_filename"] = filename
                st.session_state[f"{key}_generated"] = True
            else:
                st.error(f"Error {response.status_code}: {response.text}")
                st.session_state[f"{key}_data"] = None
                st.session_state[f"{key}_generated"] = False
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the server is running.")
            st.session_state[f"{key}_data"] = None
            st.session_state[f"{key}_generated"] = False


def download_section(key):
    """
    Also feedback on generation.
    """
    if st.session_state.get(f"{key}_generated"):
        st.success(f"Generated: {st.session_state[f'{key}_filename']}")
    if st.session_state.get(f"{key}_data"):
        st.download_button(
            "Download STEP",
            data=st.session_state[f"{key}_data"],
            file_name=st.session_state[f"{key}_filename"],
            mime="application/octet-stream",
        )

# --- LAYOUT ---
st.title("Part Generator")

tab_screw, tab_washer = st.tabs(["Screw", "Washer"])

with tab_screw:
    st.header("Screw")
    diameter = st.selectbox("Diameter (mm)", ISO_4762_DIAMETERS)
    length = st.number_input("Length (mm)")

    if st.button("Generate Screw"):
        st.session_state[f"screw_generated"] = False
        generate(
            endpoint="/v1/generate/screw",
            payload={"diameter": diameter, "length": length},
            filename=f"screw_M{diameter:g}x{length:g}.step",
            key="screw",
        )
    download_section("screw")

with tab_washer:
    st.header("Flat Washer")
    inner_diameter = st.number_input("Inner Diameter (mm)")
    outer_diameter = st.number_input("Outer Diameter (mm)")
    thickness = st.number_input("Thickness (mm)")

    if st.button("Generate Washer"):
        st.session_state[f"washer_generated"] = False
        generate(
            endpoint="/v1/generate/washer",
            payload={
                "inner_diameter": inner_diameter,
                "outer_diameter": outer_diameter,
                "thickness": thickness,
            },
            filename=f"washer_{inner_diameter:g}x{outer_diameter:g}x{thickness:g}.step",
            key="washer",
        )
    download_section("washer")
