# apps/salla_client/salla_client/install.py

import os
import shutil

import frappe
import salla_common

def after_install():
    """
    Copy JS files from salla_common to salla_client:
    1) find salla_common/public/js
    2) ensure salla_client/public/js exists
    3) copy any missing .js files
    """
    # 1) Locate salla_common/public/js using salla_common.__file__
    src_pkg_root = os.path.dirname(salla_common.__file__)
    source_dir = os.path.join(src_pkg_root, "public", "js")

    if not os.path.isdir(source_dir):
        frappe.log(f"[salla_client] Source directory not found: {source_dir}", level="warning")
        return

    # 2) Ensure salla_client/public/js exists
    dest_dir = frappe.get_app_path("salla_client", "public", "js")
    os.makedirs(dest_dir, exist_ok=True)

    # 3) List of expected JS files to copy
    expected_files = [
        "salla_order.js",
        "salla_order_fulfilment.js",            
        "salla_shipment_method_mapping.js",
        "item.js"
    ]

    # 4) Copy missing or changed JS files
    for js_file in expected_files:
        src_file = os.path.join(source_dir, js_file)
        dst_file = os.path.join(dest_dir, js_file)

        if not os.path.isfile(src_file):
            frappe.log(f"[salla_client] Missing in salla_common: {js_file}", level="warning")
            continue

        # Only copy if destination is missing or contents differ
        if not os.path.isfile(dst_file) or not files_are_same(src_file, dst_file):
            try:
                shutil.copy2(src_file, dst_file)
                frappe.log(f"[salla_client] Copied {js_file} → salla_client/public/js/")
            except Exception as e:
                frappe.log_error(
                    title="[salla_client] Failed to copy JS",
                    message=f"Could not copy {src_file}:\n{str(e)}"
                )

def files_are_same(file1, file2):
    """Return True if both files exist and have identical content."""
    if not (os.path.isfile(file1) and os.path.isfile(file2)):
        return False

    if os.path.getsize(file1) != os.path.getsize(file2):
        return False

    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        return f1.read() == f2.read()
