import frappe
import datetime
from croniter import croniter
import re
from salla_common_lib import utils as salla_utils

# Re-export whitelisted methods from salla_common_lib
@frappe.whitelist()
def update_product_balance_warehouse(merchant_name=None, item=None, is_bulk=False):
    return salla_utils.update_product_balance_warehouse(merchant_name, item, is_bulk)

@frappe.whitelist()
def update_variant_qty(item_variant, merchant_name, salla_item_info_name):
    return salla_utils.update_variant_qty(item_variant, merchant_name, salla_item_info_name)

def serialize_dates(obj):
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(i) for i in obj]
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, frappe.model.document.Document):
        return obj.name
    else:
        return obj

@frappe.whitelist()
def test_cron_format(cron_format):
    """
    Test a cron format and return next execution times
    """
    try:
        validate_cron_format(cron_format)

        # If croniter is available, show next few execution times
        try:
            from datetime import datetime

            cron = croniter(cron_format, datetime.now())
            next_runs = []
            for _ in range(5):  # Show next 5 execution times
                next_runs.append(cron.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S"))

            return {
                "valid": True,
                "message": "Cron format is valid",
                "next_executions": next_runs,
            }
        except ImportError:
            return {
                "valid": True,
                "message": "Cron format is valid (basic validation only)",
            }

    except Exception as e:
        return {"valid": False, "message": str(e)}

def validate_cron_format(cron_format):
    """
    Validate cron format using multiple methods
    """
    if not cron_format or not isinstance(cron_format, str):
        frappe.throw("Cron format cannot be empty and must be a string")

    cron_format = cron_format.strip()

    # Method 1: Basic regex validation for cron format
    # Standard cron: 5 fields (minute hour day month weekday)
    # Extended cron: 6 fields (second minute hour day month weekday) - some systems support this
    cron_regex = r"^(\*|[0-5]?\d|\*/\d+|\d+-\d+|\d+(,\d+)*)\s+(\*|\d{1,2}|\*/\d+|\d+-\d+|\d+(,\d+)*)\s+(\*|\d{1,2}|\*/\d+|\d+-\d+|\d+(,\d+)*)\s+(\*|\d{1,2}|\*/\d+|\d+-\d+|\d+(,\d+)*)\s+(\*|[0-7]|\*/\d+|\d+-\d+|\d+(,\d+)*)$"

    if not re.match(cron_regex, cron_format):
        frappe.throw(
            f"Invalid cron format: {cron_format}. Expected format: 'minute hour day month weekday'"
        )

    # Method 2: Use croniter library for more robust validation (if available)
    try:
        # Test if the cron expression is valid by creating a croniter object
        if not croniter.is_valid(cron_format):
            frappe.throw(f"Invalid cron expression: {cron_format}")
    except ImportError:
        # croniter not available, rely on regex validation
        frappe.log_error("croniter library not available, using basic regex validation")
    except Exception as e:
        frappe.throw(f"Invalid cron format: {cron_format}. Error: {str(e)}")

    # Method 3: Additional field-specific validation
    fields = cron_format.split()
    if len(fields) != 5:
        frappe.throw(f"Cron format must have exactly 5 fields, got {len(fields)}")

    # Validate individual fields
    field_names = ["minute", "hour", "day", "month", "weekday"]
    field_ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]

    for i, (field, field_range) in enumerate(zip(fields, field_ranges)):
        validate_cron_field(field, field_names[i], field_range)

def validate_cron_field(field, field_name, valid_range):
    """
    Validate individual cron field
    """
    if field == "*":
        return True

    # Handle step values (*/n)
    if field.startswith("*/"):
        try:
            step = int(field[2:])
            if step <= 0:
                frappe.throw(f"Invalid step value in {field_name}: {field}")
            return True
        except ValueError:
            frappe.throw(f"Invalid step format in {field_name}: {field}")

    # Handle ranges (n-m)
    if "-" in field and not field.startswith("-"):
        try:
            start, end = map(int, field.split("-"))
            if start < valid_range[0] or end > valid_range[1] or start > end:
                frappe.throw(f"Invalid range in {field_name}: {field}")
            return True
        except ValueError:
            frappe.throw(f"Invalid range format in {field_name}: {field}")

    # Handle comma-separated values (n,m,o)
    if "," in field:
        try:
            values = [int(x.strip()) for x in field.split(",")]
            for val in values:
                if val < valid_range[0] or val > valid_range[1]:
                    frappe.throw(f"Value {val} out of range for {field_name}: {field}")
            return True
        except ValueError:
            frappe.throw(f"Invalid comma-separated format in {field_name}: {field}")

    # Handle single numeric value
    try:
        val = int(field)
        if val < valid_range[0] or val > valid_range[1]:
            frappe.throw(
                f"Value {val} out of range for {field_name} (valid range: {valid_range[0]}-{valid_range[1]})"
            )
        return True
    except ValueError:
        frappe.throw(f"Invalid format in {field_name}: {field}")
