import random
import frappe
from erpnext.stock.utils import get_latest_stock_qty
from frappe.auth import today
from sarvadhi_custom.custom_api.reordr import reordr_item

def stock_LIFO(doc, method):
    print("stock_LIFO calling")
    
    if doc.stock_entry_type == "Material Issue":
        for item in doc.items:
            company = doc.company
            warehouse = item.s_warehouse
            item_code = item.item_code
            qty = item.qty

            print("company:", company)
            print("warehouse:", warehouse)
            print("item_code:", item_code)
            print("qty:", qty)

            # Fetch or create a batch dynamically
            batches = frappe.get_all(
                'Batch',
                filters={'item': item_code},
                fields=['name', 'creation'],
                order_by='creation DESC'
            )

            if batches:
                batch_no = batches[0]['name']
            else:
                new_batch = frappe.get_doc({
                    "doctype": "Batch",
                    "item": item_code,
                    "batch_id": f"{item_code}-{frappe.generate_hash(length=6)}"
                })
                new_batch.insert(ignore_permissions=True)
                frappe.db.commit()
                print("batch created for item:", item_code)
                batch_no = new_batch.name
            print("new batch no:", batch_no)

            # Check if Serial and Batch Bundle already exists for this transaction
            existing_bundle = frappe.get_all(
                "Serial and Batch Bundle",
                filters={
                    "voucher_no": doc.name,
                    "item_code": item_code,
                    "warehouse": warehouse
                },
                fields=["name"]
            )

            if existing_bundle:
                print(f"Serial and Batch Bundle already exists for {item_code}, skipping creation.")
            else:
                print(f"Creating Serial and Batch Bundle for {item_code} in {warehouse}")   
                entry = {
                    'batch_no': batch_no,
                    'qty': qty,
                    'warehouse': warehouse,
                    'voucher_type': 'Stock Entry',
                    'voucher_no': doc.name
                }

                print("Creating Serial and Batch Bundle with the following data:")
                print(f"Company: {company}")
                print(f"Item Code: {item_code}")
                print(f"Warehouse: {warehouse}")
                print(f"Batch No: {entry['batch_no']}")
                print(f"Voucher Type: {entry['voucher_type']}")
                print(f"Voucher No: {entry['voucher_no']}")

                # Create the Serial and Batch Bundle document
                batch = frappe.get_doc({
                    "doctype": "Serial and Batch Bundle",
                    'company': company,
                    'item_code': item_code,
                    'item_name': item_code,
                    'warehouse': warehouse,
                    'type_of_transaction': 'Inward',
                    'voucher_type': entry['voucher_type'],
                    'voucher_no': entry['voucher_no'],
                    'entries': [entry]
                })

                print(f"Batch Document Data: {batch.as_dict()}")

                batch.insert()
                frappe.db.commit()
                batch.submit()
                print(batch.name)

                print(f"Batch created for item {item_code} in warehouse {warehouse}")


def stock_reconciliation():
    print("stock_reconciliation")

    bin_data=frappe.get_all("Bin",fields=['item_code','actual_qty'],filters={'warehouse':'Finished Goods - SD','item_code':'air-conditioner'})
    actual_bin_qty=bin_data[0]["actual_qty"]
    print("actual_bin_qty:",actual_bin_qty)


    ledger_qty=frappe.db.get_all(
        "Stock Ledger Entry",
        fields=["item_code", "warehouse", "actual_qty", "voucher_no", "posting_date", "posting_datetime", "qty_after_transaction"],
        filters={
            "item_code": "air-conditioner",
            "warehouse": "Finished Goods - SD",
        },
        order_by="posting_datetime DESC",
        limit=1
    )

    stock_ledger_qty=ledger_qty[0]["qty_after_transaction"]
    print("stock_ledger_qty:",stock_ledger_qty)


    discrepancies_qty=abs(actual_bin_qty-stock_ledger_qty)
    print("discrepancies_qty:",discrepancies_qty)

    if discrepancies_qty>0:
        batch_no = frappe.db.get_value("Batch", {"item": "air-conditioner"}, "name")

        if actual_bin_qty!=discrepancies_qty:
            item={
                'item_code':'air-conditioner',
                'warehouse': 'Finished Goods - SD',
                'batch_no': batch_no,
                'qty': discrepancies_qty,
                'valuation_rate': random.randint(1000, 200000),
                'use_serial_batch_fields':1,
            }

            
            stock_reconciliation=frappe.get_doc({
                'doctype':'Stock Reconciliation',
                'company':'sarvadhi (Demo)',
                'purpose':'Stock Reconciliation',
                'posting_date':today(),
                'posting_time':'12:00:00',
                'items':[item]
            })
            stock_reconciliation.insert(ignore_permissions=True)
            frappe.db.commit()
            stock_reconciliation.submit()
        
            frappe.sendmail(
                recipients="pooja.sarvadhi@gmail.com",
                subject="Discrepancies found",
                message=f"Discrepancies found with {discrepancies_qty} quantity",
                )
            frappe.email.queue.flush()

        print("stock reconciliation created")




def sale():
    print("sale calling")

    query=f"""SELECT item_code, warehouse, MAX(posting_date) AS last_movement
            FROM `tabStock Ledger Entry`
            GROUP BY item_code, warehouse
            HAVING last_movement <= DATE_SUB(CURDATE(), INTERVAL 90 DAY); 
        """
    item=frappe.db.sql(query,as_dict=True)
    for i in item:
        sale_item=i["item_code"]
        print("query:",sale_item)

        data=frappe.get_doc('Item',sale_item)
        if not data:
            print("not a valid format")
        data.custom_sale_discount=50
        print(data.item_code)
        # print(sale_discount_fields)
        frappe.logger().info(f"Data before save: {data}")

        data.save()
        frappe.db.commit()
    print("discount:",data.custom_sale_discount)
    frappe.sendmail(
            recipients="pooja.sarvadhi@gmail.com",
            subject=f"Discount sale on {sale_item}",
            message=f"{sale_item} on sale get {data.custom_sale_discount} percent Discount",
            )  
    frappe.email.queue.flush()
