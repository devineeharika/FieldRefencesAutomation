import requests
import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
import time
import pandas as pd
from selenium.webdriver.common.by import By
from multiprocessing import Pool, Manager
import constants
import csv
from tqdm import tqdm
import multiprocessing
from zeep import Client
from zeep.transports import Transport
from PIL import Image
import sys
import streamlit.web.cli as stcli
# Ensure that Streamlit runs your app

def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.getcwd(),path))
    return resolved_path

if __name__ == '__main__':
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("FieldReferences.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
