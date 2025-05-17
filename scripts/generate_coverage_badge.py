import xml.etree.ElementTree as ET
import json

COVERAGE_XML = "coverage.xml"
BADGE_JSON = "coverage-badge.json"

def main():
    tree = ET.parse(COVERAGE_XML)
    root = tree.getroot()
    line_rate = float(root.attrib.get("line-rate", 0))
    percent = int(round(line_rate * 100))
    badge = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{percent}%25",
        "color": "brightgreen"
    }
    with open(BADGE_JSON, "w") as f:
        json.dump(badge, f)

if __name__ == "__main__":
    main() 