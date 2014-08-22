from app import app
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
# http://www.rethinkdb.com/api/python/

from forms import OrganizationEdit, OrganizationAdd
from forms import IpAddressEdit, IpAddressAdd
from forms import InterfaceEdit, InterfaceAdd
from forms import HostTypeAdd, HostTypeEdit
from forms import HostAdd, HostEdit
from forms import CircuitAdd, CircuitEdit
from forms import Vlan, Vrf
from forms import IanaIfType

from netaddr import IPNetwork
# http://pythonhosted.org//netaddr/tutorial_01.html

HOST = 'localhost'
PORT = 28015
DB   = 'qv'

# http://www.realpython.com/blog/python/rethink-flask-a-simple-todo-list-powered-by-flask-and-rethinkdb
# rethink setup, runs only once for schema creation
def SetupRethink():
  connection = r.connect( host=HOST, port=PORT )
  try:
    r.db_create( DB ).run( connection )
    try:
      r.db( DB ).table_create( 'organization', primary_key='idorganization' ).run( connection )

      r.db( DB ).table_create( 'ianaiftype', primary_key='idianaiftype' ).run( connection )
      r.db( DB ).table_create( 'vlan', primary_key='idvlan' ).run( connection )
      r.db( DB ).table_create( 'vrf', primary_key='idvrf' ).run( connection )
      r.db( DB ).table_create( 'hosttype', primary_key='idhosttype' ).run( connection )

      r.db( DB ).table( 'organization' ).insert(
        { "asn": 19626, "description": "hosting organization",
          "idorganization": "QVSL", "name": "Quovadis Services Limited", "url": 'http://www.quovadis.bm' 
          } ).run( connection )

      r.db( DB ).table_create( 'ipaddress', primary_key='idipaddress' ).run( connection )
      r.db( DB ).table('ipaddress').index_create('idorganization')

      r.db( DB ).table_create( 'circuit', primary_key='idcircuit' ).run( connection )
      r.db( DB ).table( 'circuit' ).index_create('idipaddress').run(connection )

      r.db( DB ).table_create( 'host', primary_key='idhost' ).run( connection )
      r.db( DB ).table( 'host' ).index_create( 'idhosttype' ).run( connection )

      r.db( DB ).table_create( 'interface', primary_key='idinterface' ).run( connection )
      r.db( DB ).table( 'interface' ).index_create( 'idhost' ).run( connection )
      r.db( DB ).table( 'interface' ).index_create( 'idipaddress' ).run( connection )
      r.db( DB ).table( 'interface' ).index_create( 'idcircuit' ).run( connection )
      r.db( DB ).table( 'interface' ).index_create( 'idvlan' ).run( connection )
      r.db( DB ).table( 'interface' ).index_create( 'idvrf' ).run( connection )

      print 'Database setup completed'
    except RqlRuntimeError:
      print 'Database creation problem'
    finally:
      pass
  except RqlRuntimeError:
    print 'Database already exists'
  finally:
    connection.close()  

SetupRethink()

@app.before_request
def before_request():
  try:
    g.rdb_conn = r.connect( host=HOST, port=PORT, db=DB )
  except RqlDriverError:
    abort( 503, "Database connection could not be established" )

@app.teardown_request
def teardown_request( exception ):
  try:
    g.rdb_conn.close()
  except AttributeError:
    pass

@app.route('/')
@app.route('/index')
def root():
#  user = { 'nickname': 'ray' }
  return render_template( 'index.html' )
#  return "Hello, World!"
#  return render_template( 'index', user = user )

## organization

@app.route('/organizations')
def organizations():
#  selection = list(r.db('qv').table('organization').run( g.rdb_conn ))
  selection = r.db('qv').table('organization').order_by('idorganization').run( g.rdb_conn )
  return render_template( 'organization.html', organizations=selection )
  
@app.route('/organization/edit/<idorganization>', methods=['GET','POST'])
def organization_edit( idorganization ):

  form = OrganizationEdit()

  selection = r.db('qv').table('organization').get(idorganization).run(g.rdb_conn)

  if 'GET' == request.method:
    form.name.data = selection['name']
    if selection.has_key('description'):
      form.description.data = selection['description']
    if selection.has_key('asn'):
      form.asn.data = selection['asn']
    if selection.has_key('url'): 
      form.url.data = selection['url']
    return render_template( 'organization_edit.html', org=selection, form=form, mode='edit' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('organization').get(idorganization).update(form.data).run(g.rdb_conn)
      flash('organization changes saved')
      return redirect( url_for( 'organizations' ) )
    else:
      flash('error somewhere')
      return render_template( 'organization_edit.html', org=selection, form=form, mode='edit' )

  return redirect( url_for( 'organizations' ) )
  
@app.route('/organization/add', methods=['GET','POST'])
def organization_add():
  form = OrganizationAdd()
  if 'GET' == request.method:
    return render_template( 'organization_edit.html', form=form, mode='add' )
  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('organization').insert(form.data).run(g.rdb_conn)
      # what next?  another new one, edit mode, or organization?
      return redirect( url_for( 'organizations' ) )
    else:
      return render_template( 'organization_edit.html', form=form, mode='add' )
  return redirect( url_for( 'organizations' ) )

@app.route('/organization/delete/<idorganization>', methods=['GET'])
def organization_delete(idorganization):
  # note that this is dangerous for public link, as a crawler will trigger it
  # also require a yes/no confirmation
  # need to confirm it is not associated with other records

  if 0 == r.db('qv').table('ipaddress').filter({'idorganization':idorganization}).count().run(g.rdb_conn):
    r.db('qv').table('organization').get(idorganization).delete().run(g.rdb_conn)
    flash('organization delted')
  else:
    flash('organization in use: not deleted')  
  return redirect( url_for( 'organizations' ) )

## ipaddress

@app.route('/ipaddresses')
def ipaddresses():
#  selection = list(r.db('qv').table('ipaddress').run( g.rdb_conn ))
  selection = r.db('qv').table('ipaddress').order_by('ipaddress').run( g.rdb_conn )
  final = []
  for record in selection:
    newrec = {}
    for field in record:
      newrec[field] = record[field]
      if '' != record['parent']:
        selectParent = r.db('qv').table('ipaddress').get(record['parent']).run(g.rdb_conn)
        newrec['parent'] = selectParent['ipaddress']
    final.append(newrec)
  return render_template( 'ipaddress.html', ipaddresses=final )
#  return render_template( 'ipaddress.html', ipaddresses=selection )

@app.route('/ipaddress/edit/<idipaddress>', methods=['GET','POST'] )
def ipaddress_edit( idipaddress ):

  form = IpAddressEdit()

  selectOrganization = r.db('qv').table('organization').run(g.rdb_conn)
  form.idorganization.choices = [ (item['idorganization'], item['name']) for item in selectOrganization ]

  selectParent = r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.parent.choices  = [( '', 'no parent' )]
  form.parent.choices += [(item['idipaddress'],item['ipaddress']) for item in selectParent ]

  if 'GET' == request.method:
 
    selection = r.db('qv').table('ipaddress').get(idipaddress).run(g.rdb_conn)

    form.idipaddress.data = selection['idipaddress']
    form.ipaddress.data = selection['ipaddress']
    form.idorganization.data = selection['idorganization']
    form.parent.data = selection['parent']

    if selection.has_key('name'):
      form.name.data = selection['name']
    if selection.has_key('description'):
      form.description.data = selection['description']
    if selection.has_key('url'):
      form.url.data = selection['url']
    return render_template( 'ipaddress_edit.html', form=form, mode='edit' )

  if 'POST' == request.method:

    if form.validate_on_submit():
      r.db('qv').table('ipaddress').get(idipaddress).update(form.data).run(g.rdb_conn)
      flash('ipaddress changes saved')
      return redirect( url_for( 'ipaddresses' ) )
    else:
      flash('ipaddresses error somewhere')
      selection = r.db('qv').table('ipaddress').get(idipaddress).run(g.rdb_conn)
      return render_template( 'ipaddress_edit.html',form=form, mode='edit' )

  return redirect( url_for( 'ipaddresses' ) ) 

@app.route('/ipaddress/add', methods=['GET','POST'])
def ipaddress_add():

  form = IpAddressAdd()

  selection=r.db('qv').table('ipaddress').run(g.rdb_conn)

  # needs to be here as used with both get and post
  selectParent=r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.parent.choices = [('','no parent')]
  form.parent.choices += [(item['idipaddress'], item['ipaddress']) for item in selectParent]

  selectOrganization = r.db('qv').table('organization').run(g.rdb_conn)
  form.idorganization.choices = [ (item['idorganization'], item['name']) for item in selectOrganization ]

  if 'GET' == request.method:
    form.idorganization.data = 'QVSL'
    return render_template( 'ipaddress_edit.html', form=form, mode='add' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      # need to check for redundant ipaddress for the specific idorganization
      r.db('qv').table('ipaddress').insert(form.data).run(g.rdb_conn)
      return redirect( url_for( 'ipaddresses' ) )
    else:
      return render_template( 'ipaddress_edit.html', form=form, mode='add' )

  return redirect( url_for( 'ipaddresses' ) )

@app.route('/ipaddress/delete/<idipaddress>', methods=['GET'])
def ipaddress_delete( idipaddress ):
  if      0 == r.db('qv').table('circuit').filter({'idipaddress':idipaddress}).count().run(g.rdb_conn) \
      and 0 == r.db('qv').table('interface').filter({'idipaddress':idipaddress}).count().run(g.rdb_conn) \
      and 0 == r.db('qv').table('ipaddress').filter({'parent':idipaddress}).count().run(g.rdb_conn):
    r.db('qv').table('ipaddress').get(idipaddress).delete().run(g.rdb_conn)
    flash('address deleted')
  else:
    flash('address in use, not deleted')
  return redirect( url_for( 'ipaddresses' ) )

## host

@app.route('/hosts')
def hosts():
  selection = r.db('qv').table('host').order_by('name').run( g.rdb_conn )
  return render_template( 'host.html', hosts=selection )

@app.route('/host/edit/<idhost>', methods=['GET','POST'] )
def host_edit( idhost ):

  form = HostEdit()

  # used for both get and post
  selectParent=r.db('qv').table('host').run(g.rdb_conn)
  form.parent.choices = [('','no parent')]
  form.parent.choices += [(item['idhost'], item['name']) for item in selectParent]

  selectHostType=r.db('qv').table('hosttype').run(g.rdb_conn)
  form.idhosttype.choices = [(item['idhosttype'], item['name']) for item in selectHostType ]

  if 'GET' == request.method:
    selection = r.db('qv').table('host').get(idhost).run(g.rdb_conn)
    form.idhost.data = selection['idhost']
    form.name.data = selection['name']
    form.idhosttype.data = selection['idhosttype']
    form.parent.data = selection['parent']
    if selection.has_key('description'):
      form.description.data = selection['description']
    if selection.has_key('url1'):
      form.url1.data = selection['url1']
    if selection.has_key('url2'):
      form.url2.data = selection['url2']
    return render_template( 'host_edit.html', form=form, mode='edit' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      # is there a way to verify that idhost key hasn't been changed?
      # maybe use a cookie (auto crypto'd) instead
      r.db('qv').table('host').get(idhost).update(form.data).run(g.rdb_conn)
      flash('host changes saved')
      return redirect( url_for( 'hosts' ) )
    else:
      flash('host error somewhere')
      return render_template( 'host_edit.html', form=form, mode='edit' )

  return redirect( url_for( 'hosts' ) )

@app.route('/host/add', methods=['GET','POST'])
def host_add():
  form = HostAdd()

  # used for both get and post
  selectParent=r.db('qv').table('host').run(g.rdb_conn)
  form.parent.choices = [('','no parent')]
  form.parent.choices += [(item['idhost'], item['name']) for item in selectParent ]

  selectHostType = r.db('qv').table('hosttype').run(g.rdb_conn)
  form.idhosttype.choices = [(item['idhosttype'], item['name']) for item in selectHostType]

  if 'GET' == request.method:
    return render_template( 'host_edit.html', form=form, mode='add' )
  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('host').insert( form.data).run(g.rdb_conn)
      return redirect( url_for( 'hosts' ) )
    else:
      return render_template( 'host_edit.html', form=form, mode='add' )
  return redirect( url_for( 'hosts' ) )

@app.route('/host/delete/<idhost>', methods=['GET'])
def host_delete( idhost ):
  if      0 == r.db('qv').table('interface').filter({'idhost':idhost}).count().run(g.rdb_conn) \
      and 0 == r.db('qv').table('host').filter({'parent':idhost}).count().run(g.rdb_conn):
    selection = r.db('qv').table('host').get(idhost).delete().run(g.rdb_conn)
    flash('host deleted')
  else:
    flash('host in use, not deleted')
  return redirect( url_for( 'hosts' ) )

## hosttype

@app.route('/hosttypes')
def hosttypes():
  selection = r.db('qv').table('hosttype').order_by('name').run( g.rdb_conn)
  return render_template( 'hosttype.html', hosttypes=selection )

@app.route('/hosttypes/edit/<idhosttype>', methods=['GET','POST'] )
def hosttype_edit( idhosttype ):
  form = HostTypeEdit()
  if 'GET' == request.method:
    selection = r.db('qv').table('hosttype').get(idhosttype).run(g.rdb_conn)
    form.idhosttype.data = selection['idhosttype']
    form.name.data = selection['name']
    if selection.has_key('description'):
      form.description.data = selection['description']
    return render_template( 'hosttype_edit.html', form=form, mode='edit' )
  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('hosttype').get(idhosttype).update(form.data).run(g.rdb_conn)
      flash('hosttype changes saved')
      return redirect( url_for( 'hosttypes' ) )
    else:
      flash('hosttype error somewhere')
      return render_template( 'hosttype_edit.html', form=form, mode='edit' )
  return redirect( url_for( 'hosttypes' ) )

@app.route('/hosttype/add', methods=['GET','POST'] )
def hosttype_add():
  form = HostTypeAdd()
  if 'GET' == request.method:
    return render_template( 'hosttype_edit.html', form=form, mode='add' )
  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('hosttype').insert( form.data ).run(g.rdb_conn)
      return redirect( url_for( 'hosttypes' ) )
    else:
      return render_template( 'hosttype_edit.html', form=form, mode='add' )
  return redirect( url_for( 'hosttypes' ) )

@app.route('/hosttype/delete/<idhosttype>', methods=['GET'])
def hosttype_delete(idhosttype):
  # note that this is dangerous for public link, as a crawler will trigger it
  # also require a yes/no confirmation
  if 0 == r.db('qv').table('host').filter({'idhosttype':idhosttype}).count().run(g.rdb_conn):
    selection = r.db('qv').table('hosttype').get(idhosttype).delete().run(g.rdb_conn)
    flash('hosttype deleted')
  else:
    flash('hosttype in use, not deleted')
  return redirect( url_for( 'hosttypes' ) )

## interface

@app.route('/interfaces')
def interfaces():
  selection = r.db('qv').table('interface').order_by('name').run( g.rdb_conn )
  return render_template( 'interface.html', interfaces=selection )

@app.route('/interface/edit/<idinterface>', methods=['GET','POST'] )
def interface_edit( idinterface ):

  form = InterfaceEdit()

  selectIpaddress = r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.idipaddress.choices  = [('','no ip address')]
  form.idipaddress.choices += [(item['idipaddress'],item['ipaddress']) for item in selectIpaddress ]

  selectCircuit = r.db('qv').table('circuit').run(g.rdb_conn)
  form.idcircuit.choices  = [('','no circuit')]
  form.idcircuit.choices += [(item['idcircuit'],item['name']) for item in selectCircuit ]

  selectHost = r.db('qv').table('host').run(g.rdb_conn)
  form.idhost.choices = [(item['idhost'],item['name']) for item in selectHost ]

  selectInterface = r.db('qv').table('interface').run(g.rdb_conn)
  form.parent.choices  = [('','no parent')]
  form.parent.choices += [(item['idinterface'],item['name']) for item in selectInterface ]

  if 'GET' == request.method:
 
    selection = r.db('qv').table('interface').get(idinterface).run(g.rdb_conn)

    form.idinterface.data = selection['idinterface']
    form.idhost.data = selection['idhost']
    form.name.data = selection['name']
    form.parent.data = selection['parent']
    form.idipaddress.data = selection['idipaddress']
    form.idcircuit.data = selection['idcircuit']
    if selection.has_key('description'):
      form.description.data = selection['description']
    if selection.has_key('fqdn'):
      form.fqdn.data = selection['fqdn']
    if selection.has_key('url'):
      form.url.data = selection['url']
    if selection.has_key('mac'):
      form.mac.data = selection['mac']
    if selection.has_key('idvlan'):
      form.idvlan.data = selection['idvlan']
    if selection.has_key('idvrf'):
      form.idvrf.data = selection['idvrf']
    return render_template( 'interface_edit.html', form=form, mode='edit' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      # is there a way to verify that idinterface key hasn't been changed?
      # maybe use a cookie (auto crypto'd) instead
      r.db('qv').table('interface').get(idinterface).update(form.data).run(g.rdb_conn)
      flash('interface changes saved')
      return redirect( url_for( 'interfaces' ) )
    else:
      flash('interface error somewhere')
      return render_template( 'interface_edit.html', form=form, mode='edit' )

  return redirect( url_for( 'interfaces' ) )

@app.route('/interface/add', methods=['GET','POST'])
def interface_add():

  form = InterfaceAdd()

  selectIpaddress = r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.idipaddress.choices  = [('','no ip address')]
  form.idipaddress.choices += [(item['idipaddress'],item['ipaddress']) for item in selectIpaddress ]

  selectCircuit = r.db('qv').table('circuit').run(g.rdb_conn)
  form.idcircuit.choices  = [('','no circuit')]
  form.idcircuit.choices += [(item['idcircuit'],item['name']) for item in selectCircuit ]

  selectHost = r.db('qv').table('host').run(g.rdb_conn)
  form.idhost.choices = [(item['idhost'],item['name']) for item in selectHost ]

  selectInterface = r.db('qv').table('interface').run(g.rdb_conn)
  form.parent.choices  = [('','no parent')]
  form.parent.choices += [(item['idinterface'],item['name']) for item in selectInterface ]

  if 'GET' == request.method:
    return render_template( 'interface_edit.html', form=form, mode='add' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('interface').insert( form.data).run(g.rdb_conn)
      return redirect( url_for( 'interfaces' ) )
    else:
      return render_template( 'interface_edit.html', form=form, mode='add' )

  return redirect( url_for( 'interfaces' ) )

@app.route('/interface/delete/<idinterface>', methods=['GET'])
def interface_delete( idinterface ):
  if 0 == r.db('qv').table('interface').filter({'parent':idinterface}).count().run(g.rdb_conn):
    r.db('qv').table('interface').get(idinterface).delete().run(g.rdb_conn)
  return redirect( url_for( 'interfaces' ) )

## circuit
@app.route('/circuits')
def circuits():
  selection = r.db('qv').table('circuit').run(g.rdb_conn)
  return render_template( 'circuit.html', circuits=selection )

@app.route('/circuit/add', methods=['GET','POST'] )
def circuit_add():
  form = CircuitAdd()

  selectIpaddress = r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.idipaddress.choices  = [('','no network address')]
  form.idipaddress.choices += [(item['idipaddress'],item['ipaddress']) for item in selectIpaddress ]

  selectCircuit = r.db('qv').table('circuit').run(g.rdb_conn)
  form.parent.choices  = [('','no parent circuit')]
  form.parent.choices += [(item['idcircuit'],item['name']) for item in selectCircuit ]

  if 'GET' == request.method:
    return render_template( 'circuit_edit.html', form=form, mode='add' )
  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('circuit').insert( form.data ).run( g.rdb_conn )
      return redirect( url_for( 'circuits' ) )
    else:
      return render_template( 'circuit_edit.html', form=form, mode='add' )
  return redirect( url_for( 'circuits' ) )


@app.route('/circuit/edit/<idcircuit>', methods=['GET','POST'] )
def circuit_edit( idcircuit ):

  form = CircuitEdit()

  selectIpaddress = r.db('qv').table('ipaddress').run(g.rdb_conn)
  form.idipaddress.choices  = [('','no network address')]
  form.idipaddress.choices += [(item['idipaddress'],item['ipaddress']) for item in selectIpaddress ]

  selectCircuit = r.db('qv').table('circuit').run(g.rdb_conn)
  form.parent.choices  = [('','no parent circuit')]
  form.parent.choices += [(item['idcircuit'],item['name']) for item in selectCircuit ] 

  if 'GET' == request.method:

    selection = r.db('qv').table('circuit').get(idcircuit).run(g.rdb_conn)

    form.idcircuit.data = selection['idcircuit']
    form.name.data = selection['name']
    form.parent.data = selection['parent']
    form.idipaddress.data = selection['idipaddress']
    if selection.has_key('description'):
      form.description.data = selection['description']
    if selection.has_key('url'):
      form.url.data = selection['url']
    return render_template('circuit_edit.html', form=form, mode='edit' )

  if 'POST' == request.method:
    if form.validate_on_submit():
      r.db('qv').table('circuit').get(idcircuit).update(form.data).run(g.rdb_conn)
      flash('circuit changes saved')
      return redirect( url_for( 'circuits' ) )
    else:
      flash( 'circuit error somewhere' )
      return render_template( 'circuit_edit.html', form=form, mode='edit' )

  return redirect( url_for( 'circuits' ) )

@app.route('/circuit/delete/<idcircuit>', methods=['GET'] )
def circuit_delete( idcircuit ):
  if      0 == r.db('qv').table('interface').filter({'idcircuit':idcircuit}).count().run(g.rdb_conn) \
      and 0 == r.db('qv').table('circuit').filter({'parent':idcircuit}).count().run(g.rdb_conn):
    r.db('qv').table('circuit').get(idcircuit).delete().run(g.rdb_conn)
    flash('circuit deleted')
  else:
    flash('circuit in use, not deleted')
  return redirect( url_for( 'circuits' ) )
