import xmlrpc.client

url = "http://localhost:8069"
db = "kia_test"
username = "admin"  # guessing admin
password = "admin"  # guessing admin

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
if not uid:
    print("Could not authenticate")
else:
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', [[('name', '=', 'ac_ars_cc_camera')]], {'fields': ['name', 'state']})
    print(modules)
