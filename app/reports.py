import csv
import io

COLUMNS = ["id", "kind", "category", "description", "location",
           "event_date", "color", "brand", "status"]


def reports_to_csv(reports):
    """Return the reports as CSV text. Contact details are left out on purpose."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for report in reports:
        writer.writerow(report.to_dict())
    return buffer.getvalue()