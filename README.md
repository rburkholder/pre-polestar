pre-polestar
============

This is a quick prototype to test python, flask, and rethinkdb

The rethinkdb schema is described in designer.xml, and can be cut/paste into http://ondras.zarovi.cz/sql/demo/

Schema construction is embedded in the view.py code.

Given that I come from a SQL background, it was hard to break out of that mold, 
and start to think in NoSQL terms.  In the end I was unsuccessful.  I want to 
enforce too many inter-tuple business rules on the data sets.  

But for what it does, rethinkdb certainly gets the job done.

People can use this code as basis for understanding some rethinkdb operations.  This python code 
is my first foray, so there are some redundancies and inefficiencies, but the general gist 
is there.

This project is labelled as pre-polestar.  I am taking the concepts learned here, and creating a 
new polestar project, still in python, but utilizing postgresql as the backend.  The efforts 
will be posted when something useful emerges.

Side related topics can be seen at http://blog.raymond.burkholder.net

And of course, you ask, what does it do.  It represents the beginning thoughts on how to manage the 
layer 1, layer 2 and layer 3 infrastructure of a service provider's network infrastructure.  The 
information contained here-in would be used for populating DNS tables, insfrastructure maps, 
monitoring thingys, ....
