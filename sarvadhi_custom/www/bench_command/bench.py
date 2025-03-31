import os
import time

import frappe
from frappe.utils.file_manager import save_file
import requests

@frappe.whitelist(allow_guest=True)
def bench_migrate():
    os.system('bench migrate ')

@frappe.whitelist(allow_guest=True)
def bench_build():
    os.system('bench build ')

@frappe.whitelist(allow_guest=True)
def bench_clear_cache():
    os.system('bench clear-cache ')



@frappe.whitelist(allow_guest=True)
def bench_site():
    site_name=frappe.form_dict.get("site_name")
    print("site_name:",site_name)
    root_pwd=frappe.form_dict.get("root_pwd")
    print("root_pwd:",root_pwd)
    re_site_pwd=frappe.form_dict.get("re_site_pwd")
    print("re_site_pwd:",re_site_pwd)
    site_pwd=frappe.form_dict.get("site_pwd")
    print("site_pwd:",site_pwd)
    
    sn=site_name+".localhost"
    # site=f'bench new-site {site_name}'
    site = f"bench new-site {sn} --mariadb-root-password '{root_pwd}' --admin-password '{site_pwd}' "

    print("site:",site)
    os.system(site) 
    print("site created")

    time.sleep(5)


    pwd=f"bench --site {sn} set-admin-password '{site_pwd}'"
    print("pwd:",pwd)
    os.system(pwd)






@frappe.whitelist(allow_guest=True)
def attach_resume():
    file = frappe.request.files.get('file')
    print("file:",file)
    docname = frappe.form_dict.get('docname')
    doctype = frappe.form_dict.get('doctype')

    print("docname:",docname)
    print("doctype:",doctype)
    file_name=file.filename
    print("file_name:",file_name)
    if not file or not docname or not doctype:
        frappe.throw("Missing file, doctype, or docname")

    new_doc = frappe.get_doc({
        "doctype": doctype,
        "name": docname,  
        "resume": file ,
        "file_url":f"/files/{file_name}",
        "content": file.stream.read(),
        "is_private": 0  # Make file public
    })
    new_doc.insert(ignore_permissions=True)  
    new_doc.save()
    print("after saved")
    new_doc.resume = new_doc.file_url
    new_doc.save(ignore_permissions=True) 

    frappe.db.commit()

    return {"message": f"File uploaded to {new_doc.file_url}"}


# def attach_resume(doc,method):
#     frappe.msgprint("hiii")
#     var=frappe.utils.get_url_to_form(doc.doctype, doc.name)
#     frappe.msgprint(var)
#     base_url="https://api.dub.co/qr?url=http://"
#     frappe.msgprint(base_url)
#     main_url=base_url+var
#     frappe.msgprint(main_url)   
#     file = frappe.request.files.get('file')
#     docname = frappe.form_dict.get('docname')
#     doctype = frappe.form_dict.get('doctype')

#     print("docname:",docname)
#     print("doctype:",doctype)

#     if not file or not docname or not doctype:
#         frappe.throw("Missing file, doctype, or docname")
#     response = requests.get(main_url)
#     if response.status_code==200:
#         ans=response.content
#         image= f"QR_{doc.name}.png"
#         file_doc = frappe.get_doc({
#                     "doctype": "File",
#                     "file_name": image,
#                     "attached_to_doctype": doc.doctype,
#                     "file_url":f"/files/{image}",
#                     "attached_to_name": doc.name,
#                     "content":ans,
#                 } )
#         file_doc.save()
#     else:
#         frappe.throw("error")