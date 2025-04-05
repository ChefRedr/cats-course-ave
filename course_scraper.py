import os
import re
import json
import time
import tempfile
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = "https://catalogs.northwestern.edu"
CATALOG_URLS = [
    f"{BASE}/undergraduate/courses-az/",
    f"{BASE}/tgs/courses-az/"
]

# Create a temp directory for a clean Chrome profile
user_data_dir = tempfile.mkdtemp()

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--remote-debugging-port=9222")

# Start Chrome driver
driver = webdriver.Chrome(options=options)

def get_subject_links(catalog_url):
    driver.get(catalog_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = soup.select("div.az_sitemap a[href]")
    return [BASE + link["href"] for link in links if "/courses-az/" in link["href"]]

def extract_courses_from_subject(url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    subject_code = url.rstrip('/').split('/')[-1].upper()
    course_blocks = soup.select("div.courseblock")

    courses = []
    for block in course_blocks:
        # Grab the course title from ANY <strong> tag
        title_el = block.select_one("strong")
        # Handle both <span> and <p> for course descriptions
        desc_el = block.select_one("span.courseblockdesc, p.courseblockdesc")

        if not title_el:
            continue

        title_text = title_el.get_text(strip=True)

        # Match e.g. "AFST 390-SA Course Title (1 Unit)"
        match = re.match(r"([A-Z_]+)\s+(\d{3}(?:-[A-Z0-9]+)?)\s+(.+?)\s+\((\d+)\s+Unit", title_text)
        if not match:
            continue

        subject, catalog_number, course_name, units = match.groups()
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        prereqs = re.findall(r"[A-Z_]+\s\d{3}-\d*", description)

        courses.append({
            "subject": subject,
            "catalog_number": catalog_number,
            "course_name": course_name,
            "description": description,
            "units": int(units),
            "prereqs": prereqs
        })
    return subject_code, courses

# Scrape all subjects and courses
all_courses = {}

for catalog_url in CATALOG_URLS:
    print(f"Scraping catalog: {catalog_url}")
    subject_links = get_subject_links(catalog_url)

    for link in subject_links:
        try:
            time.sleep(0.5)
            subject, courses = extract_courses_from_subject(link)
            if courses:
                all_courses.setdefault(subject, []).extend(courses)
                print(f"✓ {subject}: {len(courses)} courses")
        except Exception as e:
            print(f"Error scraping {link}: {e}")

driver.quit()

# Save to JSON
with open("northwestern_courses.json", "w") as f:
    json.dump(all_courses, f, indent=2)

print("Done! Saved to northwestern_courses.json")