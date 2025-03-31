

import random
import frappe


def create_quality_inpection_from_purchase_receipt(doc, method=None):
    print("create_quality_inpection_from_purcahse recipt calling")
    print(f"Document Data: {doc}")
    print(f"Document Type: {doc.items[0].item_code}")

    # Get the current document name
    document_name = doc.name
    print(f"Current Document Name: {document_name}")
    print(f"Type of doc: {type(doc)}")

  
    purchase_r = doc.items
    print("Purchase receipt items:", purchase_r)

    for i in purchase_r:
        pr_item=i.item_code
        print("item code:",pr_item)

    

    item=frappe.get_all('Item',filters={'item_code':pr_item},fields=['item_group'])
    print("item group:",item[0]['item_group'])
    if item[0]['item_group']=='Products':
        print(item[0]['item_group'])
        min_value=200
        max_value=250
        print(min_value)
        print(max_value)
    elif item[0]['item_group']=='Consumable':
        min_value=90
        max_value=150
        print(min_value)
        print(max_value)
    elif item[0]['item_group']=='Raw Material':
        min_value=50
        max_value=100
        print(min_value)
        print(max_value)
    elif item[0]['item_group']=='Services':
        min_value=10
        max_value=50
        print(min_value)
        print(max_value)
    elif item[0]['item_group']=='Demo Item Group':
        min_value=0
        max_value=10
        print(min_value)
        print(max_value)
    elif item[0]['item_group']=='Sub Assemblies':
        min_value=0
        max_value=5
        print(min_value)
        print(max_value)
    else:       #this is for all item groups
        min_value=0
        max_value=0
        print(min_value)
        print(max_value)

    reading = [{
        "specification": "quality",
       'status': 'Accepted',
        "numeric": 1,
        'min_value':min_value,
        'max_value':max_value,
        "reading_value": doc.custom_reading_value_for_qi,
        "reading_1": doc.custom_reading
    },
    {
        "specification":'aging test',
        'status': 'Accepted',
        "numeric": 1,
        'min_value':min_value,
        'max_value':max_value,
        "reading_value": doc.custom_reading_value_for_qi,
        "reading_1": doc.custom_reading
    }
    ]

    quality_inspection = frappe.get_doc({
        "doctype": "Quality Inspection",
        "item_code":pr_item,
        "batch_no": "aircondition0021",
       'status': 'Accepted',
        "inspection_type": "Incoming",
        "reference_type": "Purchase Receipt",
        "reference_name": doc.get("name"),
        "sample_size": 0,
        "inspected_by": "ratnanipooja000@gmail.com",
        "verified_by": "Pooja",
        'readings':reading,
        'custom_supplier_name':doc.supplier,
    })

    print(f"Creating Quality Inspection for: ")
    quality_inspection.insert(ignore_permissions=True, ignore_links=True)
    quality_inspection.save(ignore_permissions=True)

    frappe.db.commit()
    print(f"Final Status Before Save: {quality_inspection.status}")
    print(f"Readings Data: {quality_inspection.readings}")

    quality_inspection.submit()

    qi_name = quality_inspection.name
    print(f"Created Quality Inspection: {qi_name}")


    customer=frappe.get_all("Customer")
    random_customer = random.choice(customer) if customer else None
    print(random_customer['name'])

    if quality_inspection.status=='Rejected':
        issue=frappe.get_doc({
            'doctype':'Issue',
            'subject':f'Quality inspection Rejected for {quality_inspection.item_code}',
            'status':'Open',
            'customer':random_customer['name'],
            'priority':'High',
            'issue_type':'Quality inspection',

        })
        issue.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()
        issue.submit()

        frappe.sendmail(
        recipients="shrutipaneliya.sarvadhi@gmail.com",
        subject="Your product was Rejected ",
        message=f"Your product {quality_inspection.item_code} was Rejected because its quality was not good",
        )
        frappe.email.queue.flush()



    


def rejection_rate():
    print("rejection rate calling")

    rejected_qty=frappe.db.count('Quality Inspection',filters={'status':'Rejected','batch_no':'aircondition0021'})  
    print("rejected item count:",rejected_qty)

    if rejected_qty>=10:
        frappe.sendmail(
        recipients='ratnanipooja000@gmail.com',
        subject="Your product Rejection rate ",
        message=f"Your product Rejection rate per month was {rejected_qty} so we notify you",
        )
        frappe.email.queue.flush()


