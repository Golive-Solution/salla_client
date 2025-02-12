// Copyright (c) 2023, Golive Solutions and contributors
// For license information, please see license.txt

frappe.listview_settings["Salla Order"] = {
  get_indicator: function (doc) {
    if (doc.status === "Queued") {
      return [__("Queued"), "blue", "status,=,Queued"];
    } else if (doc.status === "Failed") {
      return [__("Failed"), "orange", "status,=,Failed"];
    }
  },
};
