
import frappe
from frappe.auth import today
from sarvadhi_custom.custom_api.reordr import reordr_item


def work_order(doc,method):
    print("work_order function calling")
    data=frappe.get_all("Sales Order",fields=["name","total_qty","delivery_date"],filters={"status":"To Deliver and Bill"},limit=1)
    total_qty=data[0]["total_qty"]
    name=data[0]["name"]
    delivery_date=data[0]["delivery_date"]
    print("name:",name)  
    print("qty:",total_qty)  


    purchase_r = doc.items
    print("Purchase receipt items:", purchase_r)

    for i in purchase_r:
        pr_item=i.item_code
        print("item code:",pr_item)


    stock=frappe.db.get_all(
        "Stock Ledger Entry",
        fields=["item_code", "warehouse", "actual_qty", "voucher_no", "posting_date", "posting_datetime", "qty_after_transaction"],
        filters={
            "item_code":pr_item,
            "warehouse": "Finished Goods - SD"
        },
        order_by="posting_datetime DESC",
        limit=1
    )
    total_stock_qty=stock[0]["qty_after_transaction"]
    print("stock qty:",total_stock_qty)
  
    if total_stock_qty>=total_qty:
        print("item is on stock you can directly dilivered")
        frappe.msgprint("item is on stock you can directly dilivered")
    else:
        frappe.msgprint("work order created")

        raw_data=frappe.get_all("BOM Explosion Item",fields=["item_code","rate","amount"],limit=3)
        require_item=[]
        for i in raw_data   :
            item_code=i["item_code"]
            print("item_code:",item_code)
            rate=i["rate"]
            amount=i["amount"]
            item={
            'item_code':item_code,
            'source_warehouse':'Stores - SD',
            'required_qty':total_qty,
            'amount':amount,
            'rate':rate
            }
            print("item:",item)

            require_item.append(item)
        
        bom_item=frappe.get_all("BOM",fields=["item",'name'],filters={'item':'air-conditioner'}) 
        production_item=bom_item[0]["item"] 
        bom_no=bom_item[0]["name"]  
        doc=frappe.get_doc({
            'doctype':'Work Order',
            'production_item':production_item,
            'bom_no':bom_no,
            'qty':total_qty,
            'sales_order':name,
            'required_items':require_item
        })
        print("doc:",doc)
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()
        print("after insert")
        # quality_inpection_creation(doc,method)

    
        reference_name=frappe.get_last_doc('Work Order')    
        # reference_name=work_order_name[0]["name"]
        assign=frappe.get_doc({
        'doctype': "ToDo",
        'status': 'Open',
        'priority': 'High',
        'date':delivery_date,
        'allocated_to':'pooja.sarvadhi@gmail.com',
        'description':'Work Order allocate to pooja.sarvadhi@gmail.com',
        'assigned_by':'frappe.session.user',
        'reference_type':'Work Order',
        'reference_name':reference_name
        })
        assign.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.sendmail(
        recipients="pooja.sarvadhi@gmail.com",
        subject="you have work order assign to you",
        message=f"your work order is {total_qty}",
        )
        frappe.email.queue.flush()

    return 'abc'




def manual_reorder(item_nm):
    print("manual_reorder calling")
    reorder_levels = frappe.get_all(
        "Item Reorder",
        filters={"parent": item_nm},
        fields=["warehouse", "warehouse_reorder_level"]
    )

    if not reorder_levels:
        frappe.logger().info(f"No reorder levels found for item: {item_nm}")
        return f"No reorder levels found for {item_nm}."

    items_to_reorder = []

    for reorder in reorder_levels:
        warehouse = reorder["warehouse"]

        print(f" Checking stock for: {item_nm} in {warehouse}")

        stock_qty = frappe.db.get_value("Bin", {"item_code": item_nm, "warehouse": warehouse}, "actual_qty")

        if stock_qty is None:
            print(f" No stock record found in Bin for {item_nm} in {warehouse}. Skipping...")
            continue  # Skip this warehouse

        print(f" Stock for {item_nm} in {warehouse}: {stock_qty}")

        print(f"Checking {item_nm} in {warehouse} (Stock: {stock_qty}, Reorder Level: {reorder['warehouse_reorder_level']})")

        if stock_qty < reorder["warehouse_reorder_level"]:
            print(" Reorder needed!")
            items_to_reorder.append({"item_code": item_nm, "warehouse": warehouse})

    if items_to_reorder:
        frappe.logger().info(f"Reorder required for: {items_to_reorder}")
        from erpnext.stock.reorder_item import reorder_item
        reordr_item()   # Uncomment this when you're ready to trigger the reorder
        return f" Reorder triggered for {item_nm} in warehouses: {items_to_reorder} and Reorder {item_nm} successfully"

    frappe.logger().info(f" No reorder required for {item_nm}.")
    return f"No reorder required for {item_nm}."


