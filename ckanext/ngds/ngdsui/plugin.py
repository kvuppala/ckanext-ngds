from ckan.plugins import implements, SingletonPlugin, IRoutes, IConfigurer, toolkit, IAuthFunctions, IFacets, \
    ITemplateHelpers, IPackageController, IConfigurable, IActions

from ckan.lib.base import (model, g)

from ckanext.ngds.ngdsui.misc import helpers
from ckanext.ngds.ngdsui.lib.poly import get_package_ids_in_poly
from ckanext.ngds.ngdsui import authorize

import ckanext.datastore.logic.auth as datastore_auth
import ckanext.ngds.contentmodel.model.contentmodels as contentmodels
import ckanext.ngds.contentmodel.logic.action as contentmodel_action
import ckanext.ngds.logic.action.validate as validate_action

from pylons import config as ckan_config

import sys

try:
    from collections import OrderedDict # 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

class NgdsuiPlugin(SingletonPlugin):


    def customize_ckan_for_ngds(self):
        """
        Load ckan's authorization module and update the default role with NGDS specific roles.
        """

        def _trans_role_datasteward():
            return ('Data Steward')

        def _trans_role_datasubmitter():
            return ('Data Submitter')            

        module_obj = sys.modules['ckan.new_authz']

        #Create this new module methods for new roles. 'admin' and 'member' already exists in the default roles.
        setattr(module_obj, '_trans_role_datasteward', _trans_role_datasteward)        
        setattr(module_obj, '_trans_role_datasubmitter', _trans_role_datasubmitter)

        from ckan import new_authz     

        # Initialise NGDS roles.
        new_authz.ROLE_PERMISSIONS=OrderedDict([
                ('admin', ['admin']),
                ('datasteward', ['read', 'delete_dataset', 'create_dataset', 'update_dataset','publish_dataset']),
                ('datasubmitter', ['read', 'create_dataset','update_dataset']),
                ('member', ['read']),
        ])

    def create_default_group(self,data_dict=None):
        group = model.Group.get('public')

        print group

        if group:
            print "success "
        else:
            print "fail"

        # data_dict['name'] = 'default'
        # data_dict['type'] = 'organization'
        # context= {}
        # data_dict['users'] = [{'name': 'admin', 'capacity': 'admin'}]
        # get_action('group_create')(context, data_dict)

    def contentmodel_configure(self, config):
        if "usgin_url" in config: 
            contentmodels.usgin_url= config["usgin_url"]
        else:
            contentmodels.usgin_url= "http://schemas.usgin.org/contentmodels.json"
        # Access the URL and fill the cache
        print "Caching Content Models from USGIN: " + contentmodels.usgin_url
        contentmodel_action.contentmodel_refreshCache(None, None)

        True_List = ["true", "1", "t", "y", "yes", "yeah", "yup", "certainly"]

        if "checkfile_maxerror" in config:
            try:
                checkfile_maxerror= config["checkfile_maxerror"]
                contentmodels.checkfile_maxerror = int(checkfile_maxerror)
            except:
                print "DON'T UNDERSTAND the 'checkfile_maxerror' in the development.ini, it is not an Integer"
        print "checkfile_maxerror", contentmodels.checkfile_maxerror

        if "checkfile_checkheader" in config:
            try:
                checkfile_checkheader= config["checkfile_checkheader"]
                if checkfile_checkheader in True_List:
                    contentmodels.checkfile_checkheader = True
                else:
                    contentmodels.checkfile_checkheader = False
            except:
                print "DON'T UNDERSTAND the 'checkfile_checkheader' in the development.ini, it is not a boolean string"
        print "checkfile_checkheader", contentmodels.checkfile_checkheader

        if "checkfile_checkoptionalfalse" in config:
            try:
                checkfile_checkoptionalfalse= config["checkfile_checkoptionalfalse"]
                if checkfile_checkoptionalfalse in True_List:
                    contentmodels.checkfile_checkoptionalfalse = True
                else:
                    contentmodels.checkfile_checkoptionalfalse = False
            except:
                print "DON'T UNDERSTAND the 'checkfile_checkoptionalfalse' in the development.ini, it is not a boolean string"
        print "checkfile_checkoptionalfalse", contentmodels.checkfile_checkoptionalfalse

    implements(IConfigurable, inherit=True)

    def configure(self, config):
        self.contentmodel_configure(config)

    implements(IRoutes,inherit=True)

    def before_map(self,map):
        """
        For the moment, set up routes under the sub-root /ngds to render the UI.
        """
        home_controller = "ckanext.ngds.ngdsui.controllers.home:HomeController"
        map_controller = "ckanext.ngds.ngdsui.controllers.map:MapController"
        map.connect("home","/",controller=home_controller,action="render_index",conditions={"method":["GET"]})
        map.connect("ngds_home","/ngds",controller=home_controller,action="render_index",conditions={"method":["GET"]})
        map.connect("initiate_search","/ngds/initiate_search",controller=home_controller,action="initiate_search",conditions={"method":["POST"]})
        map.connect("about","/ngds/about",controller=home_controller,action="render_about",conditions={"method":["GET"]})

        #map.connect("dashboard","/dashboard",controller=home_controller,action="render_index",conditions={"method":["GET"]})
        #map.connect("dashboard_user","/dashboard/{offset}",controller=home_controller,action="render_index",conditions={"method":["GET"]})

        contribute_controller = "ckanext.ngds.ngdsui.controllers.contribute:ContributeController"
        map.connect("contribute","/ngds/contribute",controller=contribute_controller,action="index")
        map.connect("upload_file","/ngds/contribute/upload_file",controller=contribute_controller,action="upload_file")
        #map.connect("do_harvest","/ngds/do_harvest",controller=contribute_controller,action="do_harvest")
        #map.connect("harvest","/ngds/harvest",controller=contribute_controller,action="harvest")        
        # map.connect("upload","/ngds/contribute/upload",controller=contribute_controller,action="upload")
        map.connect("create_or_update_resource","/ngds/contribute/create_or_update_resource",controller=contribute_controller,action="create_or_update_resource",conditions={"method":["POST"]})
        map.redirect('/ngds/contribute/dataset/{action}', '/dataset/{action}')
        map.connect('get_structured_form','/ngds/contribute/get_structured_form',controller=contribute_controller,action="get_structured_form",conditions={"method":["GET"]})
        #map.connect("harvest_new","/ngds/harvest/edit",controller="ckanext.ngds.ngdsui.controllers.contribute:ContributeController",action="edit")
        map.connect("bulk_upload","/ngds/bulk_upload",controller=contribute_controller,action="bulk_upload")
        map.connect("bulk_upload_handle","/ngds/bulk_upload_handle",controller=contribute_controller,action="bulk_upload_handle")
        #map.connect("harvest_new","/ngds/harvest/{action}",controller=contribute_controller)
        map.connect("bulk_upload_list","/ngds/bulkupload_list",controller=contribute_controller,action="bulkupload_list")
        map.connect("bulk_upload_package","/ngds/bulkupload_package",controller=contribute_controller,action="bulkupload_package_list")
        map.connect("execute_bulkupload","/ngds/execute_bulkupload",controller=contribute_controller,action="execute_bulkupload")

        map.connect("rating_submit","/ngds/rating_submit",controller=home_controller,action="rating_submit",conditions={"method":["POST"]})
        map.connect("save_search","/ngds/save_search",controller=home_controller, action="save_search",conditions={"method":["POST"]})


        #Map related paths
        map.connect("map","/ngds/map",controller=home_controller,action="render_map",conditions={"method":["GET"]})
        map.connect("library","/ngds/library",controller=home_controller,action="render_library",conditions={"method":["GET"]})
        map.connect("resources","/ngds/resources",controller=home_controller,action="render_resources",conditions={"method":["GET"]})
        map.redirect("search","/ngds/library/search","/dataset", highlight_actions='index search')

        user_controller = "ckanext.ngds.ngdsui.controllers.user:UserController"

        map.connect("manage_users","/ngds/users",controller=user_controller,action="manage_users")
        map.connect("member_new","/ngds/member_new",controller=user_controller,action="member_new")
        map.connect("poly","/poly",controller=map_controller,action="test")
        map.connect("logout_page","/user/logged_out_redirect",controller=user_controller,action="logged_out_page")
        map.connect("validate_resource","/ngds/contribute/validate_resource",controller=contribute_controller,action="validate_resource")
        map.connect("additional_metadata","/ngds/contribute/additional_metadata",controller=contribute_controller,action="additional_metadata")
        map.connect("new_metadata","/ngds/contribute/new_metadata",controller=contribute_controller,action="new_metadata")

        map.connect("execute_fulltext_indexer","/ngds/execute_fulltext_indexer",controller=contribute_controller,action="execute_fulltext_indexer")



        return map

    implements(IConfigurer, inherit=True)

    def update_config(self, config):
        """
        Register the templates directory with ckan so that Jinja can find them.
        """
        toolkit.add_template_directory(config,'templates')
        #Static files are to be served up from here. Otherwise, pylons will try and decode content in here and will fail.
        toolkit.add_public_directory(config,'public')

        self.customize_ckan_for_ngds()

    implements(IActions, inherit=True)
    def get_actions(self):
        return {
        'contentmodel_refreshCache' : contentmodel_action.contentmodel_refreshCache, 
        'contentmodel_list' : contentmodel_action.contentmodel_list, 
        'contentmodel_list_short' : contentmodel_action.contentmodel_list_short, 
        'contentmodel_get': contentmodel_action.contentmodel_get, 
        'contentmodel_checkFile': contentmodel_action.contentmodel_checkFile,
        'contentmodel_checkBulkFile':contentmodel_action.contentmodel_checkBulkFile,
        #'create_resource_document_index': lib_action.create_resource_document_index
        'validate_resource': validate_action.validate_resource,
        'validate_dataset_metadata':validate_action.validate_dataset_metadata
        }

    implements(IAuthFunctions, inherit=True)

    def get_auth_functions(self):

        return {
            'manage_users': authorize.manage_users,
            'publish_dataset': authorize.publish_dataset,
            'manage_nodes': authorize.manage_nodes,
            'execute_bulkupload':authorize.execute_bulkupload,
            'contentmodel_refreshCache' : datastore_auth.datastore_create, 
            'contentmodel_list' : datastore_auth.datastore_create, 
            'contentmodel_checkFile' : datastore_auth.datastore_create,
        }    

    implements(ITemplateHelpers, inherit=True)

    def get_helpers(self):
        return {
            'get_responsible_party_name':helpers.get_responsible_party_name,
            'get_default_group':helpers.get_default_group,
            'get_login_url':helpers.get_login_url,
            'get_language':helpers.get_language,
            'get_url_for_file':helpers.get_url_for_file,
            'is_plugin_enabled':helpers.is_plugin_enabled,
            'username_for_id':helpers.username_for_id,
            'get_formatted_date':helpers.get_formatted_date,
            'load_ngds_facets':helpers.load_ngds_facets,
            'get_ngdsfacets':helpers.get_ngdsfacets,
            'get_formatted_date':helpers.get_formatted_date,
            'get_formatted_date_from_obj':helpers.get_formatted_date_from_obj,
            'get_field_title':helpers.get_field_title,
            'is_string_field':helpers.is_string_field,
            'is_ogc_publishable':helpers.is_ogc_publishable,
            'jsonify':helpers.jsonify,
            'highlight_rating_star':helpers.highlight_rating_star,
            'count_rating_reviews':helpers.count_rating_reviews,
            'rating_text':helpers.rating_text,
            'get_usersearches':helpers.get_usersearches,
            'get_dataset_category_image_path':helpers.get_dataset_category_image_path,
            'is_following':helpers.is_following,
            'parseJSON':helpers.parseJSON,
            'json_extract':helpers.json_extract,
            'get_master_style':helpers.get_master_style,
            'toJSON':helpers.to_json,
            'split':helpers.split,
            'get_label_for_pkg_attribute':helpers.get_label_for_pkg_attribute,
            'is_json':helpers.is_json,
            'get_label_for_resource_attribute':helpers.get_label_for_resource_attribute,
            'is_development':helpers.is_development,
            'get_rating_details':helpers.get_rating_details
        }

    implements(IPackageController, inherit=True)

    def before_index(self, pkg_dict):
        #pkg_dict['sample_created']={'prahadeesh':'abclll'}
        is_full_text_enabled = ckan_config.get('ngds.full_text_indexing','false')

        file_formats_to_ignore = ('csv')


        import json
        if pkg_dict.get('data_dict'):
            dict = json.loads(pkg_dict.get('data_dict'))
            resources = dict.get('resources')

        #print "resources: ", resources

        if resources:
            document_index_list = []
            for resource in resources:

                res_file_field = 'resource_file_%s' % resource.get("id")
                #print "res_file_field:", res_file_field
                pkg_dict[res_file_field] = ''

                try:
                    for (okey, nkey) in [('distributor', 'res_distributor'),
                                         ('protocol', 'res_protocol'),
                                         ('layer', 'res_layer'),
                                         ('content_model', 'res_content_model')]:
                        pkg_dict[nkey] = pkg_dict.get(nkey, []) + [resource.get(okey, u'')]

                    if is_full_text_enabled == 'true' and resource.get('resource_format', '') == 'unstructured' and \
                            str(resource.get('format', u'')).lower() not in file_formats_to_ignore:

                        file_path = helpers.file_path_from_url(resource.get("url"))
                        if file_path:
                            resource_index_dict = {'package_id': pkg_dict.get('id'),
                                           'resource_id': resource.get("id"),
                                           'file_path': file_path,
                                           }
                            document_index_list.append(resource_index_dict)
                except Exception, ex:
                    print "exception: ", ex

            if is_full_text_enabled == 'true' and document_index_list:
                helpers.create_package_resource_document_index(pkg_dict.get('id'),  document_index_list)

        return pkg_dict


    def before_search(self, search_params):
        # if 'fq' not in search_params:
        #         search_params['fq'] = ''
        # search_params['fq'] = search_params['fq']+' capacity:"public"'
        if 'extras' in search_params and 'poly' in search_params['extras'] and search_params['extras']['poly']:
            # do some validation
            # We'll perform the existing search but also filtering by the ids
            # of datasets within the bbox
            x =  { 'poly':search_params['extras']['poly'] }
            bbox_query_ids = get_package_ids_in_poly(x,'4326')
            q = search_params.get('q','')
            new_q = '%s AND ' % q if q else ''
            new_q += '(%s)' % ' OR '.join(['id:%s' % id for id in bbox_query_ids])
            search_params['q'] = new_q
        else:
            print "Definitely not in"

        return search_params

    def after_search(self, search_results, search_params):
        try:
            if g.facet_json_data:
                print "global value is there..."
        except AttributeError:
            print "Facet json config is not available. Returning the default facets."
            helpers.load_ngds_facets()
        #print "search_results: ",search_results
        return search_results

    implements(IFacets, inherit=True)

    def dataset_facets(self, facets_dict, package_type):
        #print "IFACETS is called.......>>>>>>>>>>>>>>>>"

        if package_type == 'harvest':
            return OrderedDict([('frequency', 'Frequency'), ('source_type', 'Type')])

        ngds_facets = helpers.load_ngds_facets()
        
        if ngds_facets:
            facets_dict = ngds_facets
        
        return facets_dict        

    def organization_facets(self, facets_dict, organization_type, package_type):
        #print "IFACETS is called.......>>>>>>>>>>>>>>>>"

        if package_type == 'harvest':
            return OrderedDict([('frequency', 'Frequency'), ('source_type', 'Type')])

        ngds_facets = helpers.load_ngds_facets()
        
        if ngds_facets:
            facets_dict = ngds_facets
        
        return facets_dict    
