from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, IntegerField, HiddenField, SelectField
from wtforms.validators import Optional, Required, Length, IPAddress

class OrganizationEdit( Form ):
  name = TextField('name', validators = [Required()])
  description = TextField('description', validators = [Length( min=0, max=100)])
  asn = IntegerField( 'asn', validators = [Optional()] )
  url = TextField('url', validators = [Optional()] )

class OrganizationAdd( OrganizationEdit ):
  idorganization = TextField( 'idorganization', validators = [ Required(), Length( min=4, max=4 )])

class IpAddressAdd( Form ):
  ipaddress = TextField( 'ipaddress', validators = [Required() ])
  parent = SelectField( 'parent' ) # show the enclosing ip address rather than the key
  idorganization = SelectField( 'idorganization', validators = [Required()] )
  name = TextField( 'name' ) # optional name
  description = TextField( 'description' ) # optional description
  url = TextField( 'url' ) # optional url for management or for info

class IpAddressEdit( IpAddressAdd ):
  idipaddress = HiddenField( 'idipaddress', validators = [Required()])

class IanaIfType( Form ):
  idianaiftype = HiddenField( 'idianaiftype', validators = [ Required() ] )
  name = TextField( 'name', validators = [Required()] )
  description = TextField( 'description' )

class InterfaceAdd( Form ):
  parent = SelectField( 'parent' )
  idhost = SelectField( 'idhost', validators = [Required()] )
  idipaddress = SelectField( 'idipaddress' )
  idcircuit = SelectField( 'idcircuit' )
  name = TextField( 'name' )
  mac = TextField( 'mac' )
  description = TextField( 'description' )
  fqdn = TextField( 'fqdn' )
  url = TextField( 'url' )
  idvlan = HiddenField( 'idvlan' )
  idvrf = HiddenField( 'idvrf' )

class InterfaceEdit( InterfaceAdd ):
  idinterface = HiddenField( 'idinterface', validators = [Required()] )

class CircuitAdd( Form ):
  parent = SelectField( 'parent' )
  name = TextField( 'name', validators = [Required()] )
  idipaddress = SelectField( 'idipaddress' )
  description = TextField( 'description' )
  url = TextField( 'url' )

class CircuitEdit( CircuitAdd ):
  idcircuit = HiddenField( 'idcircuit', validators = [Required()] )

class HostTypeAdd( Form ):
  name = TextField( 'name', validators = [Required()] )
  description = TextField( 'description' )

class HostTypeEdit( HostTypeAdd ):
  idhosttype = HiddenField( 'idhosttype', validators = [Required() ] )

class HostAdd( Form ):
  parent = SelectField( 'parent' )
  name = TextField( 'name', validators = [Required()] )
  idhosttype = SelectField( 'idhosttype', validators = [ Required() ] )
  description = TextField( 'description' ) 
  url1 = TextField( 'url1' ) 
  url2 = TextField( 'url2' )

class HostEdit( HostAdd ):
  idhost = HiddenField( 'idhost', validators = [Required()] )

class Vlan( Form ):
  idvlan = HiddenField( 'idvlan', validators = [Required()] )
  vlan = TextField( 'vlan', validators = [ Required() ] )
  name = TextField( 'name', validators = [ Required() ] )
  description = TextField( 'description' )

class Vrf( Form ):
  idvrf = HiddenField( 'idvrf', validators = [Required()] )
  vrf = TextField( 'vrf', validators = [ Required() ] )
  description = TextField( 'description' )

