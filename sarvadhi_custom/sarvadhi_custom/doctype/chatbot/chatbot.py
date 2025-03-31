# Copyright (c) 2025, sarvadhi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class chatbot(Document):
	pass

@frappe.whitelist(allow_guest=True)
def check_doctype(doctype_name):
	if frappe.db.exists('DocType', doctype_name):
		return True
	else:
		return False
