from geoserver.support import url
#from ckan.lib.base import (model,c) 
from ckan.plugins import toolkit
from ckanext.ngds.env import ckan_model

class Layer(object): 

    def __init__(self, geoserver=None, name=None, resource_id=None):
        self.geoserver = geoserver
        self.name = name
        self.resource_id = resource_id

    def create(self): 
        """
        Creates the new layer to Geoserver and then creates the resources in Package(CKAN).

        """
        if self.create_layer() == None:
            return False
        if self.create_geo_resources() == None:
            return False
        return True

    def remove(self,resources_to_remove=None): 
        """
        Removes the Layer from Geoserver and the geo resources from the pacakage.
        """

        self.remove_layer()
        self.remove_resource(resources_to_remove)

    def create_layer(self): 
        """
        Constructs the layer details and creates it in the geoserver.
        If the layer already exists then, raises exception.

        @returns geoserver layer
        """
        #If the layer already exists in Geoserver then raise exception.
        if self.geoserver.get_layer(self.name) : 
            # raise Exception("Layer %s already exists in Geoserver.") % self.name
            return None

        #Construct layer creation request.
        self._construct_layer_request("POST")

        #Return the created layer.
        return self.geoserver.get_layer(self.name)

    def remove_layer(self): 
        """
        Removes the layer from geoserver.

        """

        self._construct_layer_request("DELETE")


    def _construct_layer_request(self,action): 
        """
        Constructs the featuretypes xml and invokes geoserver based on the action and returns.

        """
        #Get the datastore from geoserver
        store = self.geoserver.default_datastore()

        self.store = store

        featureType_url = url(self.geoserver.service_url,["workspaces", store.workspace.name, "datastores", store.name, "featuretypes"])

        data =  ("<featureType><name>{name}</name></featureType>").format(name=self.name)

        headers = {"Content-type":  "text/xml"}

        print "featureType_url:  ",featureType_url

        headers, response = self.geoserver.http.request(featureType_url, action, data, headers)

        print "sent geoserver layer POST"

        if action=="POST": 
            msg = "Tried to create Geoserver layer but encountered"
        else: 
            msg = "Tried to delete Geoserver layer but encountered"

        assert 200 <= headers.status < 300, msg + str(headers.status) + " error:  " + response

        self.geoserver._cache.clear()

    def create_geo_resources(self): 
        """
        Creates the geo resources(WMS,WFS) into CKAN. Created layer can provice WMS,WFS capabilities.
        Gets the file resource details and creates two new resources for the package.

        """

        #context = {'model':  model, 'session':  model.Session,'user':  c.user or c.author}
        context = {}

        file_resource = toolkit.get_action('resource_show')(context, {'id': self.resource_id})

        #File Resource Update
        data_dict = {
        'id': file_resource['id'],
        'layer_name': self.name
        }

        # toolkit.get_action('resource_update')(context, data_dict)
        package_id = ckan_model.Resource.get(file_resource['id']).resource_group.package_id

        action = toolkit.get_action('resource_create')

        #WMS Resource Creation
        data_dict = {
        'url': (self.geoserver.service_url.replace("/rest", "/wms")+'?layers=%s:%s') % (self.store.workspace.name, self.name),
        'package_id': package_id,
        'description': 'WMS for '+file_resource['name'] ,
        'parent_resource': file_resource['id']
        }
        print "Creating WMS Resource"
        print action(context, data_dict)
        print "Created WMS Resource"

        data_dict = {
        'url': (self.geoserver.service_url.replace("/rest", "/wfs")+'?layers=%s:%s') % (self.store.workspace.name, self.name),
        'package_id': package_id,
        'name': 'WFS for '+file_resource['name'] ,
        'description': 'WFS for '+file_resource['name'] ,
        'parent_resource': file_resource['id']
        }

        print "Creating WFS Resource"
        print action(context, data_dict)
        print "Created WFS Resource"

        return True

    def remove_resource(self,resources_to_remove): 
        """
        Removes the list of resources from package.If the resoures list not provided then find the geo resources based on
        parent_resource value and then removes them from package.
        """

        #Find the resources to be removed.
        #context = {'model':  model, 'session':  model.Session,'user':  c.user or c.author}
        context ={}
        if not resources_to_remove: 
            file_resource = toolkit.get_action('resource_show')(context, {'id': self.resource_id})

            pkg = toolkit.get_action('package_show')(context, {'id':  file_resource.resource_group.package.id})
            resources_to_remove = [resource["id"] for resource in pkg["resources"] if resource.get("parent_resource") == self.resource_id]

        #File Resource Update
        data_dict = {
        'id': self.resource_id,
        'layer_name': None
        }

        toolkit.get_action('resource_update')(context, data_dict)

        for resourceid in resources_to_remove: 
            toolkit.get_action('resource_delete')(context, {'id': resourceid})