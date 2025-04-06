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

user_data_dir = tempfile.mkdtemp()

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--remote-debugging-port=9222")

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
        title_el = block.select_one("strong")
        desc_el = block.select_one("span.courseblockdesc, p.courseblockdesc")
        
        if not title_el:
            continue

        title_text = title_el.get_text(strip=True)
        match = re.match(r"([A-Z_]+)\s+(\d{3}(?:-[A-Z0-9]+)?)\s+(.+?)\s+\((\d+)\s+Unit", title_text)
        if not match:
            continue

        subject, catalog_number, course_name, units = match.groups()
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        
        prereq_text = extract_prerequisite_text(block, description)

        # Normalize all whitespace in fields
        courses.append({
            "subject": subject,
            "catalog_number": catalog_number,
            "course_name": ' '.join(course_name.split()),
            "description": ' '.join(description.strip().split()),
            "units": int(units),
            "prereqs": ' '.join(prereq_text.split())
        })
    
    return subject_code, courses

def extract_prerequisite_text(course_block, description):
    for extra in course_block.select(".courseblockextra"):
        text = extra.get_text(" ", strip=True)
        if text.lower().startswith("prerequisite:") or text.lower().startswith("prerequisites:"):
            return text

    for p in course_block.select("p"):
        if p.get_text(" ", strip=True).lower().startswith("prerequisite") and p != course_block.select_one("p.courseblockdesc"):
            return p.get_text(" ", strip=True)
    
    prereq_patterns = [
        r"(Prerequisite[s]?:?\s+[^\.]+\.)",
        r"(Prerequisites?[^\.]+include[s]?:?\s+[^\.]+\.)"
    ]
    
    for pattern in prereq_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)
    
    if "Prerequisites:" in description or "Prerequisite:" in description:
        lines = description.split('.')
        for line in lines:
            if "Prerequisite" in line:
                return line.strip() + "."

    return ""

# Scrape all subjects and courses
all_courses = {}

for catalog_url in CATALOG_URLS:
    print(f"Scraping catalog: {catalog_url}")
    subject_links = get_subject_links(catalog_url)

    for link in subject_links:
        try:
            time.sleep(1)
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

