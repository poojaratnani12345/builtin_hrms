import frappe
@frappe.whitelist()
def get_child_api(sales_order_link):
    # sales=frappe.db.sql(f""" SELECT * FROM `tabSales order item` WHERE parent='{sales_order_link}' """,as_dict=True)    
    # print("saleaS:",sales)
    # return sales
    sales=frappe.get_all("Sales order item",fields=["item_name","uom","conversion_factor","item_code","qty","amount","rate","delivery_date"],filters={'parent':sales_order_link})
    print("saleaS:",sales)
    return sales

