
import frappe
import requests


@frappe.whitelist(allow_guest=True)
def sales_api():
    frappe.logger().info("purchase_to_sales_api called")

    print("save_sales_order calling")
    purchase_url='http://hrms.sarvadhi.work/api/resource/Purchase Order?fields=["supplier","supplier_name","total_qty","buying_price_list","currency","transaction_date","schedule_date","name"]'
    print("url:",purchase_url)
    headers= { 
            'Authorization': 'token 48f220eb8f94ac7:8385bdd7f2177ea',
            'Content-Type': 'application/json' 
        }
    response=requests.get(purchase_url,headers=headers)
    print("response:",response)
    if response.status_code==200:
        print(" valid url")
    else:
        print("not valid url")

    data=response.json()

    print("data:",data["data"][0])

    purchase_order_length=len(data["data"])
    print("lengyth:",purchase_order_length)

    try:
        for i in range(purchase_order_length):
            supplier=data["data"][i]["supplier"]
            supplier_name=data["data"][i]["supplier_name"]
            total_qty=data["data"][i]["total_qty"]
            buying_price_list=data["data"][i]["buying_price_list"]
            currency=data["data"][i]["currency"]
            # company=data["data"][i]["company"]
            transaction_date=data["data"][i]["transaction_date"]
            schedule_date=data["data"][i]["schedule_date"]
            name=data["data"][i]["name"]

            print("supplier:",supplier)
            print("supplier_name:",supplier_name)
            print("total_qty:",total_qty)
            print("buying_price_list:",buying_price_list)
            print("currency:",currency)
            # print("company:",company)
            print("transaction_date:",transaction_date)
            print("schedule_date:",schedule_date)
            print("name:",name)
        
            item={
                'item_code':'ITEM-001',
                'transaction_date':transaction_date,
                'qty':total_qty,
                'rate':100 
            }

            sale_order=frappe.get_doc({
                'doctype':'Sales Order',
                'customer':"Grant Plastics Ltd.",
                'order_type':"Sales",
                'delivery_date':schedule_date,
                'set_warehouse':'Stores - SD',
                'po_no':name,
                'po_date':transaction_date,
                'items':[]
            })

            print("before append sale_order:",sale_order)
            sale_order.append("items",item)
            print("after append child table sales order:",sale_order)

            purchase_no=frappe.get_all("Sales Order",fields=["po_no"])
            existing_po_numbers = {po["po_no"] for po in purchase_no}
            if name in existing_po_numbers:
               continue
            else:
                sale_order.insert(ignore_permissions=True)
                print("save sales order")
                frappe.db.commit() 


            

    except Exception as e:
        print("error:",e)

    



    return response.json()
