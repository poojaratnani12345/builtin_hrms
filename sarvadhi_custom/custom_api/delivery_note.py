import frappe
import requests

@frappe.whitelist(allow_guest=True)
def note(self,method):
    frappe.logger().info("purchase_to_sales_api called")

    print("save_sales_order calling")
    purchase_url='http://hr.localhost:8007/api/resource/Purchase%20Receipt'
    print("url:",purchase_url)
    headers= { 
            'Authorization': 'token 1b99bc035156c5d:704ee217922d058',
            'Content-Type': 'application/json' 
        }
   
    res=requests.get(purchase_url,headers=headers)
    print("responssss::::",res.status_code)
    print("text:",res.text)
    delivery_note=frappe.get_all("Delivery Note",fields=["name","total_qty","posting_date","posting_time","currency","set_warehouse","base_total"],order_by="posting_date DESC",limit=1)
    print("delivery_note:",delivery_note)


    posting_time=delivery_note[0]["posting_time"]
    currency=delivery_note[0]["currency"]
    set_warehouse=delivery_note[0]["set_warehouse"]  
    total_qty=delivery_note[0]["total_qty"] 
    base_total=delivery_note[0]["base_total"]
    posting_date=delivery_note[0]["posting_date"]
    qty=delivery_note[0]["total_qty"]
       

    print("posting_time:",posting_time)
    print("currency:",currency)
    print("set_warehouse:",set_warehouse)
    print("total_qty:",total_qty)
    print("base_total:",base_total)
    print("base_total:",base_total)
    print("posting_date:",posting_date)
    print("qty:",qty)

    item={
            'item_code':'ITEM-001',
            'qty':qty,
            'rate':100 
        }
    try:
        purchase_receipt=frappe.get_doc({
            'doctype':'Purchase Receipt',
            'supplier':'Zuckerman Security Ltd.',
            'set_warehouse':set_warehouse,
            'posting_time':str(posting_time),
            'items':[item],
            'posting_date':posting_date.strftime("%Y-%m-%d"),
        })
        purchase_receipt_data=purchase_receipt.as_dict()
        print("\n purchase receipt data \n:",purchase_receipt_data)
        
        response=requests.post(purchase_url,headers=headers,json=purchase_receipt_data)

        print("response:",response)
        print("response text:",response.text)

        if response.status_code==200:
            print(" data sent")
        else:
            print("not valid url")
        
    except Exception as e:
        print("error:",e)

    return 