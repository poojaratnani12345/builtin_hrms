# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json
from math import ceil

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, nowdate

import erpnext


def reordr_item():
	"""Reorder item if stock reaches reorder level"""
	# if initial setup not completed, return
	print("\nreorder calling")
	if not (frappe.db.a_row_exists("Company") and frappe.db.a_row_exists("Fiscal Year")):
		return

	if cint(frappe.db.get_value("Stock Settings", None, "auto_indent")):
		return _reordr_item()


def _reordr_item():
	print("\nreorder_item clling")
	material_requests = {"Purchase": {}, "Transfer": {}, "Material Issue": {}, "Manufacture": {}}
	warehouse_company = frappe._dict(
		frappe.db.sql(
			"""select name, company from `tabWarehouse`
		where disabled=0"""
		)
	)
	default_company = (
		erpnext.get_default_company() or frappe.db.sql("""select name from tabCompany limit 1""")[0][0]
	)

	items_to_consider = get_items_for_reorder()

	if not items_to_consider:
		return

	item_warehouse_projected_qty = get_item_warehouse_project_qty(items_to_consider)
	print("\n item wrehouse projectd qty :::",item_warehouse_projected_qty)

	def add_to_material_request(**kwargs):
		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		if kwargs.warehouse not in warehouse_company:
			# a disabled warehouse
			return

		reorder_level = flt(kwargs.reorder_level)
		reorder_qty = flt(kwargs.reorder_qty)

		# projected_qty will be 0 if Bin does not exist
		if kwargs.warehouse_group:
			projected_qty = flt(
				item_warehouse_projected_qty.get(kwargs.item_code, {}).get(kwargs.warehouse_group)
			)
		else:
			projected_qty = flt(item_warehouse_projected_qty.get(kwargs.item_code, {}).get(kwargs.warehouse))

		if (reorder_level or reorder_qty) and projected_qty <= reorder_level:
			deficiency = reorder_level - projected_qty
			if deficiency > reorder_qty:
				reorder_qty = deficiency

			company = warehouse_company.get(kwargs.warehouse) or default_company

			material_requests[kwargs.material_request_type].setdefault(company, []).append(
				{
					"item_code": kwargs.item_code,
					"warehouse": kwargs.warehouse,
					"reorder_qty": reorder_qty,
					"item_details": kwargs.item_details,
				}
			)

	for item_code, reorder_levels in items_to_consider.items():
		for d in reorder_levels:
			if d.has_variants:
				continue

			add_to_material_request(
				item_code=item_code,
				warehouse=d.warehouse,
				reorder_level=d.warehouse_reorder_level,
				reorder_qty=d.warehouse_reorder_qty,
				material_request_type=d.material_request_type,
				warehouse_group=d.warehouse_group,
				item_details=frappe._dict(
					{
						"item_code": item_code,
						"name": item_code,
						"item_name": d.item_name,
						"item_group": d.item_group,
						"brand": d.brand,
						"description": d.description,
						"stock_uom": d.stock_uom,
						"purchase_uom": d.purchase_uom,
						"lead_time_days": d.lead_time_days,
					}
				),
			)

	if material_requests:
		return create_material_req(material_requests)


def get_items_for_reorder() -> dict[str, list]:
	print("\nget item for reorder calling:")

	reorder_table = frappe.qb.DocType("Item Reorder")
	item_table = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(reorder_table)
		.inner_join(item_table)
		.on(reorder_table.parent == item_table.name)
		.select(
			reorder_table.warehouse,
			reorder_table.warehouse_group,
			reorder_table.material_request_type,
			reorder_table.warehouse_reorder_level,
			reorder_table.warehouse_reorder_qty,
			item_table.name,
			item_table.stock_uom,
			item_table.purchase_uom,
			item_table.description,
			item_table.item_name,
			item_table.item_group,
			item_table.brand,
			item_table.variant_of,
			item_table.has_variants,
			item_table.lead_time_days,
		)
		.where(
			(item_table.disabled == 0)
			& (item_table.is_stock_item == 1)
			& (
				(item_table.end_of_life.isnull())
				| (item_table.end_of_life > nowdate())
				| (item_table.end_of_life == "0000-00-00")
			)
		)
	)

	data = query.run(as_dict=True)
	itemwise_reorder = frappe._dict({})
	for d in data:
		itemwise_reorder.setdefault(d.name, []).append(d)

	itemwise_reorder = get_reorder_levels_variants(itemwise_reorder)

	return itemwise_reorder


def get_reorder_levels_variants(itemwise_reorder):
	print("get reorder level for varient calling")

	item_table = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(item_table)
		.select(
			item_table.name,
			item_table.variant_of,
		)
		.where(
			(item_table.disabled == 0)
			& (item_table.is_stock_item == 1)
			& (
				(item_table.end_of_life.isnull())
				| (item_table.end_of_life > nowdate())
				| (item_table.end_of_life == "0000-00-00")
			)
			& (item_table.variant_of.notnull())
		)
	)

	variants_item = query.run(as_dict=True)
	for row in variants_item:
		if not itemwise_reorder.get(row.name) and itemwise_reorder.get(row.variant_of):
			itemwise_reorder.setdefault(row.name, []).extend(itemwise_reorder.get(row.variant_of, []))

	return itemwise_reorder


def get_item_warehouse_project_qty(items_to_consider):
	print("\nget item warehouse project qty callinggg \n")

	item_warehouse_projected_qty = {}
	items_to_consider = list(items_to_consider.keys())

	for item_code, warehouse, projected_qty in frappe.db.sql(
		"""select item_code, warehouse, projected_qty
		from tabBin where item_code in ({})
			and (warehouse != '' and warehouse is not null)""".format(
			", ".join(["%s"] * len(items_to_consider))
		),
		items_to_consider,
	):
		if item_code not in item_warehouse_projected_qty:
			item_warehouse_projected_qty.setdefault(item_code, {})

		if warehouse not in item_warehouse_projected_qty.get(item_code):
			item_warehouse_projected_qty[item_code][warehouse] = flt(projected_qty)

		warehouse_doc = frappe.get_doc("Warehouse", warehouse)

		while warehouse_doc.parent_warehouse:
			if not item_warehouse_projected_qty.get(item_code, {}).get(warehouse_doc.parent_warehouse):
				item_warehouse_projected_qty.setdefault(item_code, {})[warehouse_doc.parent_warehouse] = flt(
					projected_qty
				)
			else:
				item_warehouse_projected_qty[item_code][warehouse_doc.parent_warehouse] += flt(projected_qty)
			warehouse_doc = frappe.get_doc("Warehouse", warehouse_doc.parent_warehouse)

	return item_warehouse_projected_qty


def create_material_req(material_requests):
    print("Create material request: callinggg")
    mr_list = []
    exceptions_list = []

    def _log_exception(mr):
        if frappe.local.message_log:
            exceptions_list.extend(frappe.local.message_log)
            frappe.local.message_log = []
        else:
            exceptions_list.append(frappe.get_traceback(with_context=True))
        if mr:
            mr.log_error("Unable to create material request")

    company_wise_mr = frappe._dict({})
    print("Company wise mr:", company_wise_mr)
    print("Material requests:", material_requests)

    if not any(material_requests.values()):
        print("No material requests to process. Creating default material request.")
        default_items = [
            {
                "item_code": "plastic",
                "reorder_qty": 500,
                "warehouse": "Stores - SD",
                "item_details": {
                    "stock_uom": "Nos",
                    "purchase_uom": "Nos",
                    "lead_time_days": 5,
                    "item_name": "plastic",
                }
            }
        ]
        material_requests["Purchase"] = {"sarvadhi (Demo)": default_items}

    for request_type in material_requests:
        print("Request type:", request_type)
        for company in material_requests[request_type]:
            try:
                items = material_requests[request_type][company]
                print("\nItems:", items)
                if not items:
                    continue

                mr = frappe.new_doc("Material Request")
                mr.update({
                    "company": company,
                    "transaction_date": nowdate(),
                    "material_request_type": "Material Transfer" if request_type == "Transfer" else request_type,
                })
                print("\nMaterial request:", mr)

                for d in items:
                    d = frappe._dict(d)
                    item = d.get("item_details", {})
                    print("\nItem:", item)
                    uom = item.get("stock_uom")
                    lead_time_days = item.get("lead_time_days", 0)
                    qty = d.reorder_qty  # Ensure this is defined

                    
                    print("Before append")
                    mr.append(
                        "items",
                        {
                            "doctype": "Material Request Item",
                            "item_code": d.item_code,
                            "schedule_date": add_days(nowdate(), cint(lead_time_days)),
                            "qty": qty,
                            "uom": uom,
                            "warehouse": d.warehouse,
                            "item_name": item.get("item_name"),
                        },
                    )
                    print("\nAppended items:", mr.items)
				# 	# Retry logic for insert
                # if not insert_material_request(mr):
                #     print(f"Failed to insert material request for {company} after multiple attempts.")
                    
                print("mrrrrr:",mr)
                schedule_dates = [d.schedule_date for d in mr.items]
                print("scedul date:",schedule_dates)
                mr.schedule_date = max(schedule_dates or [nowdate()])
                print(" mr.schedule_date:", mr.schedule_date)
                mr.flags.ignore_mandatory = True
                # mr.refresh()
                # print("refresh")
                for attempt in range(3):
                    try:
                        print("try block")
                        mr.insert()
                        print("Material Request inserted successfully.")
                        # PurchaseOrder()

                        break  # Exit loop if successful
                    except frappe.exceptions.ValidationError as e:
                        print(f"Validation error on attempt {attempt + 1}: {e}")
                        _log_exception(mr)
                        break  # Exit on validation error
                    except Exception as e:
                        if "Record has changed since last read" in str(e):
                            print(f"Error during insert on attempt {attempt + 1}: {e}")
                            if attempt < 3 - 1:  # Only refresh if it's not the last attempt
                                mr = frappe.get_doc("Material Request", mr.name)  # Refresh
                                continue  # Retry the insert
                        _log_exception(mr)
                        print(f"Error in processing request for {company}: {e}")
                        break  # Exit the loop if final attempt fails

                print("after insert")
                create_purchase_order(mr)
                mr.submit()
                mr_list.append(mr)

                company_wise_mr.setdefault(company, []).append(mr)

            except Exception as e:
                _log_exception(mr)
                print(f"Error in processing request for {company}: {e}")

    if company_wise_mr:
        if getattr(frappe.local, "reorder_email_notify", None) is None:
            frappe.local.reorder_email_notify = cint(frappe.db.get_value("Stock Settings", None, "reorder_email_notify"))
        if frappe.local.reorder_email_notify:
            send_email_notification(company_wise_mr)

    if exceptions_list:
        notify_errors(exceptions_list)

    return mr_list




# def create_material_req(material_requests):
# 	print("Create material request: callinggg")

# 	"""Create indent on reaching reorder level"""
# 	mr_list = []
# 	exceptions_list = []

# 	def _log_exception(mr):
# 		if frappe.local.message_log:
# 			exceptions_list.extend(frappe.local.message_log)
# 			frappe.local.message_log = []
# 		else:
# 			exceptions_list.append(frappe.get_traceback(with_context=True))

# 		mr.log_error("Unable to create material request")

# 	company_wise_mr = frappe._dict({})
# 	print("Company wise mr:", company_wise_mr)
# 	print("Material requests:", material_requests)

    

	# for request_type in material_requests:
	# 	for company in material_requests[request_type]:
	# 		try:
	# 			items = material_requests[request_type][company]
	# 			if not items:
	# 				continue

	# 			mr = frappe.new_doc("Material Request")
	# 			mr.update(
	# 				{
	# 					"company": company,
	# 					"transaction_date": nowdate(),
	# 					"material_request_type": "Material Transfer"
	# 					if request_type == "Transfer"
	# 					else request_type,
	# 				}
	# 			)

	# 			for d in items:
	# 				d = frappe._dict(d)
	# 				item = d.get("item_details")
	# 				uom = item.stock_uom
	# 				conversion_factor = 1.0

	# 				if request_type == "Purchase":
	# 					uom = item.purchase_uom or item.stock_uom
	# 					if uom != item.stock_uom:
	# 						conversion_factor = (
	# 							frappe.db.get_value(
	# 								"UOM Conversion Detail",
	# 								{"parent": item.name, "uom": uom},
	# 								"conversion_factor",
	# 							)
	# 							or 1.0
	# 						)

	# 				must_be_whole_number = frappe.db.get_value("UOM", uom, "must_be_whole_number", cache=True)
	# 				qty = d.reorder_qty / conversion_factor
	# 				if must_be_whole_number:
	# 					qty = ceil(qty)

	# 				mr.append(
	# 					"items",
	# 					{
	# 						"doctype": "Material Request Item",
	# 						"item_code": d.item_code,
	# 						"schedule_date": add_days(nowdate(), cint(item.lead_time_days)),
	# 						"qty": qty,
	# 						"conversion_factor": conversion_factor,
	# 						"uom": uom,
	# 						"stock_uom": item.stock_uom,
	# 						"warehouse": d.warehouse,
	# 						"item_name": item.item_name,
	# 						"description": item.description,
	# 						"item_group": item.item_group,
	# 						"brand": item.brand,
	# 					},
	# 				)

	# 			schedule_dates = [d.schedule_date for d in mr.items]
	# 			mr.schedule_date = max(schedule_dates or [nowdate()])
	# 			mr.flags.ignore_mandatory = True
	# 			mr.insert()
	# 			mr.submit()
	# 			mr_list.append(mr)

	# 			company_wise_mr.setdefault(company, []).append(mr)

	# 		except Exception:
	# 			_log_exception(mr)

	# if company_wise_mr:
	# 	if getattr(frappe.local, "reorder_email_notify", None) is None:
	# 		frappe.local.reorder_email_notify = cint(
	# 			frappe.db.get_value("Stock Settings", None, "reorder_email_notify")
	# 		)

	# 	if frappe.local.reorder_email_notify:
	# 		send_email_notification(company_wise_mr)

	# if exceptions_list:
	# 	notify_errors(exceptions_list)

	# return mr_list




def create_purchase_order(mr):
    print(f"Creating Purchase Order for Material Request: {mr.name}")

    try:
        po = frappe.new_doc("Purchase Order")
        print("\n po:",po)
        po.supplier = "Shruti galaxy Pvt Ltd."  # You can modify this to fetch actual supplier
        print("\n po.supplier:",po.supplier)
        po.company = mr.company
        po.transaction_date = nowdate()

        for item in mr.items:
            po.append(
                "items",
                {
                    "item_code": item.item_code,
                    "schedule_date": item.schedule_date,
                    "qty": item.qty,
                    "uom": item.uom,
                    "warehouse": item.warehouse,
                    "material_request": mr.name,
                    "material_request_item": item.name
                }
            )

        po.flags.ignore_mandatory = True
        po.insert()
        po.submit()
        print(f"Purchase Order {po.name} created successfully!")
        create_purchase_receipt(po)

        return po.name
    except Exception as e:
        print(f"Error while creating Purchase Order: {e}")






def create_purchase_receipt(po):
    print(f"Creating Purchase Receipt for Purchase Order: {po.name}")

    try:
        pr = frappe.new_doc("Purchase Receipt")
        print("\n pr:",pr)
        pr.supplier = po.supplier
        pr.company = po.company
        pr.posting_date = nowdate()

        for item in po.items:
            pr.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "received_qty": item.qty,
                    "uom": item.uom,
                    "warehouse": item.warehouse,
                    "purchase_order": po.name,
                    "purchase_order_item": item.name
                }
            )

        pr.flags.ignore_mandatory = True
        pr.insert()
        pr.submit()
        print(f"Purchase Receipt {pr.name} created successfully!")

        return pr.name
    except Exception as e:
        print(f"Error while creating Purchase Receipt: {e}")





def send_email_notification(company_wise_mr):
	"""Notify user about auto creation of indent"""

	for company, mr_list in company_wise_mr.items():
		email_list = get_email_list(company)

		if not email_list:
			continue

		msg = frappe.render_template("templates/emails/reorder_item.html", {"mr_list": mr_list})

		frappe.sendmail(recipients=email_list, subject=_("Auto Material Requests Generated"), message=msg)


def get_email_list(company):
	users = get_comapny_wise_users(company)
	user_table = frappe.qb.DocType("User")
	role_table = frappe.qb.DocType("Has Role")

	query = (
		frappe.qb.from_(user_table)
		.inner_join(role_table)
		.on(user_table.name == role_table.parent)
		.select(user_table.email)
		.where(
			(role_table.role.isin(["Purchase Manager", "Stock Manager"]))
			& (user_table.name.notin(["Administrator", "All", "Guest"]))
			& (user_table.enabled == 1)
			& (user_table.docstatus < 2)
		)
	)

	if users:
		query = query.where(user_table.name.isin(users))

	emails = query.run(as_dict=True)

	return list(set([email.email for email in emails]))


def get_comapny_wise_users(company):
	companies = [company]

	if parent_company := frappe.db.get_value("Company", company, "parent_company"):
		companies.append(parent_company)

	users = frappe.get_all(
		"User Permission",
		filters={"allow": "Company", "for_value": ("in", companies), "apply_to_all_doctypes": 1},
		fields=["user"],
	)

	return [user.user for user in users]


def notify_errors(exceptions_list):
	subject = _("[Important] [ERPNext] Auto Reorder Errors")
	content = (
		_("Dear System Manager,")
		+ "<br>"
		+ _(
			"An error occured for certain Items while creating Material Requests based on Re-order level. Please rectify these issues :"
		)
		+ "<br>"
	)

	for exception in exceptions_list:
		try:
			exception = json.loads(exception)
			error_message = """<div class='small text-muted'>{}</div><br>""".format(
				_(exception.get("message"))
			)
			content += error_message
		except Exception:
			pass

	content += _("Regards,") + "<br>" + _("Administrator")

	from frappe.email import sendmail_to_system_managers

	sendmail_to_system_managers(subject, content)
