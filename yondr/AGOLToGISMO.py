# Import libraries
from arcgis.gis import GIS
from arcgis.mapping import WebMap
from IPython.display import display
from getpass import getpass
import tempfile



# source_password = getpass()
# target_password = getpass()
source = GIS("https://yondr.maps.arcgis.com/", 'colin.langhorn_Yondr', "yondrmap123")
# AGOL DEV
target = GIS('https://yondrdev.maps.arcgis.com/','YondrDev' , 'df1ZDR5vhG2a')
# GISMO
# target = GIS('https://yondrdev.maps.arcgis.com/', , target_password)


TEXT_BASED_ITEM_TYPES = frozenset(['Web Map', 'Feature Service', 'Map Service','Web Scene',
                                   'Image Service', 'Feature Collection', 
                                   'Feature Collection Template',
                                   'Web Mapping Application', 'Mobile Application', 
                                   'Symbol Set', 'Color Set',
                                   'Windows Viewer Configuration'])

FILE_BASED_ITEM_TYPES = frozenset(['File Geodatabase','CSV', 'Image', 'KML', 'Locator Package',
                                  'Map Document', 'Shapefile', 'Microsoft Word', 'PDF',
                                  'Microsoft Powerpoint', 'Microsoft Excel', 'Layer Package',
                                  'Mobile Map Package', 'Geoprocessing Package', 'Scene Package',
                                  'Tile Package', 'Vector Tile Package'])

ITEM_COPY_PROPERTIES = ['title', 'type', 'typeKeywords', 'description', 'tags',
                        'snippet', 'extent', 'spatialReference', 'name',
                        'accessInformation', 'licenseInfo', 'culture', 'url']


def copy_item(target, source_item):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            item_properties = {}
            for property_name in ITEM_COPY_PROPERTIES:
                item_properties[property_name] = source_item[property_name]

            data_file = None
            
            if source_item.type in TEXT_BASED_ITEM_TYPES:
                # If its a text-based item, then read the text and add it to the request.
                text = source_item.get_data(False)
                item_properties['text'] = text
            
            elif source_item.type in FILE_BASED_ITEM_TYPES:
                # download data and add to the request as a file
                data_file = source_item.download(temp_dir)

            thumbnail_file = source_item.download_thumbnail(temp_dir)
            metadata_file = source_item.download_metadata(temp_dir)

            #find item's owner
            source_item_owner = source.users.search(source_item.owner)[0]
            
            #find item's folder
            item_folder_titles = [f['title'] for f in source_item_owner.folders 
                                  if f['id'] == source_item.ownerFolder]
            folder_name = None
            if len(item_folder_titles) > 0:
                folder_name = item_folder_titles[0]

            #if folder does not exist for target user, create it
            if folder_name:
                # target_user = target.users.search(source_item.owner)[0]
                target_user = target.users.search("YondrDev")[0]
                target_user_folders = [f['title'] for f in target_user.folders
                                       if f['title'] == folder_name]
                if len(target_user_folders) == 0:
                    #create the folder
                    target.content.create_folder(folder_name, target_user)
            
            # Add the item to the target portal, assign owner and folder
            target_item = target.content.add(item_properties, data_file, thumbnail_file, 
                                             metadata_file, target_user, folder_name)
            #! Group not working
            #Set sharing (privacy) information
            # share_everyone = source_item.access == 'public'
            # share_org = source_item.access in ['org', 'public']
            # share_groups = []
            # if source_item.access == 'shared':
            #     share_groups = source_item.groups
            
            # target_item.share(share_everyone, share_org, share_groups)
            
            return target_item
        
    except Exception as copy_ex:
        print("\tError copying " + source_item.title)
        print("\t" + str(copy_ex))
        return None


# Get all Items in a group
group_items = []
groups = source.groups.search(query = 'title: "Gismo 1.0"')
for group in groups:
    for group_item in group.content():
        print(group_item)
        group_items.append(group_item)


# Copy over each item. While doing so, construct a dictionary mapping of source item's ID with target item's ID
source_target_itemId_map = {}
for item in group_items:
    print("Copying {} \tfor\t {}".format(item.title, item.owner))
    target_item = copy_item(target, item)
    if target_item:
        source_target_itemId_map[item.itemid] =  target_item.itemid
    else:
        source_target_itemId_map[item.itemid] =  None

print(source_target_itemId_map)

for key in source_target_itemId_map.keys():
    source_item = [x for x in group_items if x.id == key][0]



# RELATIONSHIP_TYPES = frozenset(['Map2Service', 'WMA2Code',
#                                 'Map2FeatureCollection', 'MobileApp2Code', 'Service2Data',
#                                 'Service2Service'])
# DOES NOT WORK YET
for id in source_target_itemId_map.values():
    item = target.content.search(id)[0]
    if item.type == "Web Map":
        wm_obj = WebMap(item)
        print(wm_obj.item.title)
        for layer in wm_obj.layers:
            try:
                if layer.layerType == 'GroupLayer':
                    for l in layer.layers:
                        target_layer = target.content.search(source_target_itemId_map[l["itemId"]], item_type='Feature Layer')[0]
                        l['url'] = target_layer.url
                        # The JSON itemId is different from and item "itemid"
                        l['itemId'] = target_layer.itemid
                else:
                    target_layer = target.content.search(source_target_itemId_map[layer["itemId"]], item_type='Feature Layer')[0]
                    layer['url'] = target_layer.url
                    # The JSON itemId is different from and item "itemid"
                    layer['itemId'] = target_layer.itemid
                target.update_properties(wm_obj)
            except Exception as e:
                print(f'Error with:{layer.title}')
                print(e.args[0])
        wm_obj.update()        




def is_hosted(item):
    return [keyword for keyword in item.typeKeywords if "Hosted" in keyword] 






# def print_webmap_inventory(wm):
#     wm_obj = WebMap(wm)
#     print(f"{wm_obj.item.title}\n{'-'*100}")
#     for wm_layer in wm_obj.layers:
#         try:
#             if is_hosted(Item(active_gis, wm_layer['itemId'])):
#                 print(f"{' '*2}{wm_layer['title']:40}HOSTED{' ':5}"
#                       f"{wm_layer['layerType']:20}{dict(wm_layer)['itemId']}")
#             else:
#                 print(f"{' '*2}{wm_layer['title']:40}other{' ':6}"
#                       f"{wm_layer['layerType']:20}{wm_layer.id}") 
#         except:
#             print(f"{' '*2}{wm_layer['title']:40}other{' ':6}"
#                   f"{wm_layer['layerType']:20}{wm_layer.id}")
#     print("\n")

# for key in source_target_itemId_map.keys():
#     source_item = [x for x in group_items if x.id == key][0]
#     target_itemid = source_target_itemId_map[key]
#     target_item = target.content.get(target_itemid)

#     print(source_item.title + " # " + source_item.type)
#     for relationship in RELATIONSHIP_TYPES:
#         try:
#             source_related_items = source_item.related_items(relationship)
#             for source_related_item in source_related_items:
#                 print("\t\t" + source_related_item.title + " # " + 
#                       source_related_item.type +"\t## " + relationship)

#                 #establish same relationship amongst target items
#                 print("\t\t" + "establishing relationship in target portal", end=" ")
#                 target_related_itemid = source_target_itemId_map[source_related_item.itemid]
#                 target_related_item = target.content.get(target_related_itemid)
#                 status = target_item.add_relationship(target_related_item, relationship)
#                 print(str(status))
#         except Exception as rel_ex:
#             print("\t\t Error when checking for " + relationship + " : " + str(rel_ex))
#             continue

